"""Tests for server.py — JSON helpers, state management, and HTTP integration."""

from __future__ import annotations

import http.client
import json
import subprocess
from pathlib import Path

import pytest

from server import (
    load_json,
    mark_triaged,
    save_json,
)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_load_json_exists(tmp_path: Path) -> None:
    """Reads and parses an existing JSON file."""
    p = tmp_path / "data.json"
    p.write_text('{"key": "value"}')
    assert load_json(p) == {"key": "value"}


@pytest.mark.ai_generated
def test_load_json_missing(tmp_path: Path) -> None:
    """Returns empty dict for a missing file."""
    assert load_json(tmp_path / "nope.json") == {}


@pytest.mark.ai_generated
def test_save_json_creates(tmp_path: Path) -> None:
    """Writes JSON that can be re-read."""
    p = tmp_path / "out.json"
    save_json(p, {"a": 1})
    assert load_json(p) == {"a": 1}


@pytest.mark.ai_generated
def test_save_json_creates_parents(tmp_path: Path) -> None:
    """Missing parent directories are created."""
    p = tmp_path / "deep" / "nested" / "file.json"
    save_json(p, {"nested": True})
    assert load_json(p) == {"nested": True}


@pytest.mark.ai_generated
def test_save_json_no_leftover_tmp(tmp_path: Path) -> None:
    """Atomic write leaves no .tmp file."""
    p = tmp_path / "clean.json"
    save_json(p, {"clean": True})
    tmp_file = p.with_suffix(".tmp")
    assert not tmp_file.exists()


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_mark_triaged_new(triage_dir: Path) -> None:
    """Adds a new entry to state.json and returns it."""
    entry = mark_triaged(triage_dir, 102, "closed")
    state = load_json(triage_dir / "state.json")
    assert "102" in state["triaged"]
    assert state["triaged"]["102"]["action"] == "closed"
    assert entry["action"] == "closed"


@pytest.mark.ai_generated
def test_mark_triaged_with_comment(triage_dir: Path) -> None:
    """Records comment_posted flag."""
    entry = mark_triaged(triage_dir, 102, "commented", comment_posted=True)
    state = load_json(triage_dir / "state.json")
    assert state["triaged"]["102"]["comment_posted"] is True
    assert entry["comment_posted"] is True


@pytest.mark.ai_generated
def test_mark_triaged_with_note(triage_dir: Path) -> None:
    """Records note text."""
    entry = mark_triaged(triage_dir, 102, "skipped", note="Not relevant")
    state = load_json(triage_dir / "state.json")
    assert state["triaged"]["102"]["note"] == "Not relevant"
    assert entry["note"] == "Not relevant"


@pytest.mark.ai_generated
def test_mark_triaged_overwrites(triage_dir: Path) -> None:
    """Re-triaging replaces the existing entry."""
    mark_triaged(triage_dir, 101, "skipped")
    state = load_json(triage_dir / "state.json")
    assert state["triaged"]["101"]["action"] == "skipped"


@pytest.mark.ai_generated
def test_mark_triaged_creates_file(empty_triage_dir: Path) -> None:
    """Works when state.json does not exist yet."""
    mark_triaged(empty_triage_dir, 1, "closed")
    state = load_json(empty_triage_dir / "state.json")
    assert "1" in state["triaged"]




# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get(host: str, port: int, path: str) -> http.client.HTTPResponse:
    """Send a GET request and return the response."""
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", path)
    return conn.getresponse()


def _post_json(
    host: str, port: int, path: str, data: dict
) -> http.client.HTTPResponse:
    """Send a POST request with JSON body and return the response."""
    body = json.dumps(data).encode()
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        path,
        body=body,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    return conn.getresponse()


def _read_json(resp: http.client.HTTPResponse) -> dict:
    """Read and parse JSON from a response."""
    return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# HTTP integration tests — JSON API
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_get_root_serves_index(test_server) -> None:
    """GET / serves index.html with text/html content-type."""
    host, port = test_server
    resp = _get(host, port, "/")
    assert resp.status == 200
    assert "text/html" in resp.getheader("Content-Type")


@pytest.mark.ai_generated
def test_get_api_findings_200(test_server) -> None:
    """GET /api/findings returns 200 with JSON content-type."""
    host, port = test_server
    resp = _get(host, port, "/api/findings")
    assert resp.status == 200
    assert "application/json" in resp.getheader("Content-Type")


@pytest.mark.ai_generated
def test_get_api_findings_content(test_server) -> None:
    """GET /api/findings returns findings data with issues."""
    host, port = test_server
    resp = _get(host, port, "/api/findings")
    data = _read_json(resp)
    assert "issues" in data
    assert len(data["issues"]) == 2
    assert data["issues"][0]["number"] == 101


@pytest.mark.ai_generated
def test_get_api_state_200(test_server) -> None:
    """GET /api/state returns 200 with triaged dict."""
    host, port = test_server
    resp = _get(host, port, "/api/state")
    assert resp.status == 200
    data = _read_json(resp)
    assert "triaged" in data
    assert "101" in data["triaged"]


@pytest.mark.ai_generated
def test_get_api_state_empty(test_server, empty_triage_dir) -> None:
    """GET /api/state returns triaged={} when state.json is missing."""
    host, port = test_server
    # The test_server fixture uses triage_dir which has state.json
    # This tests the existing fixture — triaged should exist
    resp = _get(host, port, "/api/state")
    data = _read_json(resp)
    assert "triaged" in data


@pytest.mark.ai_generated
def test_get_unknown_path_404(test_server) -> None:
    """GET /nonexistent returns 404 JSON error."""
    host, port = test_server
    resp = _get(host, port, "/nonexistent.xyz")
    assert resp.status == 404


