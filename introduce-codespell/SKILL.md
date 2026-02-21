---
name: introduce-codespell
description: Introduce codespell spell-checking to a project. Creates branch, config file, GitHub Actions workflow, pre-commit hook. Lists typos, helps identify paths/words to ignore, and fixes typos interactively. Use when setting up codespell in a new project.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# Introduce Codespell to a Project

Set up codespell spell-checking infrastructure in a project, identify typos, configure exclusions, and fix spelling errors.

## When to Use

- User wants to add spell-checking to a project
- User mentions "codespell" or wants to check for typos
- User wants to set up CI for spelling errors
- User asks to "introduce codespell" or run "/introduce-codespell"

## Prerequisites

- `codespell` must be available (can use `uvx codespell` if not installed)
- `gh` CLI for PR creation (optional)
- Git repository

## Workflow Overview

1. **Check existing**: See if codespell is already configured
2. **Setup**: Create branch and initial configuration
3. **Analyze**: List all detected typos + historical typo fix stats
4. **Configure exclusions**: Identify paths and words to ignore
5. **Fix**: Apply fixes for legitimate typos
6. **Review**: Check for functional fixes (potential bug fixes)
7. **Finalize**: Prepare PR message and create PR

## Step 0: Check for Existing Codespell Integration

Before creating anything, check if codespell is already configured:

```bash
# Check for existing config
grep -l codespell pyproject.toml setup.cfg .codespellrc .pre-commit-config.yaml 2>/dev/null
# Check for workflow
ls .github/workflows/*codespell* 2>/dev/null
```

### If codespell is already configured:

1. **Run codespell** to see if it passes:
   ```bash
   uvx codespell
   ```

2. **If clean**: Project is already well-maintained, may not need changes

3. **If not clean**: Review and tune existing config:
   - **First, tag current state** for easy comparison:
     ```bash
     git tag -f _enh-codespell-prev
     ```
     This creates a non-annotated tag (overwriting any previous one) to make it easier to review changes from prior attempts with `git diff _enh-codespell-prev..HEAD`
   - Check `skip` patterns - may need updates for new directories
   - Check `ignore-words-list` - may need additions
   - Fix any new typos that crept in
   - Proceed with fix commits using `datalad run`

4. **If partially configured** (e.g., config but no CI): Add missing pieces

### If no codespell configuration exists:

Proceed with Step 1 to set up from scratch.

## Step 1: Initial Setup

### Create Feature Branch

```bash
git checkout -b enh-codespell
```

### Gather Historical Typo Fix Stats

Check git history for prior manual typo fixes to demonstrate value:

```bash
git log --oneline --all --grep="typo" --grep="spell" --grep="spelling" | wc -l
git log --oneline --all --grep="typo" | head -10
```

This shows the project has had typo issues before, justifying the addition of automated checking.

### Determine Configuration Location

Choose based on existing project structure (in order of preference):
1. `pyproject.toml` - if exists, add `[tool.codespell]` section
2. `setup.cfg` - if exists, add `[codespell]` section
3. `.codespellrc` - fallback standalone config

### Detect Files to Skip

Scan for common file types that should be skipped:
- Binary/generated: `*.pdf`, `*.svg`, `*.ai`, `*.min.*`, `*-min.*`, `*.pack.js`
- Dependencies: `go.sum`, `package-lock.json`, `*.lock`, `*-lock.yaml`, `vendor/`
- Virtual envs: `venv/`, `.venv/`, `venvs/`, `.tox/`
- Cache directories: `.npm/`, `.cache/` (npm/uv caches - should NEVER be committed to git)
- Localization/i18n: `*/i18n/*` (use wildcards - foreign language translations)
- Build artifacts: `*/build/*` (Sphinx docs, compiled output - may be untracked)
- External/samples: `samples/`, `third_party/`, `vendor/` (external content)
- Data files: `*.niml`, `*.gii`, `*.pgm`
- CSS: `*.css` (often has vendor prefixes flagged as typos)
- Generated: `versioneer.py`

**Important**: Check for untracked local directories (like `docs/build/`) that may contain
build artifacts. These won't show in `git ls-files` but will be scanned by codespell.

### Initial Config Template

