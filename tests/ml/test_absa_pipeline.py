"""
tests/ml/test_absa_pipeline.py
-------------------------------
Validates Phase 2 SOTA ONNX INT8 ABSA Pipeline:
1. Multi-clause contrastive disentanglement (no polarity averaging across 'though'/'but').
2. Zero-keyword implicit aspect detection (functional behaviors mapped to canonical aspects).
3. Miscellaneous nursery bucket routing for novel/out-of-domain feedback.
4. Star-vs-text rating discrepancy detection.
5. Soft-output drift indicators (PSI, JSD, nursery percentage).
"""
import uuid
import pytest
from sqlmodel import Session, select

from backend.app.ml.absa.acd_engine import ACDEngine
from backend.app.ml.absa.onnx_engine import ONNXABSAEngine
from backend.app.ml.eval.drift_monitor import ABSADriftMonitor, calculate_jsd, calculate_psi
from backend.app.models.domain import PolarityLabel, Product, Review, SentimentResult, User
from backend.app.services.absa_service import ABSAService


def test_multi_clause_contrastive_disentanglement():
    """
    Test the fundamental failure mode of the legacy DistilBERT baseline:
    A sentence with multiple clauses of opposing sentiment MUST NOT be averaged.
    """
    sentence = "The battery lasts all week, though the plastic casing feels cheap and arrived dented."
    acd = ACDEngine()
    asc = ONNXABSAEngine()

    activations = acd.detect_aspects(sentence)
    aspect_names = {a.aspect for a in activations}
    assert "Battery" in aspect_names
    assert "Quality" in aspect_names
    assert "Packaging" in aspect_names

    # Check sentiment per aspect
    results = {}
    for act in activations:
        out = asc.classify_aspect_polarity(sentence, act.aspect, act.extracted_span, act.is_implicit)
        results[act.aspect] = out.polarity

    assert results["Battery"] == PolarityLabel.POSITIVE
    assert results["Quality"] == PolarityLabel.NEGATIVE
    assert results["Packaging"] == PolarityLabel.NEGATIVE


def test_implicit_aspect_detection():
    """
    Test zero-keyword functional behavior detection without explicit nouns:
    'shut off after 20 minutes' -> Battery: Negative
    'took three weeks to reach' -> Delivery: Negative
    """
    acd = ACDEngine()
    asc = ONNXABSAEngine()

    s1 = "It shut off after 20 minutes and refused to turn back on."
    act1 = acd.detect_aspects(s1)
    assert len(act1) >= 1
    assert act1[0].aspect == "Battery"
    assert act1[0].is_implicit is True
    out1 = asc.classify_aspect_polarity(s1, act1[0].aspect, act1[0].extracted_span, act1[0].is_implicit)
    assert out1.polarity == PolarityLabel.NEGATIVE

    s2 = "Took three weeks to reach Mumbai and the courier was unresponsive."
    act2 = acd.detect_aspects(s2)
    assert len(act2) >= 1
    assert any(a.aspect == "Delivery" and a.is_implicit is True for a in act2)


def test_miscellaneous_nursery_bucket_routing():
    """Novel complaints not matching any canonical aspect must route to Miscellaneous."""
    acd = ACDEngine()
    sentence = "The purple extraterrestrial unicorn beamed down into the garden."
    activations = acd.detect_aspects(sentence)
    assert len(activations) == 1
    assert activations[0].aspect == "Miscellaneous"


def test_star_vs_text_rating_discrepancy(session: Session):
    """
    A 5-star review that has purely negative text must be flagged with has_rating_discrepancy=True.
    """
    user = User(email="discrepancy_test@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()

    prod = Product(user_id=user.id, name="Discrepancy Earbuds")
    session.add(prod)
    session.commit()

    # User accidentally clicked 5 stars but text says it broke immediately
    rev = Review(
        user_id=user.id,
        product_id=prod.id,
        rating=5,
        body="Terrible purchase. It broke in two days and battery died within an hour.",
    )
    session.add(rev)
    session.commit()
    session.refresh(rev)

    service = ABSAService()
    service.process_review(rev.id, rev.body, user.id, prod.id, session)

    session.refresh(rev)
    assert rev.has_rating_discrepancy is True


def test_drift_monitoring_metrics():
    """Verify PSI, JSD, and nursery drift calculations."""
    base_dist = [0.60, 0.20, 0.20]
    stable_dist = [0.58, 0.22, 0.20]
    shifted_dist = [0.20, 0.20, 0.60]

    psi_stable = calculate_psi(base_dist, stable_dist)
    psi_shifted = calculate_psi(base_dist, shifted_dist)
    assert psi_stable < 0.05
    assert psi_shifted > 0.30

    jsd_stable = calculate_jsd(base_dist, stable_dist)
    jsd_shifted = calculate_jsd(base_dist, shifted_dist)
    assert jsd_stable < 0.10
    assert jsd_shifted > 0.30

    # Test nursery growth rate trigger (>= 12%)
    monitor = ABSADriftMonitor(misc_threshold_pct=12.0)
    aspect_counts_ok = {"Battery": 80, "Quality": 40, "Miscellaneous": 5}
    res_ok = monitor.check_nursery_growth(aspect_counts_ok)
    assert res_ok["is_drift_detected"] is False

    aspect_counts_drift = {"Battery": 80, "Quality": 40, "Miscellaneous": 30}
    res_drift = monitor.check_nursery_growth(aspect_counts_drift)
    assert res_drift["is_drift_detected"] is True
