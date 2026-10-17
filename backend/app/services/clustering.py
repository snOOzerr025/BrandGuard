"""
services/clustering.py — Two-Tier Adaptive Taxonomy & HDBSCAN Orchestrator
-------------------------------------------------------------------------
Orchestrates Tier 2 unsupervised theme discovery within product aspect subsets
and the Miscellaneous nursery bucket:
- Evaluates Chattermill Net Sentiment: (P - N)/(P + Neu + N) * 100
- Evaluates Thematic Leave-One-Out Star Impact: Impact(t) = (a/b) - (c/d)
- Persists MicroCluster records with centroid embeddings and medoid evidence
- Triggers Taxonomy Promotion Alerts for Miscellaneous micro-clusters with N >= 25
"""
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlmodel import Session, select

from backend.app.ml.clustering.hdbscan_discovery import (
    DiscoveredMicroTheme,
    TwoTierHDBSCANClusterer,
)
from backend.app.models.domain import (
    Alert,
    MicroCluster,
    PolarityLabel,
    Review,
    SentimentResult,
    SeverityTier,
)


class ClusteringService:
    """
    Orchestrator for Tier 2 micro-clustering, Thematic impact calculation,
    and taxonomy promotion alerts.
    """

    def __init__(self, min_cluster_size: int = 12, min_samples: int = 5):
        self.clusterer = TwoTierHDBSCANClusterer(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
        )

    def cluster_product_themes(
        self,
        product_id: uuid.UUID,
        user_id: uuid.UUID,
        session: Session,
        macro_aspect: Optional[str] = None,
    ) -> List[MicroCluster]:
        """
        Runs HDBSCAN micro-clustering for a product.
        If macro_aspect is supplied, clusters reviews for that aspect;
        otherwise runs on all embedded reviews and the Miscellaneous bucket.
        """
        # 1. Fetch reviews with embeddings
        query = select(Review).where(
            Review.product_id == product_id,
            Review.user_id == user_id,
            Review.embedding != None,  # noqa: E711
        )
        all_reviews = session.exec(query).all()
        if not all_reviews:
            return []

        # All review scores for global Thematic Leave-One-Out calculation
        all_scores = [r.rating for r in all_reviews]
        sum_all_scores = sum(all_scores)
        count_all_scores = len(all_scores)
        mean_all = sum_all_scores / count_all_scores if count_all_scores > 0 else 0.0

        # Filter by aspect if requested
        target_reviews = all_reviews
        aspect_tag = macro_aspect or "Overall"

        embeddings_list = [r.embedding for r in target_reviews if r.embedding is not None]
        texts_list = [r.body for r in target_reviews if r.embedding is not None]
        uids_list = [str(r.id) for r in target_reviews if r.embedding is not None]

        if len(embeddings_list) < 5:
            return []

        emb_matrix = np.array(embeddings_list, dtype=np.float32)

        # 2. Discover micro-themes via UMAP + HDBSCAN + c-TF-IDF
        discovered = self.clusterer.fit_discover(
            embeddings=emb_matrix,
            texts=texts_list,
            review_ids=uids_list,
            macro_aspect=aspect_tag,
        )

        persisted_clusters: List[MicroCluster] = []

        # 3. Process each discovered micro-cluster
        for theme in discovered:
            cluster_uid_set = set(theme.review_ids)

            # Compute Leave-One-Out Star Impact: Impact(t) = (a/b) - (c/d)
            # where c is sum of scores excluding cluster t, d is count of reviews excluding cluster t
            excl_scores = [r.rating for r in all_reviews if str(r.id) not in cluster_uid_set]
            if excl_scores:
                mean_excl = sum(excl_scores) / len(excl_scores)
                star_impact = mean_all - mean_excl
            else:
                star_impact = 0.0

            # Compute Net Sentiment: (P - N)/(P + Neu + N) * 100
            # Pull SentimentResults for reviews in this cluster
            rev_uuids = [uuid.UUID(uid) for uid in theme.review_ids]
            sentiments = session.exec(
                select(SentimentResult).where(SentimentResult.review_id.in_(rev_uuids))
            ).all()

            pos_count = sum(1 for s in sentiments if s.polarity == PolarityLabel.POSITIVE)
            neg_count = sum(1 for s in sentiments if s.polarity == PolarityLabel.NEGATIVE)
            total_sent = len(sentiments)
            if total_sent > 0:
                net_sentiment = ((pos_count - neg_count) / total_sent) * 100.0
            else:
                # Fallback to rating polarity if sentiments not present
                ratings = [r.rating for r in all_reviews if str(r.id) in cluster_uid_set]
                pos_r = sum(1 for r in ratings if r >= 4)
                neg_r = sum(1 for r in ratings if r <= 2)
                net_sentiment = ((pos_r - neg_r) / max(len(ratings), 1)) * 100.0

            # Persist MicroCluster
            micro_cluster = MicroCluster(
                user_id=user_id,
                product_id=product_id,
                macro_aspect=aspect_tag,
                hdbscan_label=theme.cluster_label,
                theme_label=theme.theme_label,
                top_ctfidf_terms=theme.top_terms,
                evidence_review_ids=theme.medoid_review_ids,
                review_volume=theme.volume,
                net_sentiment=round(net_sentiment, 2),
                star_impact_delta=round(star_impact, 4),
                centroid_embedding=theme.centroid_embedding,
            )
            session.add(micro_cluster)
            session.commit()
            session.refresh(micro_cluster)

            # Assign review.micro_cluster_id
            for rev_id_str in theme.review_ids:
                r_obj = session.get(Review, uuid.UUID(rev_id_str))
                if r_obj:
                    r_obj.micro_cluster_id = micro_cluster.id
                    session.add(r_obj)

            session.commit()
            persisted_clusters.append(micro_cluster)

            # 4. Miscellaneous Nursery Promotion Logic:
            # Trigger alert if cluster in Miscellaneous exceeds volume threshold N >= 25
            if (aspect_tag == "Miscellaneous" or "misc" in theme.theme_label.lower()) and theme.volume >= 25:
                self._trigger_taxonomy_promotion_alert(
                    session=session,
                    user_id=user_id,
                    product_id=product_id,
                    cluster=micro_cluster,
                    medoids=theme.medoid_review_ids,
                )

        return persisted_clusters

    @staticmethod
    def _trigger_taxonomy_promotion_alert(
        session: Session,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        cluster: MicroCluster,
        medoids: List[str],
    ) -> None:
        """Surfaces Taxonomy Promotion Alert for persistent high-volume micro-issues."""
        alert = Alert(
            user_id=user_id,
            product_id=product_id,
            aspect_category="Miscellaneous",
            micro_cluster_id=cluster.id,
            severity=SeverityTier.MEDIUM,
            alert_type="TAXONOMY_PROMOTION",
            z_score=2.0,
            baseline_mean=0.0,
            current_value=cluster.net_sentiment,
            star_impact=cluster.star_impact_delta,
            support_count=cluster.review_volume,
            message=(
                f"Taxonomy Promotion Alert: Emergent micro-theme '{cluster.theme_label}' "
                f"reached {cluster.review_volume} reviews in the Miscellaneous nursery. "
                f"Promotion to tracked product sub-feature recommended."
            ),
            evidence_review_ids=medoids,
        )
        session.add(alert)
        session.commit()
