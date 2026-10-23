"""
tests/workers/test_jira_sync.py
-------------------------------
Unit and integration tests for JIRA issue automation:
1. MockJiraClient operation (create_issue, add_comment, get_issue)
2. create_jira_issue_for_alert task execution
3. Deduplication and idempotency by alert fingerprint
4. Skip-and-comment when an open ticket exists for product+aspect
5. _execute_anomaly_detection hook for HIGH and CRITICAL alerts
"""
import uuid
from datetime import datetime, timezone
import pytest
from sqlmodel import Session, select

from backend.app.models.domain import (
    Alert,
    JiraIssue,
    Product,
    SeverityTier,
    User,
)
from backend.app.services.jira_service import MockJiraClient, get_jira_client
from backend.app.workers.tasks import (
    _execute_anomaly_detection,
    create_jira_issue_for_alert,
)


@pytest.fixture(name="jira_test_setup")
def jira_test_setup_fixture(session: Session):
    """Creates a user and product for JIRA testing."""
    user = User(
        email=f"jira_test_{uuid.uuid4().hex[:6]}@brandguard.ai",
        hashed_password="pw",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    product = Product(
        user_id=user.id,
        name="Axis Mobile App",
        category="Fintech",
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    return {"user": user, "product": product}


def test_mock_jira_client_operations():
    """Verify MockJiraClient creates issues, adds comments, and retrieves data."""
    client = MockJiraClient(project_key="AXIS")
    
    # 1. Create issue
    res = client.create_issue(
        summary="Test CX Issue",
        description="Detailed description with metrics",
        priority="High",
        issue_type="Bug",
        labels=["brandguard", "cx-test"],
    )
    assert "key" in res
    assert res["key"].startswith("AXIS-")
    issue_key = res["key"]

    # 2. Get issue
    issue = client.get_issue(issue_key)
    assert issue["summary"] == "Test CX Issue"
    assert issue["status"] == "To Do"
    assert issue["priority"] == "High"

    # 3. Add comment
    comment_res = client.add_comment(issue_key, "Recurrence update: additional negative reviews.")
    assert comment_res["body"] == "Recurrence update: additional negative reviews."
    assert len(client.comments[issue_key]) == 1


def test_create_jira_issue_for_critical_alert(session: Session, jira_test_setup):
    """Verify create_jira_issue_for_alert creates a ticket for a CRITICAL alert."""
    user = jira_test_setup["user"]
    product = jira_test_setup["product"]

    alert = Alert(
        user_id=user.id,
        product_id=product.id,
        aspect_category="Onboarding/KYC",
        severity=SeverityTier.CRITICAL,
        alert_type="EWMA_DRIFT",
        z_score=-3.42,
        baseline_mean=0.45,
        current_value=-0.65,
        star_impact=-0.48,
        support_count=35,
        message="Critical negative drift in Onboarding/KYC",
        evidence_review_ids=["rev-001", "rev-002"],
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)

    # Execute task
    result = create_jira_issue_for_alert(
        alert_id_str=str(alert.id),
        user_id_str=str(user.id),
        db_session=session,
    )

    assert result["status"] == "CREATED"
    assert "jira_key" in result
    jira_key = result["jira_key"]

    # Verify persisted JiraIssue in DB
    saved_issue = session.exec(
        select(JiraIssue).where(JiraIssue.alert_id == alert.id)
    ).first()
    assert saved_issue is not None
    assert saved_issue.jira_key == jira_key
    assert saved_issue.status == "To Do"
    assert "Onboarding/KYC" in (saved_issue.summary or "")


def test_jira_alert_idempotency_and_deduplication(session: Session, jira_test_setup):
    """Running create_jira_issue_for_alert twice on the same alert must not create duplicate issues."""
    user = jira_test_setup["user"]
    product = jira_test_setup["product"]

    alert = Alert(
        user_id=user.id,
        product_id=product.id,
        aspect_category="UPI/Payments",
        severity=SeverityTier.HIGH,
        alert_type="RATING_IMPACT",
        z_score=-2.85,
        star_impact=-0.22,
        support_count=20,
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)

    # First call -> CREATED
    res1 = create_jira_issue_for_alert(str(alert.id), str(user.id), db_session=session)
    assert res1["status"] == "CREATED"
    key1 = res1["jira_key"]

    # Second call -> ALREADY_SYNCED
    res2 = create_jira_issue_for_alert(str(alert.id), str(user.id), db_session=session)
    assert res2["status"] == "ALREADY_SYNCED"
    assert res2["jira_key"] == key1

    # Verify only one JiraIssue record exists for this alert
    issues = session.exec(select(JiraIssue).where(JiraIssue.alert_id == alert.id)).all()
    assert len(issues) == 1


def test_skip_and_comment_when_open_ticket_exists(session: Session, jira_test_setup):
    """
    If an open ticket exists for the same product and aspect, a new alert for that aspect
    must NOT create a second ticket; it should append a comment to the existing open ticket.
    """
    user = jira_test_setup["user"]
    product = jira_test_setup["product"]

    # 1. Alert 1 (Day 1) -> creates first ticket
    alert1 = Alert(
        user_id=user.id,
        product_id=product.id,
        aspect_category="Login/Auth",
        severity=SeverityTier.HIGH,
        alert_type="EWMA_DRIFT",
        z_score=-2.65,
        star_impact=-0.18,
        support_count=18,
        dedup_fingerprint="fingerprint-day-1",
    )
    session.add(alert1)
    session.commit()
    session.refresh(alert1)

    res1 = create_jira_issue_for_alert(str(alert1.id), str(user.id), db_session=session)
    assert res1["status"] == "CREATED"
    parent_jira_key = res1["jira_key"]

    # 2. Alert 2 (Day 2) -> same product, same aspect ("Login/Auth")
    alert2 = Alert(
        user_id=user.id,
        product_id=product.id,
        aspect_category="Login/Auth",
        severity=SeverityTier.CRITICAL,
        alert_type="EWMA_DRIFT",
        z_score=-3.10,
        star_impact=-0.25,
        support_count=28,
        dedup_fingerprint="fingerprint-day-2",
    )
    session.add(alert2)
    session.commit()
    session.refresh(alert2)

    res2 = create_jira_issue_for_alert(str(alert2.id), str(user.id), db_session=session)
    assert res2["status"] == "COMMENTED_ON_EXISTING"
    assert res2["jira_key"] == parent_jira_key

    # Check MockJiraClient received comment
    mock_client = get_jira_client(force_mock=True)
    if isinstance(mock_client, MockJiraClient):
        comments = mock_client.comments.get(parent_jira_key, [])
        assert len(comments) >= 1
        assert "Login/Auth" in comments[0]["body"]

    # Verify alert2 has a JiraIssue row linked to parent_jira_key
    jira_issue2 = session.exec(select(JiraIssue).where(JiraIssue.alert_id == alert2.id)).first()
    assert jira_issue2 is not None
    assert jira_issue2.jira_key == parent_jira_key


def test_resolved_ticket_allows_new_ticket(session: Session, jira_test_setup):
    """
    If the previous ticket for an aspect is marked 'Done'/'Resolved', a subsequent alert
    creates a NEW ticket instead of commenting on the resolved one.
    """
    user = jira_test_setup["user"]
    product = jira_test_setup["product"]

    # Alert 1 -> Creates Ticket
    alert1 = Alert(
        user_id=user.id,
        product_id=product.id,
        aspect_category="Customer Support",
        severity=SeverityTier.HIGH,
        alert_type="EWMA_DRIFT",
        z_score=-2.55,
        star_impact=-0.15,
        support_count=15,
        dedup_fingerprint="fingerprint-support-1",
    )
    session.add(alert1)
    session.commit()
    session.refresh(alert1)

    res1 = create_jira_issue_for_alert(str(alert1.id), str(user.id), db_session=session)
    key1 = res1["jira_key"]

    # Engineering marks key1 as Done
    issue1_rec = session.exec(select(JiraIssue).where(JiraIssue.alert_id == alert1.id)).first()
    assert issue1_rec is not None
    issue1_rec.status = "Done"
    session.add(issue1_rec)
    session.commit()

    # Alert 2 -> A new issue should be created
    alert2 = Alert(
        user_id=user.id,
        product_id=product.id,
        aspect_category="Customer Support",
        severity=SeverityTier.CRITICAL,
        alert_type="VOLUME_BURST",
        z_score=-3.50,
        star_impact=-0.35,
        support_count=40,
        dedup_fingerprint="fingerprint-support-2",
    )
    session.add(alert2)
    session.commit()
    session.refresh(alert2)

    res2 = create_jira_issue_for_alert(str(alert2.id), str(user.id), db_session=session)
    assert res2["status"] == "CREATED"
    assert res2["jira_key"] != key1


def test_execute_anomaly_detection_jira_dispatch(session: Session, jira_test_setup, monkeypatch):
    """Verify that _execute_anomaly_detection calls AlertService.scan and dispatches JIRA issues."""
    user = jira_test_setup["user"]
    product = jira_test_setup["product"]

    # Create dummy alerts returned by scan
    alert_crit = Alert(
        user_id=user.id,
        product_id=product.id,
        aspect_category="Performance",
        severity=SeverityTier.CRITICAL,
        alert_type="EWMA_DRIFT",
        z_score=-3.2,
        star_impact=-0.3,
        support_count=25,
        dedup_fingerprint="fingerprint-crit-hook",
    )
    session.add(alert_crit)
    session.commit()
    session.refresh(alert_crit)

    # Mock AlertService.scan to return alert_crit
    from backend.app.services.alert_service import AlertService
    monkeypatch.setattr(AlertService, "scan", lambda p_id, u, db: [alert_crit])

    # Intercept Celery task dispatch so test doesn't depend on a live Redis broker
    monkeypatch.setattr(
        create_jira_issue_for_alert,
        "apply_async",
        lambda args=None, **kwargs: create_jira_issue_for_alert(args[0], args[1], db_session=session),
    )

    # Execute _execute_anomaly_detection
    dispatched_count = _execute_anomaly_detection(session, user.id, product.id)
    assert dispatched_count == 1

    # Verify that JiraIssue was created for alert_crit
    jira_rec = session.exec(select(JiraIssue).where(JiraIssue.alert_id == alert_crit.id)).first()
    assert jira_rec is not None
    assert jira_rec.jira_key.startswith("AXIS-")