For `.codespellrc`:
```ini
[codespell]
skip = .git*,*.pdf,*.svg,*.css,*.min.*,.npm,.cache,*/i18n/*,*/build/*
check-hidden = true
# ignore-regex =
# ignore-words-list =
```

For `pyproject.toml`:
```toml
[tool.codespell]
skip = '.git*,*.pdf,*.svg,*.css,*.min.*,.npm,.cache,*/i18n/*,*/build/*'
check-hidden = true
# ignore-regex = ''
# ignore-words-list = ''
```

### Jupyter Notebook Handling

If `*.ipynb` files exist, add ignore-regex for embedded images:
```ini
ignore-regex = ^\s*"image/\S+": ".*
```

## Step 2: Create GitHub Actions Workflow

Create `.github/workflows/codespell.yml`:

```yaml
# Codespell configuration is within <CONFIG_FILE>
---
name: Codespell

on:
  push:
    branches: [<MAIN_BRANCH>]
  pull_request:
    branches: [<MAIN_BRANCH>]

permissions:
  contents: read

jobs:
  codespell:
    name: Check for spelling errors
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Codespell
        uses: codespell-project/actions-codespell@v2
```

**Note**: Problem matcher annotations are now built into `actions-codespell@v2` - no need for a separate `codespell-problem-matcher` step.

Commit: "Add github action to codespell <BRANCH> on push and PRs"

## Step 3: Commit Initial Config

```bash
git add <CONFIG_FILE>
git commit -m 'Add rudimentary codespell config'
```

## Step 4: Add Pre-commit Hook (if applicable)

If `.pre-commit-config.yaml` exists:

```yaml
- repo: https://github.com/codespell-project/codespell
  # Configuration for codespell is in <CONFIG_FILE>
  rev: v2.4.1  # Use current version
  hooks:
  - id: codespell
```

For `pyproject.toml` config, add:
```yaml
    additional_dependencies:
    - tomli; python_version<'3.11'
```

Commit: "Add pre-commit definition for codespell"

## Step 5: Analyze Typos

Run codespell to list all detected issues:

```bash
uvx codespell 2>&1 | head -200
```

### Categorize Results

Group typos into categories:

1. **Legitimate typos to fix** - actual spelling errors in code/docs
2. **False positives - paths to skip** - vendored code, generated files, data directories
3. **False positives - words to ignore** - domain-specific terms, variable names, abbreviations

### Get Sorted Hit Counts

```bash
uvx codespell 2>&1 | grep -e '==>' | sed -e 's,.*: *,,g' | sort | uniq -c | sort -n
```

This shows which "typos" appear most frequently - often these are false positives that need exclusion.

## Step 6: Configure Exclusions

### Adding Paths to Skip

Update config `skip` field with additional paths:
- Vendored code directories (e.g., `statics/`, `vendor/`, `third_party/`)
- Generated documentation
- Test fixtures with intentional misspellings
- Binary or data file directories

### Handling camelCase/PascalCase Identifiers (IMPORTANT!)

**BEFORE adding individual identifiers to `ignore-words-list`, check if you can use regex instead:**

If you detect **3 or more** camelCase or PascalCase false positives (e.g., `doubleClick`, `hasTables`, `OptIn`), use regex patterns:

#### camelCase Pattern (starts lowercase, has uppercase):
```regex
\b[a-z]+[A-Z]\w*\b
```
Matches: `doubleClick`, `hasTables`, `addRes`, `prevEnd`, `pixelX`

#### PascalCase Pattern (starts uppercase, mixed case):
```regex
\b[A-Z][a-z]+[A-Z]\w*\b
```
Matches: `OptIn`, `OptionA`

#### Combined Pattern (recommended):
```regex
\b[a-z]+[A-Z]\w*\b|\b[A-Z][a-z]+[A-Z]\w*\b
```

#### Add to Configuration with Comment:

For `.codespellrc` (INI format):
```ini
[codespell]
skip = .git*,*.svg,dist
check-hidden = true
# Ignore camelCase and PascalCase identifiers (common in code)
ignore-regex = \b[a-z]+[A-Z]\w*\b|\b[A-Z][a-z]+[A-Z]\w*\b
ignore-words-list = inout,rouge,caf
```

