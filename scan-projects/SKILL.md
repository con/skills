---
name: scan-projects
description: Scan subdirectories and files to create/update projects.tsv with metadata and LLM-generated summaries
---

# Scan Projects Skill

Scans all entries (git repos, plain directories, and standalone files) in the current folder and creates/updates a `projects.tsv` file with metadata and summaries.

## Output Format

The `projects.tsv` file contains tab-separated columns:
- **folder**: Entry name (directory or filename)
- **type**: Entry type — `git`, `dir`, or `file`
- **summary**: High-level description
- **language**: Primary programming language (or file type for standalone files)
- **license**: License type (git repos and directories only)
- **earliest_commit**: Date of first commit (git repos only, ISO format)
- **latest_commit**: Date of most recent commit on main/master (git repos only, ISO format)
- **url**: Remote git URL (git repos only)

## Execution Instructions

### Phase 1: Scan Metadata
```bash
python3 ~/.claude/skills/scan-projects/scan.py
```

Collects metadata for all entries. Git repos get full metadata (language, license, commits, URL). Plain directories get language detection and license scanning. Files get type classification. All summaries start as "NEEDS_ANALYSIS".

### Phase 2: Generate Summaries with Claude Analysis

1. **Read projects.tsv** to find entries with "NEEDS_ANALYSIS"
2. **Batch process** entries (20+ at a time using parallel Explore agents)
3. **For each entry**, analyze to determine purpose/goal:
   - **Git repos/dirs**: Read README, main code, package metadata, directory structure
   - **Files**: Read content (if text), infer purpose from name and context
4. **Generate a concise summary** (1-2 sentences, max 150 chars):
   - Focus on **purpose and goal**, not implementation
   - Be specific about the domain
   - Avoid generic phrases — just state what it does
5. **Batch update the TSV** via inline Python or `batch_update.py`

### Summary Guidelines

- Good: "BIDS validator for neuroimaging datasets"
- Good: "CLI tool for downloading CI logs from GitHub Actions, Travis, Appveyor"
- Good: "GPG-encrypted passwords/credentials file"
- Bad: "This is a Python library"
- Bad: "A directory with some files"

### Helper Scripts

- `update_summary.py --list [N]`: List N entries needing analysis
- `update_summary.py <folder> <summary>`: Update single entry
- `batch_update.py -`: Batch update from JSON (stdin)
- `batch_update.py <file.json>`: Batch update from JSON file

## Entry Type Handling

| Type | Language detection | License | Commits | URL |
|------|-------------------|---------|---------|-----|
| `git` | File extension counting | LICENSE/COPYING parsing | Earliest + latest | `git remote get-url origin` |
| `dir` | File extension counting | LICENSE/COPYING parsing | N/A | N/A |
| `file` | Extension mapping | N/A | N/A | N/A |

## Error Handling

- Report entries where scanning fails
- Handle missing LICENSE/README gracefully
- Handle repositories with no commits
- Skip hidden directories and `.claude`
