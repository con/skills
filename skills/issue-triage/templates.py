"""HTML template functions for issue-triage web UI.

Server-rendered pages with dark theme. No template engine — just f-strings
and html.escape().
"""

from __future__ import annotations

import html
import urllib.parse
from datetime import datetime, timezone


def _escape(text: str) -> str:
    """HTML-escape text."""
    return html.escape(str(text)) if text else ""


def _parse_dt(dt_str: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _format_date(dt_str: str | None) -> str:
    """Format datetime as YYYY-MM-DD."""
    dt = _parse_dt(dt_str)
    return dt.strftime("%Y-%m-%d") if dt else "\u2014"


def _days_ago(dt_str: str | None) -> str:
    """Compute days since a datetime."""
    dt = _parse_dt(dt_str)
    if not dt:
        return "\u2014"
    days = (datetime.now(timezone.utc) - dt).days
    if days == 0:
        return "today"
    if days == 1:
        return "1 day"
    return f"{days} days"


def _verdict_badge(verdict: str) -> str:
    """Render color-coded verdict badge."""
    colors = {
        "likely_resolved": "#2ea043",
        "feature_implemented": "#2ea043",
        "still_open": "#da3633",
        "needs_investigation": "#d29922",
        "stale_wontfix": "#768390",
        "duplicate": "#768390",
        "unclear": "#768390",
        "pending": "#484f58",
    }
    color = colors.get(verdict, "#484f58")
    label = verdict.replace("_", " ").title()
    return f'<span class="badge" style="background:{color}">{_escape(label)}</span>'


def _confidence_badge(confidence: str) -> str:
    """Render color-coded confidence badge."""
    colors = {"HIGH": "#2ea043", "MEDIUM": "#d29922", "LOW": "#da3633", "PENDING": "#484f58"}
    color = colors.get(confidence, "#484f58")
    return f'<span class="badge" style="background:{color}">{_escape(confidence)}</span>'


def _status_badge(status: str | None) -> str:
    """Render triage status badge."""
    if not status:
        return '<span class="badge" style="background:#484f58">Pending</span>'
    colors = {"closed": "#2ea043", "commented": "#3fb950", "skipped": "#768390"}
    color = colors.get(status, "#484f58")
    return f'<span class="badge" style="background:{color}">{_escape(status.title())}</span>'


def _label_badges(labels: list[str]) -> str:
    """Render issue label badges."""
    if not labels:
        return ""
    return " ".join(
        f'<span class="label-badge">{_escape(l)}</span>' for l in labels
    )


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """\
:root {
    --bg: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --link: #58a6ff;
    --accent: #1f6feb;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.5;
}
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
.container { max-width: 1200px; margin: 0 auto; padding: 16px; }
nav {
    background: var(--bg-secondary); border-bottom: 1px solid var(--border);
    padding: 12px 16px; display: flex; align-items: center; gap: 16px;
}
nav .brand { font-weight: 600; font-size: 18px; color: var(--text); }
nav a { color: var(--text-muted); font-size: 14px; }
nav a:hover { color: var(--text); }
.summary-bar {
    display: flex; gap: 16px; padding: 16px 0; flex-wrap: wrap;
    border-bottom: 1px solid var(--border); margin-bottom: 16px;
}
.summary-item { font-size: 14px; color: var(--text-muted); }
.summary-item strong { color: var(--text); font-size: 20px; display: block; }
.filters {
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; align-items: center;
}
.filters select, .filters input[type="text"] {
    background: var(--bg-tertiary); border: 1px solid var(--border);
    color: var(--text); padding: 6px 10px; border-radius: 6px; font-size: 13px;
}
.filters input[type="text"] { width: 200px; }
.filters button {
    background: var(--accent); color: white; border: none;
    padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px;
}
table { width: 100%; border-collapse: collapse; }
th {
    text-align: left; padding: 8px 12px; font-size: 12px; color: var(--text-muted);
    border-bottom: 1px solid var(--border); text-transform: uppercase; letter-spacing: 0.05em;
}
td { padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 14px; vertical-align: top; }
tr:hover { background: var(--bg-secondary); }
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 12px; font-weight: 500; color: white; white-space: nowrap;
}
.label-badge {
    display: inline-block; padding: 1px 6px; border-radius: 12px; font-size: 11px;
    border: 1px solid var(--border); color: var(--text-muted); white-space: nowrap;
}
.detail-header {
    background: var(--bg-secondary); border: 1px solid var(--border);
    border-radius: 6px; padding: 20px; margin-bottom: 16px;
}
.detail-header h1 { font-size: 22px; margin-bottom: 8px; }
.detail-meta { display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px; color: var(--text-muted); }
.verdict-box {
    background: var(--bg-secondary); border: 1px solid var(--border);
    border-radius: 6px; padding: 20px; margin-bottom: 16px;
}
.verdict-box h2 { font-size: 16px; margin-bottom: 12px; }
.evidence-list { list-style: none; padding: 0; }
.evidence-list li {
    padding: 6px 0; font-size: 13px; color: var(--text-muted);
    border-bottom: 1px solid var(--border);
}
.evidence-list li:last-child { border-bottom: none; }
.body-preview {
    background: var(--bg-secondary); border: 1px solid var(--border);
    border-radius: 6px; padding: 20px; margin-bottom: 16px;
    max-height: 400px; overflow-y: auto;
}
.body-preview h2 { font-size: 16px; margin-bottom: 12px; }
.body-preview pre {
    white-space: pre-wrap; word-break: break-word; font-size: 13px; color: var(--text-muted);
}
.action-box {
    background: var(--bg-secondary); border: 1px solid var(--border);
    border-radius: 6px; padding: 20px; margin-bottom: 16px;
}
.action-box h2 { font-size: 16px; margin-bottom: 12px; }
textarea {
    width: 100%; min-height: 120px; background: var(--bg-tertiary);
    border: 1px solid var(--border); color: var(--text); border-radius: 6px;
    padding: 12px; font-family: inherit; font-size: 13px; resize: vertical;
    margin-bottom: 12px;
}
.btn-group { display: flex; gap: 8px; flex-wrap: wrap; }
.btn {
    display: inline-block; padding: 8px 16px; border-radius: 6px;
    font-size: 14px; font-weight: 500; cursor: pointer;
    border: 1px solid var(--border); text-decoration: none;
    color: var(--text); background: var(--bg-tertiary);
}
.btn:hover { background: var(--border); text-decoration: none; }
.btn-danger { background: #da3633; border-color: #da3633; color: white; }
.btn-danger:hover { background: #b62324; }
.btn-primary { background: var(--accent); border-color: var(--accent); color: white; }
.btn-primary:hover { background: #1158c7; }
.btn-success { background: #238636; border-color: #238636; color: white; }
.btn-success:hover { background: #1a7f37; }
.flash { padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; }
.flash-success { background: #0d2818; border: 1px solid #238636; color: #3fb950; }
.flash-error { background: #2d1215; border: 1px solid #da3633; color: #f85149; }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-muted); }
.empty-state h2 { margin-bottom: 8px; color: var(--text); }
"""


# ---------------------------------------------------------------------------
# Page layouts
# ---------------------------------------------------------------------------

def base_layout(title: str, content: str, flash: str = "") -> str:
    """Wrap content with full HTML page, nav, and dark-theme CSS."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape(title)} \u2014 Issue Triage</title>
<style>{CSS}</style>
</head>
<body>
<nav>
  <span class="brand">Issue Triage</span>
  <a href="/">Dashboard</a>
  <a href="/export">Export</a>
</nav>
<div class="container">
{flash}
{content}
</div>
</body>
</html>"""


def render_flash(message: str, msg_type: str = "success") -> str:
    """Render a flash message bar."""
    return f'<div class="flash flash-{msg_type}">{_escape(message)}</div>'


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def _build_summary_bar(issues: list[dict], findings_by_num: dict, triaged: dict) -> str:
    total = len(issues)
    verdicts: dict[str, int] = {}
    for i in issues:
        v = findings_by_num.get(i["number"], {}).get("verdict", "pending")
        verdicts[v] = verdicts.get(v, 0) + 1

    parts = [f'<div class="summary-item"><strong>{total}</strong>Total Issues</div>']
    for v in [
        "likely_resolved", "feature_implemented", "still_open",
        "needs_investigation", "stale_wontfix", "pending",
    ]:
        count = verdicts.get(v, 0)
        if count:
            parts.append(
                f'<div class="summary-item"><strong>{count}</strong>'
                f'{_escape(v.replace("_", " ").title())}</div>'
            )
    parts.append(
        f'<div class="summary-item"><strong>{len(triaged)}</strong>Triaged</div>'
    )
    return '<div class="summary-bar">' + "\n".join(parts) + "</div>"


def _build_filter_form(filters: dict) -> str:
    verdict_filter = filters.get("verdict", "")
    confidence_filter = filters.get("confidence", "")
    show = filters.get("show", "all")
    sort_by = filters.get("sort", "number")
    q = filters.get("q", "")

    def _sel(name: str, val: str) -> str:
        return "selected" if filters.get(name) == val else ""

    return f"""<form class="filters" method="get" action="/">
<select name="verdict">
  <option value="">All Verdicts</option>
  <option value="likely_resolved" {_sel("verdict","likely_resolved")}>Likely Resolved</option>
  <option value="still_open" {_sel("verdict","still_open")}>Still Open</option>
  <option value="needs_investigation" {_sel("verdict","needs_investigation")}>Needs Investigation</option>
  <option value="stale_wontfix" {_sel("verdict","stale_wontfix")}>Stale / Won't Fix</option>
  <option value="pending" {_sel("verdict","pending")}>Pending</option>
</select>
<select name="confidence">
  <option value="">All Confidence</option>
  <option value="HIGH" {_sel("confidence","HIGH")}>HIGH</option>
  <option value="MEDIUM" {_sel("confidence","MEDIUM")}>MEDIUM</option>
  <option value="LOW" {_sel("confidence","LOW")}>LOW</option>
</select>
<select name="show">
  <option value="all" {_sel("show","all")}>All</option>
  <option value="pending" {_sel("show","pending")}>Untriaged</option>
  <option value="triaged" {_sel("show","triaged")}>Triaged</option>
</select>
<select name="sort">
  <option value="number" {_sel("sort","number")}>Sort by #</option>
  <option value="age" {_sel("sort","age")}>Sort by Age</option>
  <option value="confidence" {_sel("sort","confidence")}>Sort by Confidence</option>
</select>
<input type="text" name="q" value="{_escape(q)}" placeholder="Search title/body...">
<button type="submit">Filter</button>
<a href="/" class="btn" style="font-size:13px;padding:6px 10px">Reset</a>
</form>"""


def render_dashboard(
    issues: list[dict],
    findings: dict,
    state: dict,
    filters: dict | None = None,
) -> str:
    """Render the main dashboard page with summary bar, filters, and issue table."""
    filters = filters or {}

    # Lookup maps
    findings_by_num: dict[int, dict] = {}
    for f in findings.get("issues", []):
        findings_by_num[f["number"]] = f
    triaged = state.get("triaged", {})

    # ---------- Apply filters ----------
    filtered = list(issues)

    verdict_filter = filters.get("verdict", "")
    if verdict_filter:
        filtered = [
            i for i in filtered
            if findings_by_num.get(i["number"], {}).get("verdict") == verdict_filter
        ]

    confidence_filter = filters.get("confidence", "")
    if confidence_filter:
        filtered = [
            i for i in filtered
            if findings_by_num.get(i["number"], {}).get("confidence") == confidence_filter
        ]

    q = filters.get("q", "")
    if q:
        ql = q.lower()
        filtered = [
            i for i in filtered
            if ql in i.get("title", "").lower() or ql in i.get("body", "").lower()
        ]

    show = filters.get("show", "all")
    if show == "pending":
        filtered = [i for i in filtered if str(i["number"]) not in triaged]
    elif show == "triaged":
        filtered = [i for i in filtered if str(i["number"]) in triaged]

    # ---------- Sort ----------
    sort_by = filters.get("sort", "number")
    if sort_by == "age":
        filtered.sort(key=lambda i: i.get("created_at", ""))
    elif sort_by == "confidence":
        order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "PENDING": 3}
        filtered.sort(
            key=lambda i: order.get(
                findings_by_num.get(i["number"], {}).get("confidence", "PENDING"), 3
            )
        )
    else:
        filtered.sort(key=lambda i: i["number"])

    # ---------- Render ----------
    summary_html = _build_summary_bar(issues, findings_by_num, triaged)
    filter_html = _build_filter_form(filters)

    if not filtered:
        table_html = (
            '<div class="empty-state"><h2>No issues match your filters</h2>'
            '<p>Try adjusting the filters above or <a href="/">reset</a>.</p></div>'
        )
    else:
        rows: list[str] = []
        for issue in filtered:
            f = findings_by_num.get(issue["number"], {})
            verdict = f.get("verdict", "pending")
            confidence = f.get("confidence", "PENDING")
            triage_status = triaged.get(str(issue["number"]), {}).get("action")
            rows.append(f"""<tr>
<td><a href="{_escape(issue.get('url', ''))}" target="_blank">#{issue["number"]}</a></td>
<td><a href="/issue/{issue["number"]}">{_escape(issue["title"])}</a></td>
<td>{_format_date(issue.get("created_at"))}</td>
<td>{_format_date(issue.get("last_comment_at"))}</td>
<td>{_days_ago(issue.get("created_at"))}</td>
<td>{_label_badges(issue.get("labels", []))}</td>
<td>{_verdict_badge(verdict)}</td>
<td>{_confidence_badge(confidence)}</td>
<td>{_status_badge(triage_status)}</td>
</tr>""")

        table_html = f"""<table>
<thead><tr>
<th>#</th><th>Title</th><th>Created</th><th>Last Comment</th>
<th>Age</th><th>Labels</th><th>Verdict</th><th>Confidence</th><th>Status</th>
</tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>"""

    content = summary_html + filter_html + table_html
    return base_layout("Dashboard", content)


