---
name: analyze-duplicates
description: Analyze codebase or documentation for code/text duplication using jscpd. Generates a Markdown report with collapsible sections (suitable for GitHub/Gitea issues) showing duplicate clusters, statistics, and a mediation plan proposing refactoring strategies.
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
user-invocable: true
---

# Analyze Duplicates

Detect code and documentation duplication in one or more paths, produce a
Markdown report with `<details>` sections for posting as a GitHub/Gitea issue,
and propose a concrete mediation plan.

## When to Use

- User wants to find duplicated code or documentation in a project
- User asks to "check for duplicates", "find copy-paste code", "DRY audit"
- User mentions "jscpd", "duplicate detection", or "code clones"
- User runs `/analyze-duplicates`

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_LINES` | `6` | Minimum duplicate block size in lines |
| `MIN_TOKENS` | `50` | Minimum duplicate block size in tokens |
| `THRESHOLD` | `5` | Duplication percentage that flags a warning |
| `FORMATS` | (auto-detect) | Comma-separated jscpd format list (e.g., `python,markdown`) |

## Arguments

The skill accepts one or more paths to scan. If none are provided, scan the
current working directory.

Optional flags (passed as part of the argument string):
- `--formats python,markdown` — override auto-detected formats
- `--min-lines N` — override MIN_LINES
- `--min-tokens N` — override MIN_TOKENS
- `--threshold N` — override warning threshold percentage
- `--output PATH` — where to write the report (default: `.jscpd-report.md` in first scanned path)
- `--cross-project` — when multiple paths given, also run a combined scan to find cross-project duplicates
- `--no-html` — skip generating the HTML report (default: generate it)
- `--badge` — also generate an SVG badge and embed it in the report (default: off)

## Execution Steps

### Step 0: Parse Arguments

Parse the argument string. Extract paths (any arg not starting with `--`),
and optional flags. Apply defaults from Configuration for anything not specified.

If no paths provided, use the current working directory.

Create the `.tmp/` directory in the current working directory for intermediate
output. If `.tmp` is not already in `.gitignore`, add it (or warn the user).

### Step 1: Ensure jscpd is Available

Check if jscpd is available:

```bash
command -v jscpd || npx --yes jscpd@latest --version
```

If neither works, report the error and stop:
> jscpd not found. Install via `npm install -g jscpd` or ensure `npx` is available.

### Step 2: Detect Project Context

For each scan path:
1. Check if it is a git repository (`git -C PATH rev-parse --is-inside-work-tree`)
2. Detect primary languages by file extension counts (`.py` -> python, `.js/.ts` -> javascript/typescript, `.md` -> markdown, etc.)
3. If `--formats` was specified, use that instead of auto-detection
4. Note the project name from the directory basename (or git remote if available)

### Step 3: Run jscpd

For each scan path, run jscpd with JSON, HTML, and badge reporters:

```bash
npx --yes jscpd@latest \
    --min-lines MIN_LINES \
    --min-tokens MIN_TOKENS \
    --reporters "json,html" \
    --output .tmp/jscpd-PROJECTNAME \
    --ignore "**/.tox/**,**/venv*/**,**/.venv/**,**/node_modules/**,**/__pycache__/**,**/build/**,**/dist/**,**/.eggs/**,**/.git/**,**/.npm/**,**/.tmp/**" \
    PATH
```

If `--no-html` is set, omit `html` from reporters. If `--badge` is set, add `badge` to reporters.
If `--formats` is set, add `--format FORMATS`.

This produces:
- `.tmp/jscpd-PROJECTNAME/jscpd-report.json` — structured data for the markdown report
- `.tmp/jscpd-PROJECTNAME/html/index.html` — interactive HTML report with syntax highlighting
- `.tmp/jscpd-PROJECTNAME/jscpd-badge.svg` — shields.io-style badge showing duplication % (only with `--badge`)

If `--cross-project` and multiple paths: after individual scans, create a
temporary parent directory with symlinks to all paths and run one combined scan.

### Step 4: Parse Results and Generate Report

Read each `.tmp/jscpd-PROJECTNAME/jscpd-report.json` and generate the report
using the helper script:

```bash
python3 SKILL_DIR/generate-report.py \
    --threshold THRESHOLD \
    --output REPORT_PATH \
    --jscpd-version "$(npx --yes jscpd@latest --version 2>/dev/null)" \
    [--cross-project .tmp/jscpd-combined/jscpd-report.json] \
    .tmp/jscpd-PROJECT1/jscpd-report.json \
    [.tmp/jscpd-PROJECT2/jscpd-report.json ...]
```

Where `SKILL_DIR` is the directory containing this SKILL.md file. Resolve it
by searching for `generate-report.py` in `~/.claude/skills/analyze-duplicates/`.

If `--badge` was requested and a badge was generated, pass `--badge-path` with
a relative path to the SVG. Copy the badge SVG to the output directory so both
files are co-located.

### Step 5: Review and Enhance Mediation Plan

The `generate-report.py` script already produces a `## Mediation Plan` section
with heuristic classifications (trivial/easy/moderate/hard) and strategies
for each cluster. After the report is generated:

1. Read the generated report and the duplicated fragments
2. For each cluster, **verify** the heuristic recommendation makes sense in
   context — read the actual source files around the duplicated lines if needed
3. For **easy/trivial** clusters: add a concrete diff or pseudo-diff showing
   the proposed refactoring (extract function, parametrize test, etc.)
4. For **moderate/hard** clusters: enhance the description with specifics
   about what the shared abstraction should look like
5. Adjust difficulty ratings if the heuristic got it wrong (e.g., what looks
   like a simple extract may actually involve different signatures)

### Step 6: Present Results

1. Print a brief summary to the console:
   - Total duplication percentage per project
   - Number of clone clusters found
   - Whether threshold was exceeded
2. Print paths to all generated artifacts:
   - Markdown report (the primary deliverable, suitable for GitHub issues)
   - HTML report directory (interactive browser view with syntax highlighting)
   - Badge SVG path (only if `--badge` was used)
3. If duplication exceeds the threshold, note this prominently

## Report Format

The report MUST be a Markdown file using `<details><summary>` blocks so it
renders well when posted as a GitHub/Gitea issue. Structure:

```markdown
# Duplication Analysis Report

> Generated: YYYY-MM-DD | Tool: jscpd VERSION | Threshold: N%

## Summary

| Project    | Files | Lines | Clones | Duplicated Lines | Percentage |
|------------|------:|------:|-------:|-----------------:|-----------:|
| my-project |    42 | 12000 |      5 |               83 |      0.69% |

> Duplication is within the 5% threshold for all projects.

## Duplicate Clusters

| # | Lines | Difficulty        | Strategy                      | Files   |
|---|-------|-------------------|-------------------------------|---------|
| 1 | 8     | Trivial | Extract local helper function | file.py |

<details>
<summary><b>Cluster 1</b>: [Trivial] `file.py` lines 10-18
&harr; `file.py` lines 30-38 (8 lines)</summary>

**Files involved:**
- `file.py` (lines 10-18)
- `file.py` (lines 30-38)

**Duplicated fragment:**
~~~python
<the duplicated code here>
~~~

**Mediation** (Trivial): Extract local helper function

> Duplicated logic within `file.py`. Extract into a private function
> in the same module.

</details>
```

## Commit Co-Authorship

All commits created during this workflow MUST include a `Co-Authored-By` trailer.
Get the version via `claude --version`. Format:

```
Co-Authored-By: Claude Code <VERSION> / Claude <MODEL> <noreply@anthropic.com>
```
