"""Tests for templates.py — HTML rendering and utility functions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from templates import (
    _confidence_badge,
    _days_ago,
    _escape,
    _format_date,
    _label_badges,
    _parse_dt,
    _status_badge,
    _verdict_badge,
    base_layout,
    render_dashboard,
    render_export,
    render_flash,
    render_issue_detail,
)

from helpers import FrozenDatetime


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_escape_html() -> None:
    """HTML special characters are escaped."""
    assert _escape("<script>alert('xss')</script>") == (
        "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    )


@pytest.mark.ai_generated
def test_escape_empty() -> None:
    """Empty string returns empty string."""
    assert _escape("") == ""


@pytest.mark.ai_generated
def test_parse_dt_valid() -> None:
    """Valid ISO string is parsed to datetime."""
    dt = _parse_dt("2025-01-15T10:00:00+00:00")
    assert dt is not None
    assert dt.year == 2025
    assert dt.month == 1
    assert dt.day == 15


@pytest.mark.ai_generated
def test_parse_dt_z_suffix() -> None:
    """Trailing Z is handled correctly."""
    dt = _parse_dt("2025-01-15T10:00:00Z")
    assert dt is not None
    assert dt.tzinfo is not None


@pytest.mark.ai_generated
def test_parse_dt_none() -> None:
    """None input returns None."""
    assert _parse_dt(None) is None


@pytest.mark.ai_generated
def test_parse_dt_invalid() -> None:
    """Invalid string returns None."""
    assert _parse_dt("not-a-date") is None


@pytest.mark.ai_generated
def test_format_date_valid() -> None:
    """Valid ISO string is formatted as YYYY-MM-DD."""
    assert _format_date("2025-06-15T10:00:00Z") == "2025-06-15"


@pytest.mark.ai_generated
def test_format_date_none() -> None:
    """None input returns em-dash."""
    assert _format_date(None) == "\u2014"


@pytest.mark.ai_generated
def test_days_ago_today() -> None:
    """Date matching 'now' returns 'today'."""
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    FrozenDatetime.freeze(now)
    with patch("templates.datetime", FrozenDatetime):
        result = _days_ago("2025-06-15T10:00:00+00:00")
    FrozenDatetime.freeze(None)
    assert result == "today"


@pytest.mark.ai_generated
def test_days_ago_one_day() -> None:
    """One day ago uses singular form."""
    now = datetime(2025, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
    FrozenDatetime.freeze(now)
    with patch("templates.datetime", FrozenDatetime):
        result = _days_ago("2025-06-15T10:00:00+00:00")
    FrozenDatetime.freeze(None)
    assert result == "1 day"


@pytest.mark.ai_generated
def test_days_ago_multiple() -> None:
    """Multiple days uses plural form."""
    now = datetime(2025, 6, 20, 12, 0, 0, tzinfo=timezone.utc)
    FrozenDatetime.freeze(now)
    with patch("templates.datetime", FrozenDatetime):
        result = _days_ago("2025-06-15T10:00:00+00:00")
    FrozenDatetime.freeze(None)
    assert result == "5 days"


@pytest.mark.ai_generated
def test_days_ago_none() -> None:
    """None input returns em-dash."""
    assert _days_ago(None) == "\u2014"


# ---------------------------------------------------------------------------
# Badges — parametrized
# ---------------------------------------------------------------------------

@pytest.mark.ai_generated
@pytest.mark.parametrize(
    "verdict,expected_color",
    [
        ("likely_resolved", "#2ea043"),
        ("feature_implemented", "#2ea043"),
        ("still_open", "#da3633"),
        ("needs_investigation", "#d29922"),
        ("stale_wontfix", "#768390"),
        ("duplicate", "#768390"),
        ("unclear", "#768390"),
        ("pending", "#484f58"),
    ],
)
def test_verdict_badge_colors(verdict: str, expected_color: str) -> None:
    """Each verdict maps to the correct hex color."""
    badge = _verdict_badge(verdict)
    assert expected_color in badge
    assert "badge" in badge


@pytest.mark.ai_generated
def test_verdict_badge_label_format() -> None:
    """Underscores become spaces, title-cased."""
    badge = _verdict_badge("likely_resolved")
    assert "Likely Resolved" in badge


@pytest.mark.ai_generated
@pytest.mark.parametrize(
    "confidence,expected_color",
    [
        ("HIGH", "#2ea043"),
        ("MEDIUM", "#d29922"),
        ("LOW", "#da3633"),
        ("PENDING", "#484f58"),
    ],
)
def test_confidence_badge(confidence: str, expected_color: str) -> None:
    """Each confidence level maps to the correct hex color."""
    badge = _confidence_badge(confidence)
    assert expected_color in badge
    assert confidence in badge


@pytest.mark.ai_generated
def test_status_badge_none() -> None:
    """None status renders 'Pending'."""
    badge = _status_badge(None)
    assert "Pending" in badge
    assert "#484f58" in badge


@pytest.mark.ai_generated
@pytest.mark.parametrize(
    "status,expected_color",
    [
        ("closed", "#2ea043"),
        ("commented", "#3fb950"),
        ("skipped", "#768390"),
    ],
)
def test_status_badge_values(status: str, expected_color: str) -> None:
    """Known status values map to correct colors."""
    badge = _status_badge(status)
    assert expected_color in badge
    assert status.title() in badge


@pytest.mark.ai_generated
def test_label_badges_empty() -> None:
    """Empty labels list returns empty string."""
    assert _label_badges([]) == ""


@pytest.mark.ai_generated
def test_label_badges_multiple() -> None:
    """Multiple labels produce multiple span elements."""
    result = _label_badges(["bug", "enhancement"])
    assert result.count("label-badge") == 2
    assert "bug" in result
    assert "enhancement" in result


@pytest.mark.ai_generated
def test_label_badges_escapes_html() -> None:
    """HTML in label names is escaped."""
    result = _label_badges(["<script>xss</script>"])
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
def test_base_layout_structure() -> None:
    """Base layout includes DOCTYPE, title, nav, and CSS."""
    html = base_layout("Test Page", "<p>content</p>")
    assert "<!DOCTYPE html>" in html
    assert "<title>Test Page" in html
    assert "Issue Triage" in html
    assert '<a href="/">Dashboard</a>' in html
    assert "<style>" in html
    assert "<p>content</p>" in html


@pytest.mark.ai_generated
def test_base_layout_escapes_title() -> None:
    """HTML in title is escaped."""
    html = base_layout("<script>bad</script>", "content")
    assert "<script>bad</script>" not in html.split("<style>")[0]
    assert "&lt;script&gt;" in html


@pytest.mark.ai_generated
def test_render_flash_success() -> None:
    """Success flash has correct class."""
    html = render_flash("Done!", "success")
    assert "flash-success" in html
    assert "Done!" in html


@pytest.mark.ai_generated
def test_render_flash_error() -> None:
    """Error flash has correct class."""
    html = render_flash("Failed!", "error")
    assert "flash-error" in html
    assert "Failed!" in html


@pytest.mark.ai_generated
def test_dashboard_with_issues(sample_issues, sample_findings, sample_state) -> None:
    """Dashboard table contains issue numbers and titles."""
    html = render_dashboard(sample_issues, sample_findings, sample_state)
    assert "#101" in html
    assert "Bug: crash on startup" in html
    assert "#102" in html
    assert "Feature: dark mode" in html


@pytest.mark.ai_generated
def test_dashboard_empty() -> None:
    """Empty issues list shows empty-state message."""
    html = render_dashboard([], {}, {})
    assert "empty-state" in html
    assert "No issues match" in html


@pytest.mark.ai_generated
def test_dashboard_filter_verdict(sample_issues, sample_findings) -> None:
    """Verdict filter narrows displayed issues."""
    html = render_dashboard(
        sample_issues, sample_findings, {},
        filters={"verdict": "likely_resolved"},
    )
    assert "#101" in html
    # Issue 102 is still_open, should not match likely_resolved filter
    assert "/issue/102" not in html


@pytest.mark.ai_generated
def test_dashboard_filter_search(sample_issues, sample_findings) -> None:
    """Text search filters by title/body content."""
    html = render_dashboard(
        sample_issues, sample_findings, {},
        filters={"q": "dark mode"},
    )
    assert "#102" in html
    assert "/issue/101" not in html


@pytest.mark.ai_generated
def test_dashboard_sort_confidence(sample_issues, sample_findings) -> None:
    """Sort by confidence puts HIGH before MEDIUM."""
    html = render_dashboard(
        sample_issues, sample_findings, {},
        filters={"sort": "confidence"},
    )
    # Issue 101 is HIGH, 102 is MEDIUM — 101 should appear first
    pos_101 = html.index("#101")
    pos_102 = html.index("#102")
    assert pos_101 < pos_102


@pytest.mark.ai_generated
def test_issue_detail_untriaged(sample_issues, sample_findings) -> None:
    """Untriaged issue shows action form with buttons."""
    issue = sample_issues[1]  # issue 102, not triaged
    finding = sample_findings["issues"][1]
    html = render_issue_detail(issue, finding, {})
    assert "Proposed Comment" in html
    assert "Close with Comment" in html
    assert "Comment Only" in html
    assert "Skip" in html


@pytest.mark.ai_generated
def test_issue_detail_triaged(sample_issues, sample_findings, sample_state) -> None:
    """Triaged issue shows 'Already Triaged', no action form."""
    issue = sample_issues[0]  # issue 101, triaged
    finding = sample_findings["issues"][0]
    html = render_issue_detail(issue, finding, sample_state)
    assert "Already Triaged" in html
    assert "triage-form" not in html


@pytest.mark.ai_generated
def test_issue_detail_evidence(sample_issues, sample_findings) -> None:
    """Evidence list is rendered in the detail page."""
    issue = sample_issues[0]
    finding = sample_findings["issues"][0]
    html = render_issue_detail(issue, finding, {})
    assert "evidence-list" in html
    assert "abc123" in html
    assert "Fix crash on startup" in html


@pytest.mark.ai_generated
def test_issue_detail_body_truncation() -> None:
    """Body longer than 2000 chars shows 'truncated' indicator."""
    issue = {
        "number": 999,
        "title": "Long body",
        "body": "x" * 3000,
        "labels": [],
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "last_comment_at": None,
        "author": "test",
        "comments_count": 0,
        "url": "",
    }
    html = render_issue_detail(issue, None, {})
    assert "truncated" in html


@pytest.mark.ai_generated
def test_export_markdown(sample_findings, sample_state) -> None:
    """Export produces valid markdown with headings and verdict info."""
    md = render_export(sample_findings, sample_state)
    assert "# Issue Triage Report" in md
    assert "## #101" in md
    assert "likely_resolved" in md
    assert "## #102" in md
    assert "still_open" in md
    assert "abc123" in md
