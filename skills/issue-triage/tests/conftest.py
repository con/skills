"""Shared fixtures for issue-triage tests."""

from __future__ import annotations

import http.server
import json
import sys
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

# Make the skill modules importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Make test helpers importable
sys.path.insert(0, str(Path(__file__).resolve().parent))


# ---------------------------------------------------------------------------
# Raw gh CLI output fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def raw_gh_issues() -> list[dict]:
    """Two issues in the shape returned by ``gh issue list --json ...``."""
    return [
        {
            "number": 101,
            "title": "Bug: crash on startup",
            "body": "App crashes immediately after launch.\n\nSteps to reproduce...",
            "labels": [{"name": "bug"}, {"name": "priority:high"}],
            "createdAt": "2025-01-15T10:00:00Z",
            "updatedAt": "2025-02-01T12:00:00Z",
            "author": {"login": "alice"},
            "comments": [
                {"createdAt": "2025-01-16T09:00:00Z", "body": "Can reproduce"},
                {"createdAt": "2025-01-20T14:30:00Z", "body": "Fixed in #102"},
            ],
            "url": "https://github.com/owner/repo/issues/101",
        },
        {
            "number": 102,
            "title": "Feature: dark mode",
            "body": "Please add dark mode support.",
            "labels": [{"name": "enhancement"}],
            "createdAt": "2025-02-01T08:00:00Z",
            "updatedAt": "2025-02-01T08:00:00Z",
            "author": {"login": "bob"},
            "comments": [],
            "url": "https://github.com/owner/repo/issues/102",
        },
    ]


@pytest.fixture()
def sample_issues() -> list[dict]:
    """Transformed issues (output of ``transform_issues``)."""
    return [
        {
            "number": 101,
            "title": "Bug: crash on startup",
            "body": "App crashes immediately after launch.\n\nSteps to reproduce...",
            "labels": ["bug", "priority:high"],
            "state": "OPEN",
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-02-01T12:00:00Z",
            "last_comment_at": "2025-01-20T14:30:00Z",
            "author": "alice",
            "comments_count": 2,
            "url": "https://github.com/owner/repo/issues/101",
        },
        {
            "number": 102,
            "title": "Feature: dark mode",
            "body": "Please add dark mode support.",
            "labels": ["enhancement"],
            "state": "OPEN",
            "created_at": "2025-02-01T08:00:00Z",
            "updated_at": "2025-02-01T08:00:00Z",
            "last_comment_at": None,
            "author": "bob",
            "comments_count": 0,
            "url": "https://github.com/owner/repo/issues/102",
        },
    ]


@pytest.fixture()
def sample_findings() -> dict:
    """findings.json with two analyzed issues."""
    return {
        "repo": "owner/repo",
        "analyzed_at": "2025-02-10T12:00:00Z",
        "issues": [
            {
                "number": 101,
                "title": "Bug: crash on startup",
                "verdict": "likely_resolved",
                "confidence": "HIGH",
                "summary": "Fixed in commit abc123",
                "evidence": [
                    {
                        "type": "commit",
                        "ref": "abc123",
                        "message": "Fix crash on startup",
                        "date": "2025-01-18",
                    }
                ],
                "proposed_comment": "This appears to have been fixed in abc123.",
            },
            {
                "number": 102,
                "title": "Feature: dark mode",
                "verdict": "still_open",
                "confidence": "MEDIUM",
                "summary": "No related changes found",
                "evidence": [],
                "proposed_comment": "",
            },
        ],
    }


@pytest.fixture()
def sample_state() -> dict:
    """state.json with one triaged issue."""
    return {
        "triaged": {
            "101": {
                "action": "closed",
                "at": "2025-02-11T10:00:00Z",
                "comment_posted": True,
            }
        }
    }


@pytest.fixture()
def empty_state() -> dict:
    return {}


@pytest.fixture()
def triage_dir(tmp_path: Path, sample_issues, sample_findings, sample_state) -> Path:
    """On-disk triage directory populated with all 3 JSON files."""
    d = tmp_path / "triage"
    d.mkdir()
    (d / "issues.json").write_text(
        json.dumps({"repo": "owner/repo", "issues": sample_issues})
    )
    (d / "findings.json").write_text(json.dumps(sample_findings))
    (d / "state.json").write_text(json.dumps(sample_state))
    return d


@pytest.fixture()
def empty_triage_dir(tmp_path: Path) -> Path:
    """Triage directory with no files."""
    d = tmp_path / "triage-empty"
    d.mkdir()
    return d


@pytest.fixture()
def test_server(triage_dir: Path):
    """Start an ephemeral HTTP server on port 0, yield ``(host, port)``."""
    from server import make_handler

    handler_cls = make_handler(triage_dir, "owner/repo")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    host, port = srv.server_address
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield host, port
    srv.shutdown()


@pytest.fixture()
def mocked_gh_server(triage_dir: Path):
    """HTTP server with ``subprocess.run`` patched (no real ``gh`` calls)."""
    from server import make_handler

    handler_cls = make_handler(triage_dir, "owner/repo")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    host, port = srv.server_address
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = None  # _run_gh ignores return value on success
        yield host, port, mock_run

    srv.shutdown()