For `pyproject.toml`:
```toml
[tool.codespell]
skip = '.git*,*.svg,dist'
check-hidden = true
# Ignore camelCase and PascalCase identifiers (common in code)
ignore-regex = '\b[a-z]+[A-Z]\w*\b|\b[A-Z][a-z]+[A-Z]\w*\b'
ignore-words-list = 'inout,rouge,caf'
```

**Always add a descriptive comment** above `ignore-regex` explaining what's being ignored and why.

### Adding Words to ignore-words-list

Use `ignore-words-list` for case-insensitive word exclusions that DON'T fit the regex patterns above:

**What goes in ignore-words-list:**
- **Language keywords**: `inout` (Swift), `afterall` (test frameworks)
- **Domain-specific terms**: `rouge` (syntax highlighter), `statics` (directory name)
- **File extensions**: `caf` (Core Audio Format)
- **Short codes/abbreviations**: `nd` (2nd), `ot` (ANSI escape), `fo` (Windows flag)
- **Legitimate words in special contexts**: Words correct in the project's domain

**What should NOT go in ignore-words-list** (use regex instead):
- camelCase identifiers: `doubleClick`, `hasTables`, `addRes`
- PascalCase identifiers: `OptIn`, `OptionA`

Example of a clean config:
```ini
# Ignore camelCase and PascalCase identifiers (common in code)
ignore-regex = \b[a-z]+[A-Z]\w*\b|\b[A-Z][a-z]+[A-Z]\w*\b
ignore-words-list = inout,rouge,statics,caf,afterall,nd,ot,fo
```

### Using ignore-regex for Other Pattern Exclusions

For more complex cases beyond camelCase/PascalCase, use regex:
```ini
# Ignore embedded base64 images in notebooks and specific codes
ignore-regex = ^\s*"image/\S+": ".*|\\bTEH\\b|\b[a-z]+[A-Z]\w*\b
```

**Comment guidelines:**
- Place comment on the line immediately above `ignore-regex`
- Use `#` for INI/config files
- Briefly explain what patterns are being ignored
- Be specific (e.g., "Ignore camelCase identifiers" not just "Ignore patterns")

## Step 7: Fix Typos - Proper Workflow

**CRITICAL WORKFLOW**: Handle ambiguous typos manually FIRST, then use `codespell -w` for non-ambiguous ones.

**⚠️ CRITICAL REMINDER**: After applying ALL fixes, you MUST review the complete diff for false positives before proceeding to the PR step. See Step 7.6 for details.

**IMPORTANT**: If redoing fixes after a previous attempt, tag the current state first:
```bash
git tag -f _enh-codespell-prev
```
This allows easy comparison with `git diff _enh-codespell-prev..HEAD` to review what changed.

### 7.1 Preview All Proposed Fixes

First, get the full list of typos codespell would fix:

```bash
uvx codespell 2>&1
```

### 7.2 Categorize Typos

For each detected typo, determine:

1. **Non-ambiguous (single suggestion)** - e.g., `becuase ==> because`
   - Will be fixed automatically with `codespell -w` later
   - Review to ensure they're genuine typos, not domain terms

2. **Ambiguous (multiple suggestions)** - e.g., `trough ==> through, trough`
   - Requires human/LLM decision based on context
   - Must be fixed manually FIRST (before running codespell -w)

3. **False positives** - domain terms, abbreviations, intentional spellings
   - Add to `ignore-words-list` or `skip` config
   - Do NOT fix

**Cases where typos should be marked as FALSE POSITIVES:**

- **Domain-specific terms**: `pres` (pressure), `ans` (answer), `hist` (histogram)
- **Intentional spellings**: test fixtures, example data, legacy API compatibility
- **Code identifiers**: variable/function names that would break if changed
- **External references**: API endpoints, third-party constants, protocol terms
- **Abbreviations in comments**: `recv`, `addr`, `buf`, etc.
- **Foreign words**: in locale files or documentation
- **The "fix" changes meaning**: e.g., `rouge` (the tool) vs `rogue`

### 7.3 Handle Ambiguous Typos FIRST (Manual Fixes)

For typos with multiple suggestions like `trough ==> through, trough`:

1. Read the surrounding context (5-10 lines) using the Read tool
2. Understand the semantic meaning
3. Choose the correct replacement based on context
4. Use the Edit tool to apply the fix

