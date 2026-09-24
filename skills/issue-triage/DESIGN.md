# `/issue-triage` — Claude Code Skill Design

## Problem

Maintainers of projects with many open GitHub issues need to efficiently determine
which issues are already addressed by recent code changes. This was demonstrated
manually on dandi-cli (192 open issues), spawning parallel Claude agents to
cross-reference git history and codebase against open issues.

No existing tool does this "reverse triage":
- [claude-github-triage](https://github.com/chhoumann/claude-github-triage) — forward-triage of new issues
- [tj/triage](https://github.com/tj/triage), [k1LoW/gh-triage](https://github.com/k1LoW/gh-triage) — notification-focused, no AI

## Architecture

**No client-server API.** The Python web server renders complete HTML pages.
Actions are regular form POSTs that execute and redirect back. Minimal JS only
where truly needed (e.g. deep-dive loading indicator).

```
/issue-triage invoked
       │
       ▼
  ┌─────────────┐     ┌──────────────┐
  │  gather.py   │────▶│ issues.json  │
  │ (gh/git-bug) │     └──────┬───────┘
  └─────────────┘             │
       │                      ▼
       │              ┌───────────────┐
       │              │ Claude agents │  (parallel Task agents)
       │              └───────┬───────┘
       │                      ▼
       │              ┌───────────────┐
       │              │ findings.json │
       │              └───────┬───────┘
       ▼                      ▼
  ┌──────────────────────────────────┐
  │  server.py (localhost:8765)      │
  │  renders HTML pages, handles     │
  │  form POSTs, calls gh/claude     │
  └──────────────────────────────────┘
```

## Pages & Routes

All routes return **fully rendered HTML**. No JSON API.

### `GET /` — Dashboard

Rendered summary page with filter controls and issue list table.

| Column | Description |
|--------|-------------|
| # | Issue number (link to GitHub) |
| Title | Issue title (link to detail page) |
| Created | Date issue was opened |
| Last Comment | Date of most recent comment |
| Age | Days since creation |
| Labels | Badge-styled labels |
| Verdict | Color-coded: resolved/open/stale/pending |
| Confidence | HIGH/MEDIUM/LOW badge |
| Status | Triaged/Pending/Skipped |

**Filters** (query params, rendered server-side):
- `?verdict=likely_resolved` — filter by verdict
- `?confidence=HIGH` — filter by confidence
- `?q=zarr` — text search in title/body
- `?sort=age` / `?sort=confidence` / `?sort=number`
- `?show=pending` / `?show=all` / `?show=triaged`

**Summary bar**: "50 issues: 12 likely resolved, 8 still open, 5 needs investigation, 25 pending"

### `GET /issue/<number>` — Issue Detail

Full page for a single issue:

```
┌─────────────────────────────────────────────────┐
│ #1234: Upload fails with large zarr datasets    │
│ Created: 2025-06-15 │ Last comment: 2025-11-20  │
│ Age: 248 days │ Labels: bug, upload              │
│ Author: username                                 │
├─────────────────────────────────────────────────┤
│ VERDICT: likely_resolved (HIGH confidence)       │
│                                                  │
│ Summary: Addressed by PR #1456 which refactored  │
│ ZarrAsset.iter_upload() for chunked uploads.     │
│                                                  │
│ Evidence:                                        │
│  • commit abc1234 (2025-09-20)                   │
│    "Fix chunked upload for large zarr datasets"  │
│  • dandi/files/zarr.py:145                       │
│    Upload logic now handles chunking             │
├─────────────────────────────────────────────────┤
│ Issue body (first 2000 chars, rendered)          │
│ ...                                              │
├─────────────────────────────────────────────────┤
│ Proposed Comment:                                │
│ ┌─────────────────────────────────────────────┐ │
│ │ [editable textarea, pre-filled]             │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ [Close with Comment] [Comment Only] [Skip]       │
│ [Deep Dive] [Open on GitHub] [← Back to List]   │
└─────────────────────────────────────────────────┘
```

### `POST /issue/<number>/close` — Close Issue

Form fields: `comment` (textarea value).
Executes: `gh issue close <number> --repo REPO --reason completed --comment "..."`
Updates `state.json`, redirects to `GET /issue/<next>` or `GET /` if none left.

### `POST /issue/<number>/comment` — Comment Only

Form fields: `comment` (textarea value).
Executes: `gh issue comment <number> --repo REPO --body "..."`
Updates `state.json`, redirects to next issue.

### `POST /issue/<number>/skip` — Skip Issue

Optional form field: `note`.
Updates `state.json` with skip record, redirects to next issue.

### `POST /issue/<number>/deep-dive` — Request Deeper Analysis

Spawns `claude --print` subprocess with codebase access.
Updates `findings.json` with new analysis.
Redirects back to `GET /issue/<number>` showing updated findings.

(This is the one route that may take 30-60 seconds. The page can show
a "Researching..." interstitial with a meta-refresh, or use minimal JS
for a loading indicator.)

### `GET /export` — Export Findings as Markdown

Renders findings as a markdown document (for pasting into GitHub discussions,
PRs, etc.). Content-type: text/markdown with download header.

## File Structure

```
~/.claude/skills/issue-triage/
├── SKILL.md              # Skill definition + Claude orchestration instructions
├── DESIGN.md             # This document
├── gather.py             # Issue fetching (gh CLI / git-bug)
├── server.py             # Python HTTP server: renders pages, handles form POSTs
├── templates.py          # HTML template functions (string formatting, no engine)
└── README.md             # User-facing docs
```

Per-repo data (in `.git/triage/`, not committed):
```
.git/triage/
├── issues.json           # Raw issues from GitHub
├── findings.json         # Analysis results with verdicts
└── state.json            # Triage decisions made by user
```

## Data Schemas

### issues.json

```json
{
  "repo": "dandi/dandi-cli",
  "fetched_at": "2026-02-18T16:30:00Z",
  "source": "gh",
  "issues": [
    {
      "number": 1234,
      "title": "Upload fails with large zarr datasets",
      "body": "When uploading...",
      "labels": [{"name": "bug"}, {"name": "upload"}],
      "state": "OPEN",
      "created_at": "2025-06-15T10:00:00Z",
      "updated_at": "2025-12-01T14:00:00Z",
      "last_comment_at": "2025-11-20T09:30:00Z",
      "author": "username",
      "comments_count": 5,
      "url": "https://github.com/dandi/dandi-cli/issues/1234"
    }
  ]
}
```

### findings.json

```json
{
  "repo": "dandi/dandi-cli",
  "analyzed_at": "2026-02-18T17:00:00Z",
  "issues": [
    {
      "number": 1234,
      "title": "Upload fails with large zarr datasets",
      "url": "https://github.com/...",
      "labels": ["bug", "upload"],
      "created_at": "2025-06-15T10:00:00Z",
      "last_comment_at": "2025-11-20T09:30:00Z",
      "verdict": "likely_resolved",
      "confidence": "HIGH",
      "summary": "Addressed by PR #1456...",
      "evidence": [
        {"type": "commit", "ref": "abc1234", "message": "Fix chunked upload", "date": "2025-09-20"}
      ],
      "proposed_comment": "This appears resolved by...",
      "proposed_action": "comment_and_close"
    }
  ]
}
```

Verdict values: `likely_resolved`, `still_open`, `stale_wontfix`, `duplicate`,
`feature_implemented`, `needs_investigation`, `unclear`, `pending`

Confidence: `HIGH` (90%+), `MEDIUM` (60-89%), `LOW` (<60%), `PENDING`

### state.json

```json
{
  "repo": "dandi/dandi-cli",
  "triaged": {
    "1234": {"action": "closed", "at": "2026-02-18T18:00:00Z", "comment_posted": true},
    "1235": {"action": "skipped", "at": "2026-02-18T18:05:00Z", "note": "needs reporter input"}
  }
}
```

## server.py Design

**Dependencies**: Python stdlib only (`http.server`, `json`, `subprocess`,
`urllib.parse`, `html`, `datetime`, `pathlib`, `argparse`, `os`, `signal`).

Uses `http.server.ThreadingHTTPServer` on `127.0.0.1`.

**Request handler** uses a closure factory:
```python
def make_handler(triage_dir: Path, repo: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self): ...   # route to page renderers
        def do_POST(self): ...  # route to action handlers
    return Handler
```

**Page rendering**: String-based templates in `templates.py`. Each page function
returns a complete HTML string. A base layout function wraps content with
`<html>`, nav bar, dark-theme CSS. No template engine — just f-strings and
`html.escape()`.

**CSS**: Inline in the base layout. Dark theme. Color-coded verdict/confidence
badges. Responsive table. Form styling.

**Action flow** (example: close):
```python
def handle_close(self, issue_number):
    body = self.read_body()
    comment = parse_qs(body)["comment"][0]
    # Write comment to temp file to avoid shell quoting issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(comment)
        tmppath = f.name
    try:
        subprocess.run(["gh", "issue", "comment", str(issue_number),
                        "--repo", self.repo, "--body-file", tmppath],
                       check=True, timeout=30)
        subprocess.run(["gh", "issue", "close", str(issue_number),
                        "--repo", self.repo, "--reason", "completed"],
                       check=True, timeout=30)
    finally:
        os.unlink(tmppath)
    mark_triaged(self.triage_dir, issue_number, "closed")
    next_num = get_next_untriaged(self.triage_dir, issue_number)
    self.redirect(f"/issue/{next_num}" if next_num else "/")
```

**Deep dive** spawns `claude --print` with structured prompt:
```python
def handle_deep_dive(self, issue_number):
    # Show interstitial page with meta-refresh
    self.send_interstitial(f"Researching issue #{issue_number}...")

    issue = load_issue(self.triage_dir, issue_number)
    prompt = build_deep_dive_prompt(issue, self.repo)

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)  # Allow nested invocation

    result = subprocess.run(
        ["claude", "--print", "-p", prompt, "--model", "sonnet"],
        capture_output=True, text=True, timeout=120,
        cwd=find_repo_root(self.triage_dir), env=env
    )
    # Parse JSON from output, update findings.json
    update_finding(self.triage_dir, issue_number, parse_claude_output(result.stdout))
    self.redirect(f"/issue/{issue_number}")
```

Note: The interstitial approach won't work with a simple redirect since the
subprocess blocks. Two options:
1. **Blocking**: The POST blocks until claude finishes (~30-60s). Browser shows
   loading. Simple but the UX shows a spinner.
2. **Background + poll**: Start subprocess in a thread, redirect to a
   `/issue/<n>/researching` page that auto-refreshes every 3s until done.

Option 2 is better UX. The `/researching` page uses `<meta http-equiv="refresh" content="3">`.

## SKILL.md Orchestration

The skill instructs Claude to:

1. **Detect repo** from `git remote get-url origin`
2. **Check prerequisites**: `gh auth status`
3. **Gather**: `python3 ~/.claude/skills/issue-triage/gather.py --repo REPO --limit N --output .git/triage/issues.json`
4. **Load state**: read `.git/triage/state.json`, count already-triaged
5. **Write initial findings**: all issues with `verdict: "pending"`
6. **Launch server in background**: `python3 ~/.claude/skills/issue-triage/server.py --triage-dir .git/triage --port 8765 &`
7. **Analyze**: Spawn parallel Task agents to batch-analyze issues against codebase/git history, writing results to `findings.json` progressively
8. **Report**: Terminal summary when done

User arguments: `--repo OWNER/REPO`, `--limit N`, `--label LABEL`, `--serve-only`, `--no-server`, `--port PORT`

## Navigation Flow

After each action (close/comment/skip), the server redirects to the **next
untriaged issue** by number. This creates a natural review flow: the user works
through issues one at a time, like an email inbox.

The dashboard (`/`) shows all issues with their current status, allowing the
user to jump to any issue or filter the list.

## MVP vs Phase 2

### MVP (implement first)
- `gather.py`: `gh` source only
- `server.py`: All routes, server-rendered pages, form POST actions
- `templates.py`: Dashboard + detail page templates with dark theme
- `SKILL.md`: Sequential analysis (Claude analyzes inline, not parallel agents)
- No deep dive, no keyboard shortcuts, no batch ops

### Phase 2
- Parallel agent analysis via Task tool
- Deep dive via `claude --print` subprocess
- Progressive loading (server starts before analysis completes)
- git-bug source support
- Markdown export
- Batch select + close/skip from dashboard
- Keyboard navigation (minimal JS)
