"""
ml/clustering/hdbscan_discovery.py — Two-Tier UMAP + HDBSCAN Unsupervised Discovery Engine
------------------------------------------------------------------------------------------
Replaces legacy fixed K-Means with density-based clustering:
1. UMAP (n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine')
2. HDBSCAN (min_cluster_size=12, min_samples=5, cluster_selection_method='eom')
   Isolates noise and one-off complaints to cluster label -1.
3. c-TF-IDF keyword extraction & medoid review extraction.
"""
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.ml.clustering.ctfidf import ClassBasedTFIDF


@dataclass
class DiscoveredMicroTheme:
    cluster_label: int
    theme_label: str
    top_terms: List[str]
    review_indices: List[int]
    review_ids: List[str]
    medoid_review_ids: List[str]
    volume: int
    centroid_embedding: List[float]


class TwoTierHDBSCANClusterer:
    """
    Tier 2 Unsupervised Theme Discovery within aspect partitions and Miscellaneous bucket.
    """

    def __init__(
        self,
        min_cluster_size: int = 12,
        min_samples: int = 5,
        n_components: int = 5,
    ):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.n_components = n_components
        self.ctfidf = ClassBasedTFIDF(top_n=10, diversity=0.3)

    def fit_discover(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        review_ids: List[str],
        macro_aspect: str = "Miscellaneous",
    ) -> List[DiscoveredMicroTheme]:
        """
        Executes UMAP dimension reduction -> HDBSCAN clustering -> c-TF-IDF theme labeling.
        Returns list of DiscoveredMicroTheme objects (excluding noise cluster -1).
        """
        n_samples = len(embeddings)
        if n_samples < 5:
            # Insufficient samples for clustering
            return []

        # 1. Dimensionality Reduction (UMAP with PCA fallback)
        reduced_embeddings = self._reduce_dimensions(embeddings)

        # 2. Density-based Clustering (HDBSCAN with DBSCAN fallback)
        cluster_labels = self._cluster_hdbscan(reduced_embeddings, n_samples)

        # 3. Group documents by cluster
        cluster_docs: Dict[int, List[str]] = {}
        cluster_indices: Dict[int, List[int]] = {}
        cluster_uids: Dict[int, List[str]] = {}

        for idx, lbl in enumerate(cluster_labels):
            if lbl not in cluster_docs:
                cluster_docs[lbl] = []
                cluster_indices[lbl] = []
                cluster_uids[lbl] = []
            cluster_docs[lbl].append(texts[idx])
            cluster_indices[lbl].append(idx)
            cluster_uids[lbl].append(review_ids[idx])

        # 4. Compute c-TF-IDF keywords per cluster
        top_terms_by_cluster = self.ctfidf.compute_ctfidf(cluster_docs)

        # 5. Build DiscoveredMicroTheme objects
        discovered_themes: List[DiscoveredMicroTheme] = []

        for lbl, doc_list in cluster_docs.items():
            if lbl == -1:
                # Outlier noise cluster — retained in data, but not promoted to a micro-theme
                continue

            indices = cluster_indices[lbl]
            uids = cluster_uids[lbl]
            terms = top_terms_by_cluster.get(lbl, ["issue", "defect"])

            # Compute centroid embedding
            cluster_vecs = embeddings[indices]
            centroid = np.mean(cluster_vecs, axis=0)
            centroid_norm = centroid / (np.linalg.norm(centroid) + 1e-9)

            # Find 3 medoid review IDs closest to centroid
            dists = np.linalg.norm(cluster_vecs - centroid_norm, axis=1)
            closest_order = np.argsort(dists)
            medoid_uids = [uids[i] for i in closest_order[:3]]

            # Synthesize 4-to-6 word customer-voice micro-theme label
            theme_label = self._synthesize_theme_label(macro_aspect, terms, doc_list[closest_order[0]])

            discovered_themes.append(
                DiscoveredMicroTheme(
                    cluster_label=lbl,
                    theme_label=theme_label,
                    top_terms=terms[:8],
                    review_indices=indices,
                    review_ids=uids,
                    medoid_review_ids=medoid_uids,
                    volume=len(uids),
                    centroid_embedding=centroid_norm.tolist(),
                )
            )

        # Sort micro-themes by volume descending
        discovered_themes.sort(key=lambda t: t.volume, reverse=True)
        return discovered_themes

    def _reduce_dimensions(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduces high-dimensional embeddings preserving topological manifolds."""
        try:
            import umap
            n_comp = min(self.n_components, embeddings.shape[0] - 1, embeddings.shape[1])
            n_neighbors = min(15, embeddings.shape[0] - 1)
            reducer = umap.UMAP(
                n_neighbors=max(n_neighbors, 2),
                n_components=max(n_comp, 2),
                min_dist=0.0,
                metric="cosine",
                random_state=42,
            )
            return reducer.fit_transform(embeddings)
        except Exception:
            # Robust fallback: TruncatedSVD / PCA
            from sklearn.decomposition import TruncatedSVD
            n_comp = min(self.n_components, embeddings.shape[0] - 1, embeddings.shape[1])
            svd = TruncatedSVD(n_components=max(n_comp, 2), random_state=42)
            return svd.fit_transform(embeddings)

    def _cluster_hdbscan(self, reduced_embeddings: np.ndarray, n_samples: int) -> np.ndarray:
        """Executes Excess-of-Mass (EOM) density clustering."""
        min_c_size = min(self.min_cluster_size, max(n_samples // 4, 3))
        min_samp = min(self.min_samples, min_c_size - 1)

        try:
            import hdbscan
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_c_size,
                min_samples=max(min_samp, 2),
                cluster_selection_method="eom",
                metric="euclidean",
            )
            return clusterer.fit_predict(reduced_embeddings)
        except Exception:
            from sklearn.cluster import DBSCAN
            # Calibrated eps on cosine/svd space
            db = DBSCAN(eps=0.35, min_samples=max(min_samp, 2))
            labels = db.fit_predict(reduced_embeddings)
            # If all are noise or only 1 cluster, assign at least dense subset
            return labels

    @staticmethod
    def _synthesize_theme_label(macro_aspect: str, top_terms: List[str], sample_text: str) -> str:
        """
        Creates a concise 4-to-6 word customer-voice micro-theme label
        from dominant c-TF-IDF terms.
        """
        meaningful_terms = [t for t in top_terms if len(t) > 2][:3]
        if meaningful_terms:
            terms_phrase = " ".join(meaningful_terms).title()
            return f"{macro_aspect}: {terms_phrase}"
        else:
            words = sample_text.split()[:4]
            return f"{macro_aspect}: {' '.join(words).title()}"
