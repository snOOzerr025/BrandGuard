"""
backend.app.services.jira_service
---------------------------------
JIRA integration service supporting both Atlassian JIRA Cloud REST API v3
and an in-memory MockJiraClient for offline testing and local development.
"""
from __future__ import annotations

import base64
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class BaseJiraClient(ABC):
    @abstractmethod
    def create_issue(
        self,
        summary: str,
        description: str,
        priority: str = "Medium",
        issue_type: str = "Bug",
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new JIRA issue and return a dictionary with key, id, etc."""
        pass

    @abstractmethod
    def add_comment(self, issue_key: str, comment_text: str) -> Dict[str, Any]:
        """Add a comment to an existing JIRA issue."""
        pass

    @abstractmethod
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Retrieve issue details including status."""
        pass


class MockJiraClient(BaseJiraClient):
    """
    In-memory mock JIRA client for offline execution and deterministic test suites.
    Requires no network calls, credentials, or external API availability.
    """
    def __init__(self, project_key: str = "AXIS"):
        self.project_key = project_key
        self.issues: Dict[str, Dict[str, Any]] = {}
        self.comments: Dict[str, List[Dict[str, Any]]] = {}
        self._counter = 100

    def create_issue(
        self,
        summary: str,
        description: str,
        priority: str = "Medium",
        issue_type: str = "Bug",
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        self._counter += 1
        key = f"{self.project_key}-{self._counter}"
        issue_id = str(self._counter)
        record = {
            "id": issue_id,
            "key": key,
            "summary": summary,
            "description": description,
            "priority": priority,
            "issue_type": issue_type,
            "labels": labels or [],
            "status": "To Do",
        }
        self.issues[key] = record
        self.comments[key] = []
        logger.info("[MockJiraClient] Created issue %s: %s", key, summary)
        return {
            "id": issue_id,
            "key": key,
            "self": f"https://mock-jira.local/rest/api/3/issue/{issue_id}",
        }

    def add_comment(self, issue_key: str, comment_text: str) -> Dict[str, Any]:
        if issue_key not in self.comments:
            self.comments[issue_key] = []
        comment_record = {
            "id": str(len(self.comments[issue_key]) + 1),
            "body": comment_text,
        }
        self.comments[issue_key].append(comment_record)
        logger.info("[MockJiraClient] Added comment to %s", issue_key)
        return comment_record

    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        if issue_key in self.issues:
            return self.issues[issue_key]
        raise ValueError(f"Issue {issue_key} not found in MockJiraClient")


class JiraClient(BaseJiraClient):
    """
    Production REST API v3 client for Atlassian JIRA Cloud.
    Authenticates via HTTP Basic Auth (email + API token).
    """
    def __init__(
        self,
        domain: str,
        email: str,
        api_token: str,
        project_key: str = "AXIS",
        timeout: float = 10.0,
    ):
        clean_domain = domain.strip().rstrip("/")
        if not clean_domain.startswith("http://") and not clean_domain.startswith("https://"):
            clean_domain = f"https://{clean_domain}"
        self.base_url = f"{clean_domain}/rest/api/3"
        self.project_key = project_key
        self.timeout = timeout

        auth_str = f"{email}:{api_token}"
        b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        self.headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _text_to_adf(self, text: str) -> Dict[str, Any]:
        """Convert plain text into an Atlassian Document Format (ADF) block."""
        paragraphs = text.split("\n\n")
        content_nodes = []
        for p in paragraphs:
            if not p.strip():
                continue
            content_nodes.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": p.strip()}],
            })
        if not content_nodes:
            content_nodes = [{
                "type": "paragraph",
                "content": [{"type": "text", "text": text or "No details provided."}],
            }]
        return {
            "type": "doc",
            "version": 1,
            "content": content_nodes,
        }

    def create_issue(
        self,
        summary: str,
        description: str,
        priority: str = "Medium",
        issue_type: str = "Bug",
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary[:255],
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
                "labels": labels or [],
                "description": self._text_to_adf(description),
            }
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/issue", headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Created JIRA issue %s for project %s", data.get("key"), self.project_key)
            return data

    def add_comment(self, issue_key: str, comment_text: str) -> Dict[str, Any]:
        payload = {"body": self._text_to_adf(comment_text)}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/issue/{issue_key}/comment", headers=self.headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/issue/{issue_key}", headers=self.headers)
            resp.raise_for_status()
            return resp.json()


_global_mock_jira_client: Optional[MockJiraClient] = None


def get_jira_client(force_mock: bool = False) -> BaseJiraClient:
    """
    Factory function: returns JiraClient if JIRA_ENABLED=True and credentials exist;
    otherwise returns a singleton MockJiraClient.
    """
    global _global_mock_jira_client

    if not force_mock and settings.JIRA_ENABLED and settings.JIRA_API_TOKEN and settings.JIRA_DOMAIN and settings.JIRA_EMAIL:
        return JiraClient(
            domain=settings.JIRA_DOMAIN,
            email=settings.JIRA_EMAIL,
            api_token=settings.JIRA_API_TOKEN,
            project_key=settings.JIRA_PROJECT_KEY,
        )

    if _global_mock_jira_client is None:
        _global_mock_jira_client = MockJiraClient(project_key=settings.JIRA_PROJECT_KEY)
    return _global_mock_jira_client
