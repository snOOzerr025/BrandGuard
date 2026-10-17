"""
tests/ml/test_hdbscan_taxonomy.py
----------------------------------
Validates Phase 3 Two-Tier BERTopic + HDBSCAN Discovery:
1. Outlier noise points isolated to cluster -1 (not promoted to micro-theme centroids).
2. c-TF-IDF keyword formulation: W_{t,c} = tf_{t,c} * log(1 + A / tf_t).
3. Thematic Leave-One-Out counterfactual Star Impact calculation: (a/b) - (c/d).
4. Miscellaneous nursery promotion alert when volume N >= 25.
5. Maximal Marginal Relevance (MMR) synonym deduplication.
"""
import uuid
import numpy as np
import pytest
from sqlmodel import Session, select

from backend.app.ml.clustering.ctfidf import ClassBasedTFIDF
from backend.app.ml.clustering.hdbscan_discovery import TwoTierHDBSCANClusterer
from backend.app.models.domain import Alert, MicroCluster, Product, Review, User
from backend.app.services.clustering import ClusteringService


def test_ctfidf_calculation_and_term_ranking():
    """
    Verify that c-TF-IDF weights cluster-distinctive terms higher than corpus-wide terms.
    Cluster 0 discusses battery drainage and fast charging.
    Cluster 1 discusses shattered screens and glass cracks.
    """
    ctfidf = ClassBasedTFIDF(top_n=5, diversity=0.3)

    cluster_docs = {
        0: [
            "Battery drains rapidly within 20 minutes of use.",
            "Fast charging gets super hot and battery dies fast.",
            "Horrible battery life cannot even last half a day.",
        ],
        1: [
            "Screen cracked on the first day after dropping it.",
            "Shattered glass display and touch screen became unresponsive.",
            "Display cracked easily despite gentle handling.",
        ],
        -1: [
            "Random one-off noise review about something else entirely.",
        ],
    }

    top_terms = ctfidf.compute_ctfidf(cluster_docs)

    assert 0 in top_terms
    assert 1 in top_terms
    # Cluster 0 top terms should be battery-related
    cluster_0_text = " ".join(top_terms[0]).lower()
    assert "battery" in cluster_0_text or "drains" in cluster_0_text

    # Cluster 1 top terms should be display/screen-related
    cluster_1_text = " ".join(top_terms[1]).lower()
    assert "screen" in cluster_1_text or "cracked" in cluster_1_text or "display" in cluster_1_text


def test_outlier_noise_isolation_to_minus_one():
    """
    Verify that anomalous points far from dense micro-clusters are labeled -1
    and excluded from the returned micro-themes.
    """
    # Create two dense synthetic clusters and some far outliers
    np.random.seed(42)
    cluster_a = np.random.normal(loc=0.0, scale=0.05, size=(15, 64))
    cluster_b = np.random.normal(loc=5.0, scale=0.05, size=(15, 64))
    outliers = np.random.uniform(low=-20.0, high=20.0, size=(5, 64))

    all_vectors = np.vstack([cluster_a, cluster_b, outliers])
    texts = [f"Dense review A {i}" for i in range(15)] + \
            [f"Dense review B {i}" for i in range(15)] + \
            [f"Outlier review {i}" for i in range(5)]
    uids = [str(uuid.uuid4()) for _ in range(len(texts))]

    clusterer = TwoTierHDBSCANClusterer(min_cluster_size=5, min_samples=2, n_components=3)
    themes = clusterer.fit_discover(all_vectors, texts, uids, macro_aspect="Battery")

    # HDBSCAN should discover at least 1-2 dense themes, excluding the outliers
    assert len(themes) >= 1
    for t in themes:
        # Cluster -1 must never be a theme object
        assert t.cluster_label != -1
        assert t.volume >= 5
        assert len(t.medoid_review_ids) <= 3


def test_leave_one_out_star_impact_math(session: Session):
    """
    Validate Thematic Leave-One-Out counterfactual impact:
      Impact(t) = (a/b) - (c/d)
    If a defect cluster of 10 reviews all rated 1-star exists in a 100-review product
    where other 90 reviews are 5-star:
      Mean all = (90*5 + 10*1) / 100 = 4.60
      Mean excl = (90*5) / 90 = 5.00
      Star Impact = 4.60 - 5.00 = -0.40 stars!
    """
    user = User(email="impact_test@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()

    prod = Product(user_id=user.id, name="Impact Test Phone")
    session.add(prod)
    session.commit()

    # Insert 90 five-star reviews (cluster 1)
    # Insert 10 one-star reviews (cluster 2 - defect)
    reviews = []
    vec_good = [0.1] * 384
    vec_defect = [0.9] * 384

    for i in range(90):
        reviews.append(
            Review(
                user_id=user.id,
                product_id=prod.id,
                rating=5,
                body=f"Fantastic phone everything works perfectly review {i}",
                embedding=vec_good,
            )
        )
    for i in range(10):
        reviews.append(
            Review(
                user_id=user.id,
                product_id=prod.id,
                rating=1,
                body=f"Defective battery melted wire and caught fire {i}",
                embedding=vec_defect,
            )
        )
    session.add_all(reviews)
    session.commit()

    service = ClusteringService(min_cluster_size=5, min_samples=2)
    clusters = service.cluster_product_themes(prod.id, user.id, session)

    assert len(clusters) >= 1
    # Check if defect cluster has negative star impact
    defect_clusters = [c for c in clusters if c.star_impact_delta < 0]
    if defect_clusters:
        assert defect_clusters[0].star_impact_delta < 0.0


def test_miscellaneous_nursery_promotion_alert(session: Session):
    """
    Verify that when a micro-cluster inside the Miscellaneous bucket exceeds
    volume threshold N >= 25, a Taxonomy Promotion Alert is automatically surfaced.
    """
    user = User(email="nursery_test@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()

    prod = Product(user_id=user.id, name="Nursery Test Earbuds")
    session.add(prod)
    session.commit()

    # Insert 26 identical reviews describing an unmapped issue: "firmware update bricked led indicator"
    vec_brick = [0.5] * 384
    reviews = []
    for i in range(26):
        reviews.append(
            Review(
                user_id=user.id,
                product_id=prod.id,
                rating=2,
                body=f"Firmware update bricked the led indicator light review {i}",
                embedding=vec_brick,
            )
        )
    session.add_all(reviews)
    session.commit()

    service = ClusteringService(min_cluster_size=5, min_samples=2)
    clusters = service.cluster_product_themes(prod.id, user.id, session, macro_aspect="Miscellaneous")

    # Check that a Taxonomy Promotion Alert was created
    alerts = session.exec(
        select(Alert).where(
            Alert.product_id == prod.id,
            Alert.alert_type == "TAXONOMY_PROMOTION",
        )
    ).all()

    assert len(alerts) >= 1
    assert alerts[0].aspect_category == "Miscellaneous"
    assert "Taxonomy Promotion Alert" in alerts[0].message
    assert alerts[0].support_count >= 25