Example ambiguous cases:
- `trough ==> through, trough` - is it "through" (preposition) or "trough" (container)?
- `loner ==> longer, loner` - is it "longer" (comparison) or "loner" (person)?
- `manger ==> manager, manger` - is it "manager" (person) or "manger" (feeding trough)?
- `seach ==> search, each, reach, ...` - context determines which is correct

**After fixing all ambiguous typos**, commit them:

```bash
git add -A
git commit -m "Fix ambiguous typos requiring context review

Fixed ambiguous typos:
- typo1 -> fix1 (file1:line) - rationale
- typo2 -> fix2 (file2:line) - rationale"
```

### 7.4 Spot Additional Typos Codespell Might Miss

While reviewing context, watch for:
- Typos not in codespell's dictionary (e.g., `anonimization` → `anonymization`)
- Context-dependent misspellings codespell can't detect
- Consistent misspellings across the codebase

If you spot typos codespell missed, fix them in the same manual commit.

### 7.4.1 Contribute Missed Typos to Codespell Dictionary

**TODO**: When you find typos that codespell missed (e.g., `sycalls` → `syscalls`,
`liklihood` → `likelihood` in hyphenated words like `log-liklihood`), consider
opening a PR to add them to the codespell dictionary at
https://github.com/codespell-project/codespell so that future users benefit.

Known typos not in codespell's dictionary:
- `sycalls` → `syscalls`

Known limitations of codespell's word splitting:
- Hyphenated words like `log-liklihood` may not be caught even though `liklihood` → `likelihood`
  is in the dictionary, because codespell may not split on hyphens consistently.

### 7.5 Verify Non-Ambiguous Typos

Before running `codespell -w`, review the remaining non-ambiguous typos to ensure:
- They are genuine typos (not domain terms that should be ignored)
- The suggested fix is correct
- Files aren't read-only or external protocols that shouldn't be modified

If any should be skipped, add them to `ignore-words-list` first.

### 7.6 CRITICAL: Review ALL Diffs for False Positives

**BEFORE committing or proceeding to PR creation**, you MUST review the complete diff for semantic false positives that codespell incorrectly "fixed". This is the most critical step to avoid breaking code!

```bash
git diff master
```

#### Common False Positive Categories to Check:

**1. Regex Patterns** (MOST CRITICAL):
- Patterns intentionally matching typos in source text (e.g., OCR errors)
- Examples:
  - `ddress` matching "Electronic Addess" in email cleanup regexes
  - `Acknowledge?ment?` matching "Acknowledgment"/"Acknowledgement"
  - DO NOT "fix" these to `address` or `meant` - they MUST remain as-is

**2. Variable Names and Abbreviations**:
- `consol` = consolidation variable (not "console")
- `countr` = country code variable (not "counter")
- `inpu` = singular of "inputs" loop variable (not "input")
- `currentY`, `currentX` = coordinate variables (not "currently")
- Check the actual usage context, not just the name!

**3. Domain-Specific Terms in Code**:
- Technical abbreviations that look like typos
- API parameter names that must remain unchanged
- Protocol-specific terminology

#### How to Fix False Positives:

**For regex patterns** - Add inline `codespell:ignore` comments:
```java
// Regex may intentionally match OCR typos in source text
email = email.replaceAll("(A|a)ddress", "");  // codespell:ignore ddress
Pattern.compile("Acknowledge?ment?");  // codespell:ignore ment
```

**For variable names** - Add to `ignore-words-list` in config:
```ini
# consol - variable abbreviation for "consolidation" (not "console")
# countr - variable for 2-character country code (not "counter")
# inpu - loop variable, singular form of "inputs"
# currenty, currentx - coordinate variables (currentY, currentX)
ignore-words-list = serie,consol,countr,inpu,currenty,currentx
```

#### Process:

1. **Review the entire diff** line by line, looking for the categories above
2. **For each suspicious change**, read the surrounding code context
3. **Revert incorrect fixes** using Edit or git revert
4. **Add protection** via inline comments or ignore-words-list
5. **Re-run codespell** to verify zero errors after protections
6. **Commit the fixes** to false positive handling