# ---------------------------------------------------------------------------
# Issue detail
# ---------------------------------------------------------------------------

def render_issue_detail(
    issue: dict,
    finding: dict | None,
    state: dict,
    flash_msg: str = "",
) -> str:
    """Render the detail page for a single issue."""
    number = issue["number"]
    finding = finding or {}
    triaged = state.get("triaged", {})
    triage_info = triaged.get(str(number))

    verdict = finding.get("verdict", "pending")
    confidence = finding.get("confidence", "PENDING")
    summary = finding.get("summary", "Analysis pending...")
    evidence = finding.get("evidence", [])
    proposed_comment = finding.get("proposed_comment", "")

    flash_html = render_flash(flash_msg) if flash_msg else ""

    # -- Header --
    header = f"""<div class="detail-header">
<h1>#{number}: {_escape(issue["title"])}</h1>
<div class="detail-meta">
  <span>Created: {_format_date(issue.get("created_at"))}</span>
  <span>Last comment: {_format_date(issue.get("last_comment_at"))}</span>
  <span>Age: {_days_ago(issue.get("created_at"))}</span>
  <span>Labels: {_label_badges(issue.get("labels", []))}</span>
  <span>Author: {_escape(issue.get("author", "unknown"))}</span>
  <span>Comments: {issue.get("comments_count", 0)}</span>
</div>
</div>"""

    # -- Verdict box --
    evidence_html = ""
    if evidence:
        items = []
        for e in evidence:
            etype = _escape(e.get("type", ""))
            ref = _escape(e.get("ref", ""))
            msg = _escape(e.get("message", ""))
            date = _escape(e.get("date", ""))
            items.append(f"<li><strong>{etype}</strong>: {ref} \u2014 {msg} ({date})</li>")
        evidence_html = f'<ul class="evidence-list">{"".join(items)}</ul>'

    verdict_box = f"""<div class="verdict-box">
<h2>Analysis</h2>
<p style="margin-bottom:12px">{_verdict_badge(verdict)} {_confidence_badge(confidence)}</p>
<p style="margin-bottom:12px;color:var(--text-muted)">{_escape(summary)}</p>
{evidence_html}
</div>"""

    # -- Body preview --
    body = issue.get("body", "") or ""
    body_preview = body[:2000]
    if len(body) > 2000:
        body_preview += "\n\n... (truncated)"
    body_box = f"""<div class="body-preview">
<h2>Issue Body</h2>
<pre>{_escape(body_preview)}</pre>
</div>"""

    # -- Action box --
    if triage_info:
        action_html = f"""<div class="action-box">
<h2>Already Triaged</h2>
<p>Action: {_status_badge(triage_info.get("action"))} at {_escape(triage_info.get("at", ""))}</p>
<div class="btn-group" style="margin-top:12px">
  <a href="{_escape(issue.get('url', ''))}" target="_blank" class="btn">Open on GitHub</a>
  <a href="/" class="btn">\u2190 Back to List</a>
</div>
</div>"""
    else:
        action_html = f"""<div class="action-box">
<h2>Proposed Comment</h2>
<form method="post" id="triage-form">
  <textarea name="comment">{_escape(proposed_comment)}</textarea>
  <div class="btn-group">
    <button type="submit" formaction="/issue/{number}/close" class="btn btn-danger">Close with Comment</button>
    <button type="submit" formaction="/issue/{number}/comment" class="btn btn-success">Comment Only</button>
    <button type="submit" formaction="/issue/{number}/skip" class="btn">Skip</button>
    <a href="{_escape(issue.get('url', ''))}" target="_blank" class="btn">Open on GitHub</a>
    <a href="/" class="btn">\u2190 Back to List</a>
  </div>
</form>
</div>"""

    content = flash_html + header + verdict_box + body_box + action_html
    return base_layout(f"#{number}: {issue['title']}", content)


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------

def render_export(findings: dict, state: dict) -> str:
    """Render findings as a downloadable markdown document."""
    repo = findings.get("repo", "")
    analyzed_at = findings.get("analyzed_at", "")
    triaged = state.get("triaged", {})

    lines = [
        f"# Issue Triage Report \u2014 {repo}",
        f"Analyzed: {analyzed_at}",
        "",
    ]

    for f in findings.get("issues", []):
        number = f["number"]
        title = f.get("title", "")
        verdict = f.get("verdict", "pending")
        confidence = f.get("confidence", "PENDING")
        summary = f.get("summary", "")
        triage_action = triaged.get(str(number), {}).get("action", "pending")

        lines.append(f"## #{number}: {title}")
        lines.append(f"**Verdict**: {verdict} ({confidence}) | **Status**: {triage_action}")
        if summary:
            lines.append(f"\n{summary}")

        evidence = f.get("evidence", [])
        if evidence:
            lines.append("")
            for e in evidence:
                lines.append(
                    f"- {e.get('type', '')}: {e.get('ref', '')} \u2014 {e.get('message', '')}"
                )
        lines.append("")

    return "\n".join(lines)
