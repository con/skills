---
name: scan-projects
description: Scan git repository subdirectories and create/update projects.tsv with metadata and LLM-generated summaries
---

# Scan Projects Skill

This skill scans all git repository subdirectories in the current folder and creates/updates a `projects.tsv` file with metadata about each project.

## Output Format

The `projects.tsv` file contains tab-separated columns:
- **folder**: Directory name
- **summary**: High-level description of the project
- **language**: Primary programming language
- **license**: License type
- **earliest_commit**: Date of first commit (ISO format)
- **latest_commit**: Date of most recent commit on main/master branch (ISO format)
- **url**: Remote git URL (if available)

## Execution Instructions

When this skill is invoked, execute the following steps:

### Phase 1: Scan Metadata
Run the scan script to collect basic metadata:
```bash
python3 ~/.claude/skills/scan-projects/scan.py
```

This collects: language, license, commit dates, and git URLs. Summaries are marked as "NEEDS_ANALYSIS".

### Phase 2: Generate Summaries with Claude Analysis

After the scan completes:

1. **Read projects.tsv** to find entries with "NEEDS_ANALYSIS" in the summary column
2. **Batch process** projects (suggest 10-20 at a time to avoid overwhelming context)
3. **For each project directory**, analyze it to determine its ultimate purpose/goal:
   - Read README, main documentation files
   - Look at directory structure, main code files
   - Check git remote URL for context (GitHub description, topics)
   - Examine package metadata (setup.py, pyproject.toml, package.json, etc.)
4. **Generate a concise summary** (1-2 sentences) describing:
   - What the project does (its primary purpose)
   - Target domain/audience if relevant
   - Key distinguishing features if applicable
5. **Update the TSV** with the generated summaries

### Summary Guidelines

Good summaries should:
- Be 1-2 sentences, max 150 characters
- Focus on **purpose and goal**, not implementation details
- Be specific about the domain (e.g., "neuroimaging", "web framework", "CLI tool")
- Avoid generic phrases like "This is a tool for..." - just state what it does

Examples:
- Bad: "This is a Python library"
- Bad: "A tool for data analysis"
- Good: "BIDS validator for neuroimaging datasets"
- Good: "Distributed task queue for Python web applications"
- Good: "Terminal multiplexer with session persistence"

### Batch Processing Strategy

To handle large numbers of projects efficiently:

1. **Get list of projects needing analysis:**
   ```bash
   python3 ~/.claude/skills/scan-projects/update_summary.py --list 20
   ```

2. **Process batch:**
   - For each project in the batch, analyze its content
   - Build a JSON object: `{"folder_name": "generated summary", ...}`

3. **Update TSV with batch results:**
   ```bash
   echo '{"project1": "Summary 1", "project2": "Summary 2"}' | python3 ~/.claude/skills/scan-projects/batch_update.py -
   ```

4. **Repeat** until all projects are analyzed, or ask user if they want to continue

5. **Report progress** after each batch (e.g., "Analyzed 20/1135 projects, 1115 remaining")

### Helper Scripts

- `update_summary.py --list [N]`: List N projects needing analysis
- `update_summary.py <folder> <summary>`: Update single project
- `batch_update.py -`: Batch update from JSON (stdin)
- `batch_update.py <file.json>`: Batch update from JSON file

## Implementation Details

### Getting commit dates:
```bash
# Earliest commit
git log --reverse --format=%aI --all | head -1

# Latest commit on main/master
git log -1 --format=%aI origin/HEAD 2>/dev/null || git log -1 --format=%aI main 2>/dev/null || git log -1 --format=%aI master 2>/dev/null
```

### Determining primary language:
Count file extensions (excluding common non-code files), prioritize:
- `.py` → Python
- `.js`/`.ts` → JavaScript/TypeScript
- `.java` → Java
- `.cpp`/`.c`/`.h` → C/C++
- `.rs` → Rust
- `.go` → Go
- `.rb` → Ruby
- `.jl` → Julia
- `.r`/`.R` → R
- `.m` → MATLAB/Objective-C

### Finding license:
```bash
find . -maxdepth 2 -iname "license*" -o -iname "copying*" | head -1
```
Parse first line for license type (MIT, GPL, Apache, BSD, etc.)

### Getting summary:
1. Try git remote description: `git remote get-url origin` → parse GitHub/GitLab description
2. Try README.md first line or first heading
3. Fall back to "No description"

### Getting remote URL:
```bash
git remote get-url origin 2>/dev/null || echo "N/A"
```

## Error Handling

- Skip non-git directories silently
- Report directories where git commands fail
- Handle missing LICENSE/README gracefully
- Handle repositories with no commits

## Output

Print a summary table showing:
- Total directories scanned
- New projects added
- Projects skipped (already in TSV)
- Errors encountered

Example:
```
Scanned 145 directories
- New projects: 3
- Skipped (existing): 140
- Errors: 2 (see below)

Errors:
- project-foo: git log failed (bare repository?)
- project-bar: unable to determine language

Updated projects.tsv with 143 entries
```