**Example of fixing a false positive:**
```bash
# Found: Acknowledge?meant? (should be Acknowledge?ment?)
git diff  # Review the change
# Edit the file to revert and add inline comment
git add <file>
git commit -m "Fix regex pattern incorrectly changed by codespell

Revert Acknowledge?meant? → Acknowledge?ment? in regex pattern.
Added inline codespell:ignore comment to protect regex pattern."
```

**This step is NON-NEGOTIABLE** - skipping it will result in broken code!

## Step 8: Verify Formatting Integrity

**CRITICAL**: After applying fixes, check that no formatting was broken.

### 8.1 Check the Diff

```bash
git diff
```

### 8.2 Look for Broken Formatting

**Markdown issues to check:**
- Table alignment - columns must still align with `|` separators
- Heading underlines - `===` or `---` must match heading length (for some parsers)
- Code fence closures - ensure ``` blocks are still properly closed
- List indentation - numbered/bulleted lists should maintain structure

**reStructuredText issues to check:**
- Table formatting - grid tables and simple tables have strict alignment
- Section underlines - `====`, `----`, `~~~~` must be at least as long as title
- Directive indentation - content under directives must be indented
- Role/reference syntax - `:role:`text`` must remain intact

### 8.3 Common Formatting Breakage Patterns

| Issue | Example | Problem |
|-------|---------|---------|
| Table column shift | Fixed word is longer/shorter | Misaligned `|` characters |
| RST underline | `Managment` → `Management` | Underline now too short |
| Markdown table | Cell content changed length | Table renders incorrectly |
| Code in docs | Variable name in backticks | Might break doc references |

### 8.4 Fix Formatting Issues

If formatting is broken:

1. Identify affected tables/headings in the diff
2. Use Edit tool to realign tables, extend underlines, etc.
3. These fixes go in a **separate fixup commit**

### 8.5 RST Underline Fix Example

If changing `Managment` to `Management` in RST:
```rst
Managment
---------
```
Must become:
```rst
Management
----------
```
(Add one more `-` to match the new length)

### 8.6 Markdown Table Realignment

If a cell content changes length, realign the entire table:
```markdown
| Column    | Description |
|-----------|-------------|
| old_word  | meaning     |
```

## Step 9: Commit Non-Ambiguous Fixes Using datalad run + codespell -w

**IMPORTANT**: For non-ambiguous typos (single suggestion), use `codespell -w` wrapped in `datalad run`.

**Note**: `datalad run` works on plain git repositories - no need to initialize as a datalad
dataset first. Do NOT run `datalad create` - it adds unnecessary commits and configuration.

### Install datalad if not available

Check if datalad is installed, and install it if needed:

```bash
# Check if datalad is available
datalad --version

# If not installed, install with uv (preferred):
uv pip install datalad

# Or install with pip if uv is not available:
pip install datalad

# Or use uvx to run without installing:
uvx --from datalad datalad --version
```

**Recommended**: Use `uvx --from datalad datalad` to run datalad commands without permanent installation.

### Commit Order Summary

By this point, you should have:
1. **Already committed** ambiguous typos (manual fixes using Edit tool) - Step 7.3
2. **Now committing** non-ambiguous typos using `codespell -w` - This step

### Commit Non-Ambiguous Typos with codespell -w

For typos with a single suggestion (e.g., `becuase ==> because`), use `codespell -w`:

```bash
# If datalad is installed:
datalad run -m "chore: fix non-ambiguous typos with codespell" 'codespell -w'

# If using uvx (no permanent installation):
uvx --from datalad datalad run -m "chore: fix non-ambiguous typos with codespell" 'uvx codespell -w'
```

**You can provide a detailed custom message** with the `-m` option listing what was fixed:

```bash
# If datalad is installed:
datalad run -m "chore: fix non-ambiguous typos with codespell

Fixed typos:
- succint -> succinct (biomni/utils.py)
- becuase -> because (biomni/utils.py)
- softwares -> software (biomni/agent/a1.py, biomni_env/README.md)
- arugments -> arguments (biomni/tool/genomics.py)
- referece -> reference (biomni/tool/genomics.py)
" 'codespell -w'

# If using uvx (no permanent installation):
uvx --from datalad datalad run -m "chore: fix non-ambiguous typos with codespell

