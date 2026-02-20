---
name: issue-triage
description: Triage open GitHub issues by cross-referencing against codebase and git history
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, Task, AskUserQuestion
user-invocable: true
---

# Issue Triage

Cross-reference open GitHub issues against the codebase and git history to
identify issues that may already be resolved, stale, or actionable.  Results
are presented in a local web UI for review.

## Arguments

Parse the user's invocation for these optional arguments:

| Arg | Default | Description |
|-----|---------|-------------|
| `--repo OWNER/REPO` | auto-detect from `git remote` | GitHub repository |
| `--limit N` | `0` (all) | Max issues to fetch (0 = no limit) |
| `--label LABEL` | *(none)* | Filter issues by label |
| `--serve-only` | `false` | Serve existing data without re-gathering or re-analyzing |
| `--no-server` | `false` | Analyze only, don't start web UI |
| `--port PORT` | `8765` | Port for the web UI |

## Execution

### Step 1 — Prerequisites

```bash
gh auth status
```

If this fails, tell the user to run `gh auth login` first.

### Step 2 — Detect repo

```bash
git remote get-url origin
```

Parse the output to get `OWNER/REPO`.  Use `--repo` if the user provided it.

### Step 3 — Gather issues

Skip this step if `--serve-only` is set and `.git/triage/issues.json` exists.

```bash
python3 ~/.claude/skills/issue-triage/gather.py --repo OWNER/REPO --limit N --output .git/triage/issues.json
```

Add `--label LABEL` if the user specified one.

### Step 4 — Load existing state

Read `.git/triage/state.json` if it exists.  Count already-triaged issues
and report: "Found N issues, M already triaged."

### Step 5 — Initialize findings

Skip if `--serve-only` and `.git/triage/findings.json` already exists.

Read `.git/triage/issues.json`.  Write `.git/triage/findings.json` with all
issues set to `verdict: "pending"`, `confidence: "PENDING"`:

```json
{
  "repo": "OWNER/REPO",
  "head_sha": "<from issues.json>",
  "analyzed_at": "<ISO timestamp>",
  "issues": [
    {
      "number": 123,
      "title": "...",
      "url": "...",
      "labels": [...],
      "created_at": "...",
      "last_comment_at": "...",
      "verdict": "pending",
      "confidence": "PENDING",
      "summary": "",
      "evidence": [],
      "proposed_comment": "",
      "proposed_action": ""
    }
  ]
}
```

### Step 6 — Launch web UI

Skip if `--no-server` is set.

```bash
python3 ~/.claude/skills/issue-triage/server.py --triage-dir .git/triage --repo OWNER/REPO --port PORT &
```

Run this in the background.  The server binds to `0.0.0.0` so it is
accessible from outside containers.  Print the URL: `http://127.0.0.1:PORT`

**Container access (Podman/Docker):** If running inside a container, the
user needs to have published the port when starting the container, e.g.:
```bash
podman run -p 8765:8765 ...
# or: docker run -p 8765:8765 ...
```
If the port was not published at container start, inform the user that they
need to restart the container with `-p 8765:8765` (or their chosen port) to
access the web UI from the host.  Alternatively, they can use `--no-server`
and review findings via the markdown export.

### Step 7 — Duplicate detection pass

Skip if `--serve-only` is set.

Before per-issue analysis, do a lightweight duplicate detection pass over
all issues in `issues.json`:

1. **Group candidates** — for each pair of issues, compute similarity based
   on:
   - Title overlap: shared significant words (ignoring stopwords like
     "the", "a", "is", "in", "bug", "feature", "request")
   - Label overlap: shared labels (especially specific ones, not just "bug")
   - Body keyword overlap: shared distinctive terms in the first 500 chars

2. **Flag potential duplicates** — when two issues have high similarity
   (e.g. >60% title word overlap or near-identical bodies), mark the
   **newer** issue (higher number) as `duplicate` with:
   - `confidence`: `HIGH` if titles are near-identical or one explicitly
     references the other; `MEDIUM` if strong keyword/label overlap;
     `LOW` if only moderate similarity
   - `summary`: "Appears to duplicate #N (older issue)"
   - `evidence`: `[{"type": "duplicate", "ref": "#N", "message": "Similar title/body: <shared terms>", "date": ""}]`
   - `proposed_comment`: "This issue appears to duplicate #N which was
     filed earlier.  Closing in favor of the original — please follow
     #N for updates.  If this is actually a distinct problem, feel free
     to reopen with additional details."
   - `proposed_action`: "close"

3. **Write findings** — update `findings.json` for each detected duplicate.
   Only flag the newer issue; leave the older counterpart for normal
   analysis.

Issues already marked as duplicates in this pass are skipped in Step 8.

### Step 8 — Analyze issues

Skip if `--serve-only` is set.

For each issue in `issues.json` that does not already have a non-pending
verdict in `findings.json` (including those marked duplicate in Step 7):

1. **Search git history** for references to the issue number, keywords from
   the title, and related file paths:
   - `git log --oneline --all --grep="#<number>"` — commits mentioning the issue
   - `git log --oneline --all --grep="<key terms>"` — commits with related keywords
   - Search the codebase with Grep for patterns related to the issue

2. **Determine verdict** based on what you find:
   - `likely_resolved` — commits or PRs clearly address the issue
   - `feature_implemented` — the requested feature exists in the codebase
   - `still_open` — the issue describes a problem not addressed by any changes
   - `needs_investigation` — some related changes exist but unclear if resolved
   - `stale_wontfix` — issue is very old with no activity and appears obsolete
   - `duplicate` — another issue covers the same problem (also caught by Step 7)
   - `unclear` — not enough information to determine

3. **Set confidence**:
   - `HIGH` — strong evidence (direct commit references, clear code changes)
   - `MEDIUM` — circumstantial evidence (related changes, partial fixes)
   - `LOW` — weak evidence (only tangentially related changes)

4. **Write summary** — 1-2 sentences explaining the verdict.

5. **Collect evidence** — list of commits, code locations, PRs that support
   the verdict.  Each evidence item has `type`, `ref`, `message`, `date`.

6. **Draft proposed comment** — if the verdict is `likely_resolved` or
   `feature_implemented`, draft a GitHub comment explaining how the issue
   appears to be addressed (mention specific commits/PRs).  Be polite and
   ask the reporter to confirm and close if they agree.

7. **Update findings.json** — write the updated finding for this issue.
   Read the current file, update the entry, write it back.  This way the
   web UI shows results progressively.

Process issues in order.  After analyzing each issue, briefly report
progress: "Analyzed #123: likely_resolved (HIGH confidence)".

### Step 9 — Summary

After all issues are analyzed (or if `--serve-only`), print a summary:

```
Issue Triage Complete
=====================
Repository: OWNER/REPO
Total issues: 150
  Likely resolved: 12
  Duplicates: 5
  Still open: 80
  Needs investigation: 18
  Stale: 10
  Pending: 25
Already triaged: 5

Web UI: http://127.0.0.1:8765
```

If the server is running, remind the user they can review issues in the
browser.  When they're done, they can press Ctrl+C or kill the server
process.
