"""
ml/clustering/ctfidf.py — Class-Based TF-IDF (c-TF-IDF) & MMR Keyword Extractor
-----------------------------------------------------------------------------
Implements BERTopic class-based TF-IDF:
  W_{t,c} = tf_{t,c} * log(1 + A / tf_t)
where:
  - tf_{t,c} is the frequency of n-gram t in cluster c
  - tf_t is the frequency of n-gram t across all clusters
  - A is the average number of words per cluster
Maximal Marginal Relevance (MMR, diversity=0.3) filters redundant synonyms.
"""
import math
import re
from collections import Counter
from typing import Dict, List, Tuple

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
}


def tokenize_document(doc: str, n_gram_range: Tuple[int, int] = (1, 2)) -> List[str]:
    """Tokenizes document into lowercased unigrams and bigrams, filtering stop words."""
    words = re.findall(r"\b[a-zA-Z]{3,}\b", doc.lower())
    filtered_words = [w for w in words if w not in STOP_WORDS]
    tokens = list(filtered_words)

    if n_gram_range[1] >= 2 and len(filtered_words) >= 2:
        for i in range(len(filtered_words) - 1):
            bigram = f"{filtered_words[i]} {filtered_words[i+1]}"
            tokens.append(bigram)

    return tokens


class ClassBasedTFIDF:
    """
    Computes class-based TF-IDF (c-TF-IDF) across clustered pseudo-documents.
    """

    def __init__(self, top_n: int = 10, diversity: float = 0.3):
        self.top_n = top_n
        self.diversity = diversity

    def compute_ctfidf(self, cluster_docs: Dict[int, List[str]]) -> Dict[int, List[str]]:
        """
        Calculates c-TF-IDF for each cluster:
          cluster_docs: Dict mapping cluster_label (int) -> List[document_text]
        Returns:
          Dict mapping cluster_label -> List[top_terms]
        """
        # Exclude outlier cluster -1 from vocabulary baseline
        valid_clusters = {k: v for k, v in cluster_docs.items() if k != -1 and len(v) > 0}
        if not valid_clusters:
            return {}

        # 1. Concatenate docs in each cluster into a single pseudo-document
        cluster_tokens: Dict[int, List[str]] = {}
        global_term_counts: Counter = Counter()
        total_cluster_words = 0

        for c_id, docs in valid_clusters.items():
            tokens = []
            for doc in docs:
                tokens.extend(tokenize_document(doc))
            cluster_tokens[c_id] = tokens
            total_cluster_words += len(tokens)
            global_term_counts.update(tokens)

        # Average words per cluster (A)
        avg_words_per_cluster = max(total_cluster_words / max(len(valid_clusters), 1), 1.0)

        # 2. Compute W_{t,c} = tf_{t,c} * log(1 + A / tf_t)
        cluster_top_terms: Dict[int, List[str]] = {}

        for c_id, tokens in cluster_tokens.items():
            if not tokens:
                cluster_top_terms[c_id] = []
                continue

            tf_c = Counter(tokens)
            scores: Dict[str, float] = {}

            for term, count in tf_c.items():
                tf_global = global_term_counts[term]
                # c-TF-IDF formula
                score = count * math.log(1.0 + (avg_words_per_cluster / tf_global))
                scores[term] = score

            # Maximal Marginal Relevance (MMR) diversification
            ranked_terms = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
            diverse_terms = self._apply_mmr(ranked_terms, self.top_n, self.diversity)
            cluster_top_terms[c_id] = diverse_terms

        return cluster_top_terms

    @staticmethod
    def _apply_mmr(candidates: List[str], top_n: int, diversity: float) -> List[str]:
        """
        Selects top-N distinct terms, dampening candidates that share high token overlap.
        """
        selected: List[str] = []
        for cand in candidates:
            if len(selected) >= top_n:
                break
            cand_tokens = set(cand.split())
            # Check overlap with already selected terms
            redundant = False
            for sel in selected:
                sel_tokens = set(sel.split())
                overlap = len(cand_tokens.intersection(sel_tokens)) / max(len(cand_tokens), 1)
                if overlap > (1.0 - diversity):
                    redundant = True
                    break
            if not redundant:
                selected.append(cand)
            elif len(selected) < top_n and len(candidates) < top_n * 2:
                selected.append(cand)

        return selected[:top_n]