Fixed typos:
- succint -> succinct (biomni/utils.py)
- becuase -> because (biomni/utils.py)
- softwares -> software (biomni/agent/a1.py, biomni_env/README.md)
- arugments -> arguments (biomni/tool/genomics.py)
- referece -> reference (biomni/tool/genomics.py)
" 'uvx codespell -w'
```

Note: When using `uvx --from datalad datalad`, also use `uvx codespell -w` inside the command
to ensure codespell is available in the same environment.

### Why NOT use codespell -w for ambiguous fixes?

`codespell -w` only fixes typos with a single suggestion. Ambiguous typos (multiple suggestions)
are skipped by `codespell -w`, which is why you must fix them manually first.

### Alternative: Interactive Mode (if in interactive terminal)

If you have access to an interactive terminal and want codespell to prompt for ambiguous fixes:

```bash
datalad run -m "chore: fix typos with codespell interactively" 'codespell -w -i 3 -C 4'
```

The `-i 3` flag enables interactive mode, `-C 4` shows 4 context lines.

**However**, the recommended workflow is to fix ambiguous typos manually first (Step 7.3),
then use `codespell -w` non-interactively for the remaining unambiguous typos.

### Formatting Fixup Commit (if needed)

If Step 8 required formatting corrections (table realignment, RST underlines):

```bash
git add -A
git commit -m "fixup: realign tables/headings after typo fixes"
```

Note: Formatting fixups are manual edits, so use regular git commit (not datalad run).

### Why datalad run?

- **Reproducibility**: The exact command is recorded in git commit metadata
- **Re-runnable**: Can be re-executed on different repo states with `datalad rerun`
- **Auditable**: Clear record of what tool made the changes
- **Automation-friendly**: The commit message can be customized while preserving the command

This separation makes review easier and keeps the typo fixes atomic.

## Step 10: Review for Functional Fixes

After fixing typos, review the diff to identify any that might be **functional bug fixes**
(typos in code that affected behavior but weren't caught by tests):

```bash
git diff HEAD~2..HEAD -- '*.py' '*.js' '*.ts' '*.go' '*.rs' '*.c' '*.cpp'
```

Look for typos fixed in:
- Variable/function names (could have been silently broken)
- String comparisons or dictionary keys
- Error messages that might be matched elsewhere
- Configuration keys

If any functional fixes are found:
1. Note them prominently in the PR description
2. Consider if tests should be added
3. May warrant a separate commit or mention in changelog

## Step 11: Prepare and Create Pull Request

### CRITICAL: Verify codespell passes with zero errors

Before preparing the PR, run a final check:

```bash
uvx codespell 2>&1
```

**If ANY errors appear**, go back to Step 7.6 and fix the remaining false positives!

### Prepare PR Message

Write the PR description to `.git/pr-description.md` (**NOT** `.git/prospective-PR.md`):

**IMPORTANT**: Do NOT include the PR title in the body text - it will be added automatically by `gh pr create --title`.

```markdown
Add codespell configuration and fix existing typos.

More about codespell: https://github.com/codespell-project/codespell

I personally introduced it to dozens if not hundreds of projects already and so far only positive feedback.

CI workflow has 'permissions' set only to 'read' so also should be safe.

## Changes

### Configuration & Infrastructure
- Added <CONFIG_FILE> configuration with comprehensive skip patterns
- Created GitHub Actions workflow to check spelling on push and PRs
- Pre-commit hook (if applicable)
- Configured to skip: [list skip patterns]

### Domain-Specific Whitelist
Added legitimate terms that codespell flags as typos:
- [List terms with brief explanations]

### Typo Fixes

**Ambiguous typos fixed manually** (N fixes with context review):
- [List with before → after and context]

**Non-ambiguous typos fixed automatically** (N fixes in N files):
Common fixes include: [list common patterns]

### Regex Pattern Protection
Added inline `codespell:ignore` comments for:
- [List files with regex patterns that were protected]

### Historical Context
This project has had X prior commits fixing typos manually, demonstrating the value of automated spell-checking.

## Testing

✅ Codespell passes with zero errors after all fixes

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Determine Remote and Branch Names

Identify the fork remote and upstream repository:

```bash
# List remotes to find fork (e.g., gh-<username>) and upstream (e.g., origin)
git remote -v

# Get current branch name
git branch --show-current
```

