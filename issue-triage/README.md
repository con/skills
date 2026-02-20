# /issue-triage — Claude Code Skill

Triage open GitHub issues by cross-referencing them against your codebase and
git history.  Claude analyzes each issue to determine whether it's likely
resolved, still open, stale, or needs investigation, then presents the results
in a local web UI where you can review, comment, close, or skip each issue.

## Prerequisites

- **Python 3.10+** (stdlib only — no pip install needed)
- **gh CLI** authenticated (`gh auth login`)
- **Claude Code** with skill support

## Quick Start

Inside any git repository with a GitHub remote:

```
/issue-triage
```

This will:
1. Fetch open issues via `gh issue list`
2. Analyze each against git history and codebase
3. Launch a web UI at `http://127.0.0.1:8765`

## Options

```
/issue-triage --repo dandi/dandi-cli --limit 20 --label bug
/issue-triage --serve-only          # re-serve existing data
/issue-triage --no-server           # analyze only, no web UI
/issue-triage --port 9000           # custom port
```

| Option | Default | Description |
|--------|---------|-------------|
| `--repo OWNER/REPO` | auto-detect | GitHub repository |
| `--limit N` | 50 | Maximum issues to fetch |
| `--label LABEL` | — | Filter by issue label |
| `--serve-only` | false | Skip gathering/analysis, serve existing data |
| `--no-server` | false | Analyze only, don't start web UI |
| `--port PORT` | 8765 | Web UI port |

## Web UI

The dashboard shows all issues with:
- Color-coded verdict badges (green=resolved, red=open, yellow=investigate)
- Confidence levels (HIGH/MEDIUM/LOW)
- Filters by verdict, confidence, triage status, and text search
- Sortable by issue number, age, or confidence

Click an issue to see:
- Full analysis with evidence (commits, code locations)
- Issue body preview
- Editable proposed comment
- Action buttons: Close with Comment, Comment Only, Skip

After each action, you're redirected to the next untriaged issue.

## Data Files

Stored in `.git/triage/` (not committed):

| File | Contents |
|------|----------|
| `issues.json` | Raw issues from GitHub |
| `findings.json` | Analysis results with verdicts |
| `state.json` | Your triage decisions |

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `likely_resolved` | Commits or PRs clearly address the issue |
| `feature_implemented` | The requested feature exists in the codebase |
| `still_open` | Problem not addressed by any changes |
| `needs_investigation` | Related changes exist but unclear if resolved |
| `stale_wontfix` | Very old, no activity, appears obsolete |
| `duplicate` | Another issue covers the same problem |
| `unclear` | Not enough information |

## Troubleshooting

**`gh auth status` fails**: Run `gh auth login` to authenticate.

**No issues found**: Check `--repo` is correct and has open issues.

**Server won't start**: Check if port 8765 is already in use. Use `--port`
to pick a different one.

**Stale data**: Delete `.git/triage/` and re-run to start fresh.
