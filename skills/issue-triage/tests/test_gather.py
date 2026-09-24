"""Tests for gather.py — issue gathering and transformation."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from gather import (
    compute_last_comment_at,
    detect_repo,
    gather_from_gh,
    get_head_sha,
    transform_issues,
)


# ---------------------------------------------------------------------------
# compute_last_comment_at — pure function tests
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_compute_last_comment_at_with_comments() -> None:
    """Returns the max createdAt among comments."""
    comments = [
        {"createdAt": "2025-01-10T09:00:00Z"},
        {"createdAt": "2025-01-20T14:30:00Z"},
        {"createdAt": "2025-01-15T11:00:00Z"},
    ]
    assert compute_last_comment_at(comments) == "2025-01-20T14:30:00Z"


@pytest.mark.ai_generated
def test_compute_last_comment_at_empty() -> None:
    """Returns None for an empty list."""
    assert compute_last_comment_at([]) is None


@pytest.mark.ai_generated
def test_compute_last_comment_at_missing_dates() -> None:
    """Returns None when no comment has a createdAt field."""
    comments = [{"body": "no date"}, {"body": "also none"}]
    assert compute_last_comment_at(comments) is None


@pytest.mark.ai_generated
def test_compute_last_comment_at_single() -> None:
    """Works correctly for exactly one comment."""
    comments = [{"createdAt": "2025-03-01T00:00:00Z"}]
    assert compute_last_comment_at(comments) == "2025-03-01T00:00:00Z"


# ---------------------------------------------------------------------------
# transform_issues — pure function tests
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_transform_issues_full(raw_gh_issues: list[dict]) -> None:
    """Two-issue input produces correct schema with all fields."""
    result = transform_issues(raw_gh_issues)
    assert len(result) == 2

    first = result[0]
    assert first["number"] == 101
    assert first["title"] == "Bug: crash on startup"
    assert first["state"] == "OPEN"
    assert first["author"] == "alice"
    assert first["comments_count"] == 2
    assert first["last_comment_at"] == "2025-01-20T14:30:00Z"
    assert first["labels"] == ["bug", "priority:high"]
    assert first["url"] == "https://github.com/owner/repo/issues/101"


@pytest.mark.ai_generated
def test_transform_issues_empty() -> None:
    """Empty input produces empty output."""
    assert transform_issues([]) == []


@pytest.mark.ai_generated
def test_transform_issues_missing_fields() -> None:
    """Graceful defaults when body, labels, and author are missing."""
    raw = [{"number": 1, "title": "Minimal issue"}]
    result = transform_issues(raw)
    assert len(result) == 1
    issue = result[0]
    assert issue["body"] == ""
    assert issue["labels"] == []
    assert issue["author"] == "unknown"


@pytest.mark.ai_generated
def test_transform_issues_labels_extracted() -> None:
    """Label dicts are flattened to name strings."""
    raw = [
        {
            "number": 5,
            "title": "Labeled",
            "labels": [{"name": "bug"}, {"name": "help wanted"}],
        }
    ]
    result = transform_issues(raw)
    assert result[0]["labels"] == ["bug", "help wanted"]


@pytest.mark.ai_generated
def test_transform_issues_no_comments() -> None:
    """Issue with no comments gets count=0 and last_comment_at=None."""
    raw = [{"number": 9, "title": "No comments", "comments": []}]
    result = transform_issues(raw)
    assert result[0]["comments_count"] == 0
    assert result[0]["last_comment_at"] is None


# ---------------------------------------------------------------------------
# detect_repo — subprocess mocks
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_detect_repo_ssh() -> None:
    """SSH remote URL parsed correctly."""
    mock_result = MagicMock()
    mock_result.stdout = "git@github.com:owner/repo.git\n"
    with patch("gather.subprocess.run", return_value=mock_result):
        assert detect_repo() == "owner/repo"


@pytest.mark.ai_generated
def test_detect_repo_https() -> None:
    """HTTPS remote URL parsed correctly."""
    mock_result = MagicMock()
    mock_result.stdout = "https://github.com/owner/repo.git\n"
    with patch("gather.subprocess.run", return_value=mock_result):
        assert detect_repo() == "owner/repo"


@pytest.mark.ai_generated
def test_detect_repo_no_dotgit() -> None:
    """URL without .git suffix still works."""
    mock_result = MagicMock()
    mock_result.stdout = "https://github.com/owner/repo\n"
    with patch("gather.subprocess.run", return_value=mock_result):
        assert detect_repo() == "owner/repo"


@pytest.mark.ai_generated
def test_detect_repo_unknown_host() -> None:
    """Non-GitHub URL raises ValueError."""
    mock_result = MagicMock()
    mock_result.stdout = "https://gitlab.com/owner/repo.git\n"
    with patch("gather.subprocess.run", return_value=mock_result):
        with pytest.raises(ValueError, match="Cannot parse repo"):
            detect_repo()


@pytest.mark.ai_generated
def test_detect_repo_subprocess_fails() -> None:
    """CalledProcessError propagates from subprocess."""
    with patch(
        "gather.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "git"),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            detect_repo()


# ---------------------------------------------------------------------------
# gather_from_gh — subprocess mocks
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_gather_from_gh_basic() -> None:
    """Correct gh args assembled without --label."""
    mock_result = MagicMock()
    mock_result.stdout = "[]"
    with patch("gather.subprocess.run", return_value=mock_result) as mock_run:
        result = gather_from_gh("owner/repo", 50)
        assert result == []
        args = mock_run.call_args[0][0]
        assert "--repo" in args
        assert "owner/repo" in args
        assert "--limit" in args
        assert "50" in args
        assert "--label" not in args


@pytest.mark.ai_generated
def test_gather_from_gh_with_label() -> None:
    """--label is appended when label argument is provided."""
    mock_result = MagicMock()
    mock_result.stdout = "[]"
    with patch("gather.subprocess.run", return_value=mock_result) as mock_run:
        gather_from_gh("owner/repo", 10, label="bug")
        args = mock_run.call_args[0][0]
        assert "--label" in args
        idx = args.index("--label")
        assert args[idx + 1] == "bug"


@pytest.mark.ai_generated
def test_gather_from_gh_parses_json() -> None:
    """JSON stdout is parsed to a list of dicts."""
    mock_result = MagicMock()
    mock_result.stdout = json.dumps([{"number": 1, "title": "Test"}])
    with patch("gather.subprocess.run", return_value=mock_result):
        result = gather_from_gh("owner/repo", 10)
        assert len(result) == 1
        assert result[0]["number"] == 1


# ---------------------------------------------------------------------------
# get_head_sha — subprocess mocks
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_get_head_sha_success() -> None:
    """Returns the stripped SHA from git rev-parse."""
    mock_result = MagicMock()
    mock_result.stdout = "abc1234def5678\n"
    with patch("gather.subprocess.run", return_value=mock_result):
        assert get_head_sha() == "abc1234def5678"


@pytest.mark.ai_generated
def test_get_head_sha_failure() -> None:
    """Returns empty string when git rev-parse fails."""
    with patch(
        "gather.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "git"),
    ):
        assert get_head_sha() == ""
