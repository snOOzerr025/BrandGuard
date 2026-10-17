"""
rag/citation_verifier.py — Post-Generation Verification & NLI Guardrail
-----------------------------------------------------------------------
Enforces zero hallucinations before returning responses to the user:
1. UUID Existence Gate: Verifies every cited UUID exists in the retrieved top-10 set.
   Any fabricated or hallucinated UUID is stripped immediately.
2. NLI Entailment Gate: Cross-Encoder evaluates semantic entailment of claim.statement
   against concatenated cited review text. Suppresses claims with confidence < 0.70.
"""
import uuid
from typing import Dict, List, Optional, Set, Tuple

from backend.app.models.domain import Review
from backend.app.rag.reranker import CrossEncoderReranker
from backend.app.rag.schemas import CitedClaim, CopilotStructuredResponse


class CitationVerifier:
    """
    Guardrail verifying LLM generated citations and statements against source evidence.
    """

    def __init__(self, reranker: Optional[CrossEncoderReranker] = None, min_entailment: float = 0.70):
        self.reranker = reranker or CrossEncoderReranker()
        self.min_entailment = min_entailment

    def verify_response(
        self,
        raw_response: CopilotStructuredResponse,
        retrieved_reviews: List[Review],
    ) -> CopilotStructuredResponse:
        """
        Filters hallucinated UUIDs and verifies claim entailment.
        """
        valid_uuid_map: Dict[str, Review] = {
            str(r.id): r for r in retrieved_reviews
        }
        valid_short_map: Dict[str, Review] = {
            str(r.id)[:8]: r for r in retrieved_reviews
        }

        verified_claims: List[CitedClaim] = []

        for claim in raw_response.claims:
            # 1. UUID Existence Gate
            valid_cited_ids: List[str] = []
            for cid in claim.cited_review_ids:
                cid_str = str(cid).strip()
                if cid_str in valid_uuid_map:
                    valid_cited_ids.append(cid_str)
                elif cid_str[:8] in valid_short_map:
                    valid_cited_ids.append(str(valid_short_map[cid_str[:8]].id))

            if not valid_cited_ids:
                # Claim had zero valid source citations from retrieved reviews — suppress or uncite
                continue

            # 2. NLI Entailment Gate
            # Concatenate cited review texts
            cited_text = " ".join([valid_uuid_map[uid].body for uid in valid_cited_ids])
            entailment_score = self.reranker.score_nli_entailment(
                statement=claim.statement,
                context=cited_text,
            )

            if entailment_score >= self.min_entailment:
                verified_claims.append(
                    CitedClaim(
                        statement=claim.statement,
                        cited_review_ids=valid_cited_ids,
                        confidence=entailment_score,
                    )
                )

        has_warning = len(verified_claims) == 0 and len(raw_response.claims) > 0

        return CopilotStructuredResponse(
            executive_summary=raw_response.executive_summary,
            quantitative_metrics_used=raw_response.quantitative_metrics_used,
            claims=verified_claims,
            insufficient_evidence_warning=has_warning or raw_response.insufficient_evidence_warning,
            latency_ms=raw_response.latency_ms,
        )