### Provide Final PR Creation Command

After verifying everything is ready, provide the user with the complete command to push and create the PR:

**Template:**
```bash
git push <fork-remote> <branch-name> && gh pr create --repo <upstream-org>/<repo-name> --title "Add codespell support with configuration and fixes" --body-file .git/pr-description.md --web
```

**Example:**
```bash
git push gh-<username> enh-codespell && gh pr create --repo grobidOrg/grobid --title "Add codespell support with configuration and fixes" --body-file .git/pr-description.md --web
```

The `--web` flag opens the PR in browser for final review before submission.

**This is the final deliverable** - always provide this exact command as the last step!

## Interactive Decision Points

When running this skill, ask the user about:

1. **Paths to skip**: After seeing typo locations, ask which directories contain vendored/generated code
2. **Words to ignore**: After seeing frequent "typos", ask which are legitimate domain terms
3. **Questionable fixes**: When LLM is unsure if a fix is appropriate, ask the user
4. **Pre-commit**: Whether to add pre-commit hook
5. **PR creation**: Whether to create PR or just prepare commits

### LLM Autonomous Decisions

The LLM should make these decisions WITHOUT asking the user:

- **Clear typos**: `managment` → `management`, `recieve` → `receive`
- **Obvious false positives**: domain terms, abbreviations, code identifiers
- **Ambiguous with clear context**: when surrounding text makes the intent obvious

### Ask User When Uncertain

- The word could legitimately be either spelling
- Changing it might break external compatibility
- It's in a string that might be user-visible (UI text)
- Multiple occurrences with different intended meanings

## Common False Positives by Domain

### Web Development
- `statics` (static files directory, not "statistics")
- `navbar`, `btn` (common abbreviations)

### Scientific Computing
- `hist` (histogram)
- `ans` (answer)
- `pres` (pressure or presentation)

### Internationalization
- Words from other languages in locale files

### Testing
- Intentional misspellings in test fixtures

## Output

After completing the skill:
- Feature branch `enh-codespell` with all changes
- Working codespell configuration
- GitHub Actions workflow for CI
- Pre-commit hook (if requested)
- All legitimate typos fixed via `datalad run` (reproducible commits)
- **All false positives reviewed and fixed** (regex patterns, variable names protected)
- Formatting intact (tables realigned, RST underlines adjusted)
- Functional fixes identified and noted
- **Codespell passes with zero errors**
- PR description saved to `.git/pr-description.md` (without duplicate title)
- **Ready-to-use command provided**: `git push <remote> <branch> && gh pr create --repo <upstream> --title "..." --body-file .git/pr-description.md --web`

## Tips

- Start with a minimal skip list and add paths as false positives are identified
- Use `ignore-words-list` sparingly - prefer fixing actual typos
- Review typos before running `codespell -w` to ensure they're genuine (not domain terms)
- Some projects may have legacy code with intentional misspellings for backwards compatibility
- **Workflow order matters**: Fix ambiguous typos manually first, then run `codespell -w` for the rest
- **⚠️ CRITICAL: Always review the complete diff for false positives** - especially regex patterns and variable names!
- **Always check formatting after fixes** - especially in RST/Markdown docs with tables
- For RST files, run `rst2html` or similar to validate after changes
- When fixing typos in headings, immediately check/fix the underline length
- Use `datalad run` with custom `-m` messages to document what typos were fixed
- If a "typo" appears many times and is domain-specific, add to ignore-words-list rather than skipping each instance
- `codespell -w` is safe for non-ambiguous typos - it only fixes single-suggestion typos
- The Edit tool is for ambiguous typos that need context-based decisions
- **Regex patterns**: Use inline `// codespell:ignore <word>` comments to protect patterns
- **Variable names**: Add to `ignore-words-list` with explanatory comments about what they represent
- **Trust but verify**: codespell is good but not perfect - human review of diffs is mandatory!
- **Contribute back**: When you find typos codespell misses (e.g., `sycalls` → `syscalls`), consider PRing them to https://github.com/codespell-project/codespell to improve the dictionary for everyone
- **Hyphenated words**: codespell may miss typos inside hyphenated compounds (e.g., `log-liklihood`) - grep for known typo patterns after `codespell -w` to catch these
