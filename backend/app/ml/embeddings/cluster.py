"""
ml/embeddings/cluster.py
-------------------------
KMeans clustering on review embeddings for automatic theme discovery.

Pipeline:
  1. Encode reviews → 384-dim embeddings (encoder.py)
  2. KMeans with k=8 clusters (elbow-validated on our 28k dataset)
  3. Auto-label each cluster using top TF-IDF terms from reviews in that cluster
  4. Return cluster assignments + human-readable labels

Design note:
  - K=8 chosen empirically — 65 products * ~4 topics each ≈ 8-12 meaningful clusters.
  - We use KMeans (not HDBSCAN) for v1: it's deterministic, fast, and predictable.
    HDBSCAN is better for high-noise data; revisit if clusters look bad in production.
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

DEFAULT_N_CLUSTERS = 8
RANDOM_STATE = 42


class ReviewClusterer:
    """
    Clusters reviews by semantic similarity and auto-labels each cluster.

    Usage:
        clusterer = ReviewClusterer(n_clusters=8)
        results = clusterer.fit(embeddings, texts)
        # results["cluster_ids"] — array of int cluster assignments
        # results["cluster_labels"] — dict {cluster_id: "battery performance"}
        # results["cluster_sizes"] — dict {cluster_id: count}
    """

    def __init__(self, n_clusters: int = DEFAULT_N_CLUSTERS):
        self.n_clusters = n_clusters
        self._kmeans: KMeans | None = None
        self._cluster_labels: dict[int, str] = {}

    def fit(self, embeddings: np.ndarray, texts: list[str]) -> dict:
        """
        Fit KMeans on embeddings and auto-label clusters via TF-IDF.

        Args:
            embeddings: numpy array (N, 384) from ReviewEncoder.
            texts: Raw review texts corresponding to each embedding.

        Returns:
            {
                "cluster_ids": np.ndarray of int (N,),
                "cluster_labels": {cluster_id: "label string"},
                "cluster_sizes": {cluster_id: int},
            }
        """
        if len(embeddings) == 0:
            return {"cluster_ids": np.array([]), "cluster_labels": {}, "cluster_sizes": {}}

        n_clusters = min(self.n_clusters, len(embeddings))

        self._kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=RANDOM_STATE,
            n_init=10,
            max_iter=300,
        )
        cluster_ids = self._kmeans.fit_predict(embeddings)

        # Auto-label each cluster with top TF-IDF terms
        self._cluster_labels = self._auto_label(texts, cluster_ids, n_clusters)

        # Cluster size counts
        unique, counts = np.unique(cluster_ids, return_counts=True)
        cluster_sizes = {int(k): int(v) for k, v in zip(unique, counts)}

        return {
            "cluster_ids": cluster_ids,
            "cluster_labels": self._cluster_labels,
            "cluster_sizes": cluster_sizes,
        }

    def predict(self, embeddings: np.ndarray) -> np.ndarray:
        """Assign new embeddings to existing clusters (after fit)."""
        if self._kmeans is None:
            raise RuntimeError("Call fit() before predict()")
        return self._kmeans.predict(embeddings)

    def _auto_label(
        self, texts: list[str], cluster_ids: np.ndarray, n_clusters: int
    ) -> dict[int, str]:
        """
        For each cluster, extract the top 3 TF-IDF terms from the reviews in it.
        These terms become the human-readable cluster label.

        E.g.: cluster 2 → "battery life charge" → label: "Battery Life"
        """
        labels: dict[int, str] = {}

        # Fit TF-IDF on all texts (bigrams + unigrams, ignore stopwords)
        tfidf = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english",
            min_df=2,
        )
        try:
            tfidf_matrix = tfidf.fit_transform(texts)
            feature_names = tfidf.get_feature_names_out()
        except ValueError:
            # Too few texts to fit TF-IDF
            return {i: f"Cluster {i}" for i in range(n_clusters)}

        for cluster_id in range(n_clusters):
            mask = cluster_ids == cluster_id
            if not mask.any():
                labels[cluster_id] = f"Cluster {cluster_id}"
                continue

            # Mean TF-IDF vector for reviews in this cluster
            cluster_tfidf = tfidf_matrix[mask].mean(axis=0)
            cluster_tfidf = np.asarray(cluster_tfidf).flatten()

            # Top 3 terms by TF-IDF weight
            top_indices = cluster_tfidf.argsort()[-3:][::-1]
            top_terms = [feature_names[i] for i in top_indices if cluster_tfidf[i] > 0]

            if top_terms:
                # Capitalize and join: "battery life" → "Battery Life & product"
                label = " · ".join(t.title() for t in top_terms[:2])
            else:
                label = f"Cluster {cluster_id}"

            labels[cluster_id] = label

        return labels