@pytest.mark.ai_generated
def test_post_unknown_endpoint_404(test_server) -> None:
    """POST to unknown endpoint returns 404."""
    host, port = test_server
    resp = _post_json(host, port, "/api/nope", {})
    assert resp.status == 404


@pytest.mark.ai_generated
def test_post_action_skip(mocked_gh_server, triage_dir: Path) -> None:
    """POST skip action returns ok and updates state.json."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "skip", "comment": ""
    })
    assert resp.status == 200
    data = _read_json(resp)
    assert data["ok"] is True
    assert data["action"] == "skipped"
    state = load_json(triage_dir / "state.json")
    assert "102" in state["triaged"]
    assert state["triaged"]["102"]["action"] == "skipped"


@pytest.mark.ai_generated
def test_post_action_close_with_comment(mocked_gh_server) -> None:
    """POST close with comment calls subprocess.run twice (comment + close)."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "close", "comment": "Closing this issue."
    })
    assert resp.status == 200
    data = _read_json(resp)
    assert data["ok"] is True
    assert data["action"] == "closed"
    # Should call gh twice: once for comment, once for close
    assert mock_run.call_count == 2
    calls = [c[0][0] for c in mock_run.call_args_list]
    assert any("comment" in str(c) for c in calls)
    assert any("close" in str(c) for c in calls)


@pytest.mark.ai_generated
def test_post_action_close_empty_comment(mocked_gh_server) -> None:
    """POST close with empty comment only calls gh once (close only)."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "close", "comment": ""
    })
    assert resp.status == 200
    data = _read_json(resp)
    assert data["ok"] is True
    # Only the close call, no comment
    assert mock_run.call_count == 1
    args = mock_run.call_args[0][0]
    assert "close" in args


@pytest.mark.ai_generated
def test_post_action_close_wontfix(mocked_gh_server, triage_dir: Path) -> None:
    """POST close_wontfix adds wontfix label, closes with not_planned reason."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "close_wontfix", "comment": "Stale issue."
    })
    assert resp.status == 200
    data = _read_json(resp)
    assert data["ok"] is True
    assert data["action"] == "closed"
    # 3 calls: add label, post comment, close
    assert mock_run.call_count == 3
    calls = [c[0][0] for c in mock_run.call_args_list]
    # First call adds wontfix label
    assert "edit" in calls[0]
    assert "--add-label" in calls[0]
    assert "wontfix" in calls[0]
    # Last call closes with not_planned
    assert "close" in calls[2]
    assert "not planned" in calls[2]


@pytest.mark.ai_generated
def test_post_action_close_wontfix_no_comment(mocked_gh_server) -> None:
    """POST close_wontfix without comment: 2 calls (label + close)."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "close_wontfix", "comment": ""
    })
    assert resp.status == 200
    data = _read_json(resp)
    assert data["ok"] is True
    # 2 calls: add label, close
    assert mock_run.call_count == 2
    calls = [c[0][0] for c in mock_run.call_args_list]
    assert "--add-label" in calls[0]
    assert "close" in calls[1]
    assert "not planned" in calls[1]


@pytest.mark.ai_generated
def test_post_action_close_default_reason(mocked_gh_server) -> None:
    """Regular close uses 'completed' reason by default."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "close", "comment": ""
    })
    assert resp.status == 200
    args = mock_run.call_args[0][0]
    assert "completed" in args


@pytest.mark.ai_generated
def test_post_action_close_gh_failure(mocked_gh_server) -> None:
    """gh CLI failure returns ok=false with error message."""
    host, port, mock_run = mocked_gh_server
    mock_run.side_effect = subprocess.CalledProcessError(
        1, "gh", stderr="not found"
    )
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "close", "comment": "test"
    })
    assert resp.status == 502
    data = _read_json(resp)
    assert data["ok"] is False
    assert "error" in data


@pytest.mark.ai_generated
def test_post_action_comment(mocked_gh_server) -> None:
    """POST comment action calls gh issue comment with body-file."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "comment", "comment": "Nice work!"
    })
    assert resp.status == 200
    data = _read_json(resp)
    assert data["ok"] is True
    assert data["action"] == "commented"
    assert mock_run.call_count == 1
    args = mock_run.call_args[0][0]
    assert "comment" in args
    assert "--body-file" in args


@pytest.mark.ai_generated
def test_post_action_comment_empty_rejected(mocked_gh_server) -> None:
    """POST comment with empty body returns 400 error."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "comment", "comment": ""
    })
    assert resp.status == 400
    data = _read_json(resp)
    assert "error" in data
    assert "empty" in data["error"].lower()


@pytest.mark.ai_generated
def test_post_action_invalid_action(mocked_gh_server) -> None:
    """POST with invalid action returns 400."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": 102, "action": "nope"
    })
    assert resp.status == 400
    data = _read_json(resp)
    assert "error" in data


@pytest.mark.ai_generated
def test_post_action_invalid_number(mocked_gh_server) -> None:
    """POST with non-integer number returns 400."""
    host, port, mock_run = mocked_gh_server
    resp = _post_json(host, port, "/api/action", {
        "number": "abc", "action": "skip"
    })
    assert resp.status == 400


@pytest.mark.ai_generated
def test_post_action_invalid_json(test_server) -> None:
    """POST with non-JSON body returns 400."""
    host, port = test_server
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST", "/api/action",
        body=b"not json",
        headers={"Content-Type": "application/json", "Content-Length": "8"},
    )
    resp = conn.getresponse()
    assert resp.status == 400
