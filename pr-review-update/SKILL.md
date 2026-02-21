---
name: pr-review-update
description: Review dashboard PRs needing your response and generate high-confidence update proposals for PRs where maintainers are waiting
---

# PR Review & Update Skill

Review PRs from the improveit-dashboard where upstream authors have requested changes (listed in "Needs Your Response"), analyze the feedback to determine if updates can be made with high confidence (≥90%), and generate clear actionable instructions for review and submission.

For codespell PRs requiring rebase, the skill will automatically attempt the rebase and clean up history to maintain a tight, clean commit structure.

## Configuration

This skill uses the following values. Adjust for your setup by editing this section:

- **DASHBOARD_DIR**: `~/proj/improveit-dashboard` — path to improveit-dashboard checkout
- **REPOS_DIR**: `~/proj/misc` — path where PR repos are cloned
- **GITHUB_USER**: `yarikoptic` — your GitHub username
- **FORK_REMOTE**: `gh-yarikoptic` — git remote name for your fork

Throughout this document, these names refer to the configured values above.

## User Arguments

The user may provide optional arguments:
- `--repo <pattern>`: Filter by repository name (e.g., `--repo duckdb`)
- `--pr <number>`: Analyze specific PR number
- `--min-confidence <0-100>`: Override default 90% confidence threshold (default: 90)
- `--limit <N>`: Limit to top N PRs by waiting time (default: 10)
- `--show-all`: Show all awaiting PRs, not just top N
- `--auto-rebase`: Automatically perform rebase for high-confidence PRs (default: true for codespell PRs)

## Prerequisites

- Dashboard data at `$DASHBOARD_DIR/data/repositories.json`
- User's README at `$DASHBOARD_DIR/READMEs/$GITHUB_USER.md`
- Repos typically cloned in `$REPOS_DIR/` with PR branch checked out
- GitHub CLI (`gh`) authenticated for fetching additional PR details if needed

## Execution Steps

### 1. Load Dashboard Data

Read the pre-collected PR data from `$DASHBOARD_DIR/data/repositories.json`.

Filter for PRs where:
- `author == "$GITHUB_USER"`
- `response_status == "awaiting_submitter"` (maintainer has responded, waiting for you)
- `status == "open"` (not merged or closed)

Apply any user-provided filters from arguments.

### 2. Prioritize PRs

Sort filtered PRs by:
1. **Primary**: Days waiting (longest first) - from `days_awaiting_submitter`
2. **Secondary**: CI status (failing > pending > passing) - address broken CI first
3. **Tertiary**: Has conflicts (conflicts=true > conflicts=false)

Extract key metadata for each PR:
- Repository full name (e.g., `readthedocs/readthedocs.org`)
- PR number and URL
- Title
- Last developer comment body (the feedback to address)
- CI status: `ci_status` field
- Conflicts: `has_conflicts` field
- Days waiting: `days_awaiting_submitter`
- Tool type: `tool` field (codespell, shellcheck, other)

### 3. Analyze Feedback for Each PR

For each prioritized PR, examine `last_developer_comment_body` to categorize the request:

**Actionable Categories:**

1. **Merge Conflicts** (`has_conflicts: true`)
   - Request: Resolve conflicts with main branch
   - Confidence: 95% (rebase is well-defined)
   - Action: `git fetch upstream && git rebase upstream/main`

2. **CI Failures** (`ci_status: "failing"`)
   - Request: Fix failing tests or checks
   - Confidence: Depends on failure type
   - Action: Read CI logs, fix issues, push update

3. **Code Review Feedback**
   - Specific file/line changes: 90-100% confidence
   - Typo fixes: 100% confidence
   - Configuration tweaks: 85-95% confidence
   - Architectural changes: <70% confidence (usually needs manual review)

4. **Questions/Clarifications**
   - Request: Answer reviewer questions
   - Confidence: 100% (just needs response, not code)
   - Action: Comment on PR with answer

5. **Approval Pending Action** (e.g., "looks good", "yes, please")
   - Request: Merge approval pending minor action (rebase, squash, etc.)
   - Confidence: 95%
   - Action: Perform requested action and notify

**Non-Actionable (Skip or Manual Review):**
- Vague feedback ("needs improvement")
- Design disagreements
- Requests for major refactoring
- Awaiting third-party decision

### 4. Repository Availability Check

For each actionable PR, check if repo exists locally:

```bash
ls -d $REPOS_DIR/<repo-name>/.git 2>/dev/null
```

Extract repo name from `repository` field (e.g., `readthedocs/readthedocs.org` → `readthedocs.org`).

**If repo exists:**
- Get current branch: `git -C $REPOS_DIR/<repo-name> branch --show-current`
- Check if it matches expected PR branch (infer from PR metadata or common pattern like `enh-codespell`)
- Verify clean working tree: `git -C $REPOS_DIR/<repo-name> status --porcelain`

**If repo missing:**
- Extract clone URL from PR data or construct from repository full_name
- Typically user's fork: `https://github.com/$GITHUB_USER/<repo-name>`
- Generate clone command

### 5. Confidence Assessment

Assign confidence score (0-100%) based on feedback analysis:

**100% Confidence:**
- Merge conflict resolution (standard rebase workflow)
- Answering questions (no code change)
- Typo fixes in specific files mentioned
- Rebase/squash requests with approval

**90-95% Confidence:**
- CI failures with clear error messages (linting, formatting)
- Configuration file updates (e.g., add ignore patterns)
- Minor code changes with specific file/line references
- Updating PR branch to target (e.g., `develop` instead of `main`)

**80-89% Confidence:**
- CI failures requiring code fixes (test failures)
- Refactoring specific functions with examples
- Documentation improvements with clear guidance

**<80% Confidence (Manual Review):**
- Architectural changes
- Performance optimization requests
- Security concerns
- Design disagreements
- Vague feedback

**Exclude from proposals (<90% unless --min-confidence lowered):**
- Anything requiring user judgment on approach
- Breaking changes
- Multi-step complex changes

### 6. Automated Rebase for Codespell PRs

For codespell PRs (tool == "codespell") that need rebasing, perform the following automated workflow to maintain clean history:

**Goal:** End with a clean codespell state, no conflicts, and tight commit history.

#### 6.1. Identify Codespell Commits

Before rebasing, identify commits in the PR branch:
```bash
cd $REPOS_DIR/<repo-name>
git log --oneline origin/<base-branch>..HEAD
```

Look for:
- **Config commit**: Adds `.codespellrc` or similar config
- **Workflow commit**: Adds/modifies `.github/workflows/` files
- **Automated typo fix commit**: Usually contains "DATALAD RUNCMD" or "codespell -w" or similar automated fix message
- **Manual/ambiguous fix commit**: Fixes to ambiguous typos or manual corrections

#### 6.2. Save Current State

Create a backup tag before any operations:
```bash
git tag backup-before-rebase-$(date +%Y%m%d-%H%M%S)
```

This allows recovery via `git reflog` and `git reset --hard backup-before-rebase-<timestamp>` if needed.

#### 6.3. Rebase Strategy: Clean Rebase Path

**Attempt 1: Direct rebase**
```bash
git fetch origin
git rebase origin/<base-branch>
```

**If rebase succeeds cleanly:**
- Proceed to 6.4 (Clean up workflow file)

**If rebase has conflicts:**

Follow this conflict resolution strategy prioritizing clean history:

1. **Abort current rebase**
   ```bash
   git rebase --abort
   ```

2. **Drop automated typo fix commit first**
   ```bash
   # Interactive rebase to drop the automated fix commit
   git rebase -i origin/<base-branch>
   # In the editor, change 'pick' to 'drop' for the automated typo fix commit
   # Keep config and workflow commits
   ```

3. **Retry rebase**
   ```bash
   git rebase origin/<base-branch>
   ```

4. **If still conflicts:**
   - Abort again: `git rebase --abort`
   - Also drop manual/ambiguous fix commit if present
   - Retry rebase with only config + workflow commits
   - **Last resort:** Start fresh by cherry-picking only config + workflow commits onto latest main

5. **If rebase succeeds after dropping commits:**
   - Proceed to 6.4 to clean up workflow file

#### 6.4. Clean Up Workflow File

After successful rebase, check if the workflow file includes the redundant `codespell-problem-matcher@v1` step and remove it if present.

**Background**: The `actions-codespell@v2` action internally includes the problem matcher functionality, so the explicit `codespell-project/codespell-problem-matcher@v1` step is redundant.

**Process:**

1. **Check if workflow file has the problem-matcher step:**
   ```bash
   cd $REPOS_DIR/<repo-name>

   # Look for the workflow file (usually .github/workflows/codespell.yml)
   workflow_file=$(find .github/workflows -name "*codespell*" -o -name "*spell*" | head -1)

   if [ -n "$workflow_file" ]; then
       if grep -q "codespell-project/codespell-problem-matcher" "$workflow_file"; then
           echo "Found redundant problem-matcher step in $workflow_file"
       else
           echo "No problem-matcher step found, skipping cleanup"
       fi
   fi
   ```

2. **Remove the problem-matcher step if found:**

   Use Edit tool to remove the entire step block:

   **BEFORE:**
   ```yaml
   steps:
     - name: Checkout
       uses: actions/checkout@v4
     - name: Annotate locations with typos
       uses: codespell-project/codespell-problem-matcher@v1
     - name: Codespell
       uses: codespell-project/actions-codespell@v2
   ```

   **AFTER:**
   ```yaml
   steps:
     - name: Checkout
       uses: actions/checkout@v4
     - name: Codespell
       uses: codespell-project/actions-codespell@v2
   ```

3. **Amend the workflow commit:**

   Find the commit that added the workflow file and amend it:

   ```bash
   # Find the commit that added or last modified the workflow
   workflow_commit=$(git log --oneline --diff-filter=A -- "$workflow_file" | head -1 | awk '{print $1}')

   # If workflow was added in this PR branch (not in base branch):
   if git log --oneline origin/<base-branch>..HEAD | grep -q "$workflow_commit"; then
       # Amend the workflow commit
       # First, stage the cleaned workflow file
       git add "$workflow_file"

       # Interactive rebase to edit the workflow commit
       git rebase -i origin/<base-branch>
       # In the editor, change 'pick' to 'edit' for the workflow commit
       # After rebase stops:
       git commit --amend --no-edit
       git rebase --continue
   else
       # Workflow already existed in base branch, just commit the cleanup
       git add "$workflow_file"
       git commit -m "Remove redundant codespell-problem-matcher step

The actions-codespell@v2 action internally includes the problem matcher,
so the explicit codespell-project/codespell-problem-matcher@v1 step is redundant.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   fi
   ```

4. **Alternative: If workflow commit is first commit in PR:**

   Simpler approach when workflow was added in this PR:

   ```bash
   # Stage the cleaned workflow file
   git add .github/workflows/codespell.yml

   # Amend the first commit (assuming it's the workflow commit)
   # Use git rebase -i to identify which commit added the workflow
   git log --oneline --reverse origin/<base-branch>..HEAD

   # If it's the first commit after base:
   git rebase -i origin/<base-branch>
   # Mark the workflow commit as 'edit', then:
   git commit --amend --no-edit
   git rebase --continue
   ```

5. **Proceed to 6.5 (Re-run codespell)**

#### 6.5. Re-run Codespell After Clean Rebase

After successful rebase, check for typos and apply fixes BEFORE reporting to user:

**Step 1: Check what ambiguous typos were already fixed in original branch**

Before rebase, the original branch may have already fixed ambiguous typos. Check the original typo fix commit:

```bash
cd $REPOS_DIR/<repo-name>

# Find the original automated typo fix commit (usually has "DATALAD RUNCMD" or "codespell" in message)
git log backup-before-rebase-<timestamp> --oneline --grep="codespell" --grep="DATALAD RUNCMD" | head -5

# Extract what ambiguous typos were fixed manually before the automated commit
# Look for commits that fixed specific typos before the bulk automated fix
git show <original-typo-fix-commit-hash> | grep -E "^[-+]" | grep -v "^[-+][-+][-+]" | head -100
```

**Identify ambiguous typo fixes from original commit:**
- Lines with multiple similar words changed (e.g., `trough` → `through`)
- Context-dependent fixes that codespell -w wouldn't auto-fix
- Save these for reference when fixing ambiguous typos after rebase

**Step 2: Run codespell to identify all typos:**

```bash
cd $REPOS_DIR/<repo-name>
uvx codespell . 2>&1 | tee codespell-output.txt
```

**Analyze output:**
- Non-ambiguous typos: Lines with `==>` and single suggestion (codespell -w will fix these)
- Ambiguous typos: Lines with `==>` and multiple suggestions (need manual/AI review)
- Count: `grep -c "^.*:" codespell-output.txt`

**Step 3: Extract ambiguous typos for AI review:**

```bash
# Get ambiguous typos (multiple suggestions)
grep "," codespell-output.txt > ambiguous-typos.txt

# Get non-ambiguous typos (single suggestion)
grep -v "," codespell-output.txt | grep "==>" > simple-typos.txt
```

#### 6.5b. Fix Ambiguous Typos First (AI-Assisted)

**CRITICAL**: Fix ambiguous typos BEFORE running `codespell -w` for non-ambiguous ones.

For each ambiguous typo from `ambiguous-typos.txt`:

1. **Read the file and context** around the typo (5-10 lines):
   ```bash
   # Example: ./path/file.cpp:123: trough ==> through, trough
   ```

2. **Analyze context to determine correct fix:**

   **Common ambiguous patterns and how to resolve:**

   - `trough ==> through, trough`
     - "through" = passing from one side to another, via, by means of
     - "trough" = container, low point in a wave
     - Read context: is it about passing through something or a physical container?

   - `manger ==> manager, manger`
     - "manager" = person who manages
     - "manger" = feeding trough for animals
     - Usually "manager" in code/business contexts

   - `loner ==> longer, loner`
     - "longer" = comparative of long
     - "loner" = person who prefers to be alone
     - Check if comparing lengths or describing behavior

   - `ot ==> to, of, or, not, it`
     - Usually ANSI escape codes or abbreviations in comments
     - Check: is it a flag like `-ot`, a comment like `ot her`, or code?

   - `te ==> the, be, we, to`
     - Often template parameter names (`TE`, `template<typename TE>`)
     - Check if it's code identifier vs. misspelled article

   - `fo ==> of, for, to, do, go`
     - Often flags like `-fo` or variable names
     - Check context: is it reversed typing or intentional abbreviation?

3. **Decision logic:**

   **Fix if:**
   - Context clearly indicates correct spelling (e.g., "passing trough the data" → "through")
   - It's in a comment or documentation (not code identifiers)
   - The fix doesn't change meaning or break code
   - Previous commit in original branch fixed the same typo the same way

   **Skip (add to ignore-words-list) if:**
   - It's a code identifier (variable, function, class name)
   - It's a template parameter (TE, TT, etc.)
   - It's a domain-specific term intentionally spelled that way
   - It's in a third-party library or vendored code
   - Multiple occurrences with different intended meanings
   - Changing it would break external API compatibility

4. **Apply fixes using Edit tool:**
   ```bash
   # For each ambiguous typo determined to need fixing:
   # Use Edit tool to change the specific occurrence
   ```

5. **Track decisions:**
   Create a list of:
   - Fixed: "file:line: old → new (reason)"
   - Skipped: "file:line: word (reason - add to ignore-words-list)"

6. **Update .codespellrc with skipped words:**

   If multiple ambiguous typos are legitimate (not errors), add to config:
   ```bash
   # Edit .codespellrc or pyproject.toml
   # Add to ignore-words-list: te,ot,fo (if they're template params or flags)
   # Add to ignore-regex if it's a pattern (e.g., camelCase identifiers)
   ```

7. **Commit ambiguous fixes separately (if substantial):**

   ```bash
   git add -u
   git commit -m "Fix ambiguous typos requiring context review

Fixed based on context analysis:
- file1:line: trough → through (passing through data)
- file2:line: manger → manager (person managing resources)

Skipped (added to ignore-words-list):
- TE: template parameter name (throughout codebase)
- ot: ANSI escape code flag
"
   ```

   Or combine with the datalad run commit if changes are minor.

#### 6.6. Regenerate Non-Ambiguous Typo Fixes Using datalad run

Apply non-ambiguous typo fixes using `datalad run` for reproducibility, then REVIEW BEFORE reporting to user:

**IMPORTANT**: Use `datalad run` to wrap `codespell -w` for auditable, reproducible commits.

**Note**: `datalad run` works on plain git repositories - no need to initialize as datalad dataset.

**CRITICAL POST-FIX REVIEW**: After codespell -w runs, review fixes in context to catch false positives.

1. **Check if datalad is available:**
   ```bash
   datalad --version 2>/dev/null || echo "Need to use uvx"
   ```

2. **Apply automated fixes using datalad run:**

   **Option A: If datalad is installed:**
   ```bash
   cd $REPOS_DIR/<repo-name>
   datalad run -m "Fix typos found by codespell

Automated fixes applied by codespell -w after rebase onto main.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>" 'codespell -w'
   ```

   **Option B: If datalad not installed (use uvx):**
   ```bash
   cd $REPOS_DIR/<repo-name>
   uvx --from datalad datalad run -m "Fix typos found by codespell

Automated fixes applied by codespell -w after rebase onto main.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>" 'uvx codespell -w'
   ```

   **Option C: Interactive mode (if ambiguous typos remain):**
   ```bash
   # Prompts for each ambiguous typo with context
   datalad run -m "Fix typos interactively with codespell" 'codespell -w -i 3 -C 4'
   # Or with uvx:
   uvx --from datalad datalad run -m "Fix typos interactively with codespell" 'uvx codespell -w -i 3 -C 4'
   ```
   The `-i 3` flag enables interactive mode, `-C 4` shows 4 context lines.

   **Option D: If using extracted patch (when codespell unavailable):**
   ```bash
   # Apply patch first, then commit normally (not with datalad run)
   git add -u
   git commit -m "Fix typos found by codespell

Typo fixes extracted from original commit and re-applied after rebase.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

3. **Why use datalad run?**
   - **Reproducibility**: Command is recorded in git commit metadata
   - **Re-runnable**: Can re-execute with `datalad rerun`
   - **Auditable**: Clear record of what tool made changes
   - **Standard practice**: Follows introduce-codespell skill workflow

4. **Review changes after commit:**
   ```bash
   git show HEAD --stat
   git log --oneline -1
   ```

5. **Handle ambiguous typos if needed** (manual review before datalad run)
   - If `codespell -w` skipped ambiguous typos, fix them manually first
   - Review ambiguous cases using Read tool to understand context
   - Use Edit tool to apply correct fixes
   - Commit manually, then run datalad run for remaining typos
   - Or use interactive mode: `codespell -w -i 3`

#### 6.7. CRITICAL: Review Fixes Made by codespell -w

**After running datalad run with codespell -w, ALWAYS review the changes in context.**

Codespell can make incorrect "fixes" that break code or change meaning:

**Common False Positive Patterns:**

1. **API/Function naming patterns** - suffix letters that look like typos:
   - `allocatedp` → `allocated` (WRONG: "p" suffix for pointer variant)
   - `deallocatedp` → `deallocated` (WRONG: same pattern)
   - `widthIn` → `within` (WRONG: parameter name)
   - `readByte` → `readable` (WRONG: method name)

2. **Variable naming conventions:**
   - `errorOccured` → `errorOccurred` (might be OK, but check usage)
   - `hasHappend` → `hasHappened` (might be OK, but check consistency)

3. **Test data or intentional misspellings:**
   - Test cases that verify error handling
   - Sample data with intentional typos

**Review Process:**

1. **Check the diff of the datalad run commit:**
   ```bash
   git show HEAD --stat
   git show HEAD -- path/to/changed/file.c
   ```

2. **For each changed file, verify:**
   - Is this in vendored/third-party code? → Should skip entire directory
   - Is this a naming pattern (suffix/prefix)? → Add to ignore-words-list
   - Does changing it break the code? → Revert and add to ignore-words-list
   - Is it used consistently throughout codebase? → Search for other uses

3. **Search for related patterns:**
   ```bash
   # If you find "allocatedp" was wrongly "fixed", search for similar patterns:
   git grep -i "allocatedp\|deallocatedp\|somethingp"

   # Check if the pattern is used elsewhere:
   git diff HEAD -- . | grep "^-.*allocatedp"
   ```

4. **Revert incorrect fixes and update config:**

   **Option A: Revert specific lines and add to ignore-words-list**
   ```bash
   # Undo the commit
   git reset --soft HEAD~1

   # Revert specific bad changes
   git checkout HEAD -- path/to/file/with/bad/fix.c

   # Or manually fix using Edit tool

   # Update .codespellrc
   # Add: ignore-words-list = ...,allocatedp,deallocatedp

   # Recommit with datalad run
   datalad run -m "Fix typos with codespell" 'codespell -w'
   ```

   **Option B: Use inline pragma for specific lines**

   When a word is only wrong in specific contexts (correct elsewhere), use inline pragma:

   ```c
   // Before:
   {NAME("allocatedp"), CTL(thread_allocatedp)},

   // After adding pragma:
   {NAME("allocatedp"), CTL(thread_allocatedp)},  // codespell:ignore
   ```

   **IMPORTANT**: Use `// codespell:ignore` without specifying the word.
   - ✅ Correct: `// codespell:ignore`
   - ❌ Wrong: `// codespell:ignore allocatedp` (codespell 2.4.1+ doesn't parse word-specific pragmas)

   This tells codespell to ignore all words on that line.

5. **Common scenarios requiring revert + config update:**

   - **Naming patterns in APIs:** `allocatedp`, `pread`, `pwrite`
   - **Protocol/spec keywords:** Intentional spellings from external specs
   - **Legacy compatibility:** Old API names that can't change
   - **Foreign language words:** Especially in test data or i18n

6. **Update .codespellrc after finding false positives:**
   ```bash
   # Add to ignore-words-list (case-insensitive):
   ignore-words-list = ans,inout,allocatedp,deallocatedp

   # Or add to skip paths if entire directory is problematic:
   skip = .git*,./extension/vendored_lib/*
   ```

7. **Recommit after fixing:**
   ```bash
   git add .codespellrc
   git add -u  # Stage reverted files
   datalad run -m "Fix typos with codespell (excluding false positives)" 'codespell -w'
   ```

**Signs of False Positives to Watch For:**

- Changes in vendored/third-party code (jemalloc, tpch, tpcds, etc.)
- Changes to identifiers that match across multiple files consistently
- Changes that affect struct field names, function names, enum values
- Changes in test data or fixture files
- Changes that add/remove characters from what looks like abbreviations

**When in Doubt:**
- Search codebase for the term before/after the change
- Check if it's used in multiple places with same spelling
- Look at surrounding code patterns (e.g., `allocated` and `allocatedp` both exist)
- If pattern is intentional, add to ignore-words-list rather than fixing

#### 6.7b. Analyze Identifier Changes (Don't Blindly Revert)

**IMPORTANT**: Not all identifier changes are false positives. Some identifiers DO contain typos that should be fixed.

Codespell can change identifiers (function names, variables, struct fields). These require **analysis** to determine:
1. Is this fixing an actual typo in the identifier? → Keep the fix
2. Is this changing a correct identifier that looks like a typo? → Revert
3. Is this part of a public API/interface? → Extra caution
4. Would fixing it conflict with existing code? → Check for name collisions

**Detection: Find identifier changes in the diff**

```bash
cd $REPOS_DIR/<repo-name>

# Find changes to function/method names (with parentheses)
git show HEAD | grep -E "^[-+].*\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(" | head -30

# Find changes to struct/object field access (. or ->)
git show HEAD | grep -E "^[-+].*(\.|->)[a-z][a-zA-Z0-9_]*" | head -30

# Find changes to variable declarations
git show HEAD | grep -E "^[-+].*\b(auto|const|static|int|bool|string)\s+(&|\*)?\s*[a-z][a-zA-Z0-9_]*\s*(=|;)" | head -30
```

**Analysis Process for Each Identifier Change:**

1. **Read the context** (at least 10 lines before/after):
   ```bash
   git show HEAD -- path/to/file.cpp | grep -B10 -A10 "changed_identifier"
   ```

2. **Ask: Is the original spelling actually wrong?**

   - ✅ **YES, it's a typo** → Keep the fix:
     - `IsAvailble` → `IsAvailable` (missing 'a')
     - `varaible` → `variable` (transposed letters)
     - `funciton` → `function` (typo in name)

   - ❌ **NO, it's intentional** → Revert:
     - `HasTable` → `hashtable` (valid method name, not a typo)
     - `larg` → `large` (convention: larg/rarg = left/right argument)
     - `pres` → `press` (abbreviation for "present" or "result")
     - `allocatedp` → `allocated` (API naming: 'p' suffix for pointer variant)

3. **Check if it's part of an interface/API:**
   ```bash
   # Is this a public method/function?
   git grep -n "class.*HasTable\|DUCKDB_API.*HasTable"

   # Is this declared in a header file?
   git show HEAD -- "*.h" "*.hpp" | grep "HasTable"

   # If yes → Reverting is safer unless certain it's a typo
   ```

4. **Check for consistent usage across codebase:**
   ```bash
   # How many times does the old spelling appear?
   git grep -c "HasTable" | grep -v ":0$"

   # If used >5 times with same spelling → likely intentional, not a typo
   # If used only 1-2 times → might be an actual typo worth fixing
   ```

5. **Check for paired patterns (strong signal of intentionality):**
   ```bash
   # Example: larg/rarg pairing
   git show HEAD | grep -E "larg|rarg"

   # If you see both larg and rarg → this is an intentional pairing pattern
   # Changing only larg to "large" breaks the symmetry → revert
   ```

6. **Check for name collisions after fix:**
   ```bash
   # Would the new name conflict with existing identifier?
   git grep -n "hashtable" | head -20

   # If "hashtable" already exists as a different entity → collision risk
   ```

7. **SPECIAL CASE: Intentional typos in tests:**
   ```bash
   # Check if change is in test files
   git show HEAD --stat | grep "test/"

   # Read the test context
   git show HEAD -- test/api/test_pending_query.cpp | grep -B5 -A5 "changed_word"
   ```

   **Tests may have intentional typos to verify error handling:**
   - Testing error messages that include the typo
   - Testing that system detects/reports the typo
   - Testing compatibility with legacy misspelled identifiers

   **If typo is intentional in test:**
   ```cpp
   // BEFORE codespell:
   test_error_message("errorOccured");  // Tests error handling

   // AFTER codespell (WRONG):
   test_error_message("errorOccurred");  // Now test breaks!

   // CORRECT FIX: Add inline pragma and revert
   test_error_message("errorOccured");  // codespell:ignore
   ```

   Use inline pragma `// codespell:ignore` for intentional typos in tests.

**Decision Matrix:**

| Original | Changed To | Used >5× | Paired Pattern | Part of API | In Test | Decision |
|----------|-----------|----------|----------------|-------------|---------|----------|
| `HasTable` | `hashtable` | Yes | No | Yes (method) | No | **REVERT** - Valid method name |
| `larg` | `large` | Yes | Yes (with rarg) | Yes (struct field) | No | **REVERT** - Intentional pairing |
| `pres` | `press` | Yes | No | No (local var) | No | **REVERT** - Valid abbreviation |
| `errorOccured` | `errorOccurred` | No | No | No | Yes (test string) | **REVERT + PRAGMA** - Intentional test typo |
| `IsAvailble` | `IsAvailable` | No | No | Yes (method) | No | **KEEP** - Actual typo in method |
| `varaible` | `variable` | No | No | No | No | **KEEP** - Actual typo in variable |

**Action on False Positives (Intentional Identifiers):**

```bash
# Option A: Revert specific changes using Edit tool
# Read the file, then Edit to restore original identifier

# Option B: Reset and exclude from next run
git reset --soft HEAD~1

# For common abbreviations used throughout codebase (>10 occurrences):
# Add to .codespellrc ignore-words-list
# Example: larg,rarg,pres
echo "ignore-words-list = ans,inout,larg,rarg,pres" >> .codespellrc

# For intentional typos in tests (error testing):
# Revert and add inline pragma on that specific line
# Example in test file:
test_error("errorOccured");  // codespell:ignore

# For unique identifiers (like HasTable method name):
# Just revert in the code, don't add to global ignore list
# (Too specific to warrant global exclusion)

# Re-run datalad run after corrections
git add .codespellrc test/  # If added pragmas
datalad run -m "Fix typos with codespell (reverted false positives)" 'codespell -w'
```

**Action on Actual Identifier Typos:**

```bash
# If the identifier really contains a typo (like IsAvailble):
# 1. Keep the codespell fix
# 2. Check if it's part of public API - may need deprecation path
# 3. Search for all uses and ensure they're all updated
git grep -n "IsAvailable" | head -50

# 4. Check if tests need updating
git grep -n "IsAvailable" -- "test/*" "tests/*"
```

**Key Principle:**

> **Analyze first, then decide.** Don't blindly revert all identifier changes or blindly accept them all.
> The goal is correctness: fix actual typos (even in identifiers), but preserve intentional naming.

#### 6.7b-ii. Special Case: Paired Function Parameters

Function parameters often use single-letter prefixes for parallel data structures. This is especially common in:
- **Merge functions**: `a[]`/`b[]` arrays with `acount`/`bcount`, `aidx`/`bidx`
- **Comparison functions**: parallel indices, pointers, values
- **Parallel processing**: `aptr`/`bptr`, `aval`/`bval`, `asize`/`bsize`

**Common Paired Patterns:**
- `[a-z]count` / `[a-z]count` - array counts (a/b/c prefix)
- `[a-z]idx` / `[a-z]idx` - array indices
- `[a-z]ptr` / `[a-z]ptr` - pointers
- `[a-z]val` / `[a-z]val` - values
- `[a-z]size` / `[a-z]size` - sizes
- `[a-z]arg` / `[a-z]arg` - arguments (e.g., larg/rarg)

**Why This Matters:**

Codespell may "fix" one side of a pair but not the other, creating **asymmetric naming** that breaks the intentional pattern:

```cpp
// BEFORE (correct pairing):
void MergeLoop(row_t a[], row_t b[], idx_t acount, idx_t bcount) {
    idx_t aidx = 0, bidx = 0;
    while (aidx < acount && bidx < bcount) {
        // merge logic
    }
}

// AFTER codespell (WRONG - breaks pairing):
void MergeLoop(row_t a[], row_t b[], idx_t account, idx_t bcount) {
    idx_t aidx = 0, bidx = 0;
    while (aidx < account && bidx < bcount) {  // ASYMMETRIC!
        // merge logic
    }
}
```

The asymmetry (`account` vs `bcount`) is the key signal of a false positive.

**Detection Strategy:**

```bash
cd $REPOS_DIR/<repo-name>

# Step 1: Check for changes to variables with single-letter prefixes
git show HEAD | grep -E "^[-+].*\b[a-z](count|idx|ptr|val|size|arg)\b" | head -30

# Step 2: If found, check for pairing in the modified file
# Extract the file path from git show output
file_path=$(git show HEAD --name-only | grep "\.cpp\|\.hpp\|\.c\|\.h" | head -1)

# Read the modified section to check for paired variables
git show HEAD -- "$file_path" | grep -E "\b[a-z](count|idx|ptr|val|size|arg)\b" | head -30

# Look for patterns like:
# - acount and bcount
# - aidx and bidx
# - larg and rarg (already covered in Step 6.7b)
```

**Detection: Asymmetric Changes (One Side Changed, Other Unchanged)**

This is the most reliable signal of a false positive in paired variables:

```bash
# Check if codespell created asymmetric paired variables
git show HEAD | grep -E "^\+.*\b(account|aindex|apointer)" | while read -r line; do
    # Extract the changed identifier
    changed=$(echo "$line" | grep -oE "\b(account|aindex|apointer|avalue|asize)\b" | head -1)

    # Check if there's a corresponding b* variable in the same file
    if git show HEAD | grep -qE "\bbcount\b|\bbidx\b|\bbptr\b|\bbval\b|\bbsize\b"; then
        echo "⚠️  ASYMMETRIC CHANGE DETECTED: $changed exists with paired b* variable"
        echo "   This is likely a false positive - check the context"
    fi
done
```

**Warning Signs:**

1. Function with parameters `a[]` and `b[]` (parallel arrays)
2. Variables like `acount`, `aidx` alongside `bcount`, `bidx`
3. Merge/comparison logic (while loops comparing indices)
4. **Only ONE side changed** (asymmetric change)

**Decision Logic:**

| Changed | Paired With | Pattern | Decision |
|---------|-------------|---------|----------|
| `acount` → `account` | `bcount` exists | Parallel arrays | **REVERT** - Intentional pairing |
| `aidx` → `index` | `bidx` exists | Parallel indices | **REVERT** - Intentional pairing |
| `aptr` → `after` | `bptr` exists | Parallel pointers | **REVERT** - Intentional pairing |
| `larg` → `large` | `rarg` exists | Struct fields | **REVERT** - Intentional pairing (see 6.7b) |
| `errcount` → `errorcount` | No pair | Single variable | **KEEP** - Actual typo fix (if appropriate) |
| `acount` → `account` | No `bcount` found | Single variable | **ANALYZE** - May be legitimate fix |

**Action on Paired Variable False Positives:**

```bash
# Option 1: Add to .codespellrc ignore-words-list
# (Best for patterns used throughout codebase)
echo "ignore-words-list = ...,acount" >> .codespellrc

# Option 2: Revert the specific change
# Read the file and use Edit tool to restore the paired naming

# Then re-run codespell
git add .codespellrc
datalad run -m "Fix typos with codespell (excluded paired patterns)" 'codespell -w'
```

**Example False Positive Analysis:**

```bash
# Found: acount → account in src/storage/table/update_segment.cpp
cd $REPOS_DIR/duckdb

# Check context
git show HEAD -- src/storage/table/update_segment.cpp | grep -B10 -A10 "account"

# Output shows:
# static idx_t MergeLoop(row_t a[], sel_t b[], idx_t account, idx_t bcount, ...) {
#     idx_t aidx = 0, bidx = 0;
#     while (aidx < account && bidx < bcount) {
#         ...
#     }
# }

# Analysis:
# ✅ Found paired pattern: account/bcount (should be acount/bcount)
# ✅ Found paired indices: aidx/bidx
# ✅ Parallel arrays: a[] and b[]
# ✅ Asymmetric change: only acount changed, bcount unchanged
#
# Conclusion: FALSE POSITIVE - Revert and add acount to ignore list
```

**Validation After Fix:**

After reverting paired variable false positives and adding to ignore list:

```bash
# Verify the pattern is now symmetric
git diff HEAD -- src/storage/table/update_segment.cpp | grep -E "acount|bcount"

# Should show both acount and bcount with symmetric naming

# Verify codespell is happy
codespell
# Exit code should be 0
```

**Key Insight:**

> **Asymmetric changes in paired variables are almost always false positives.**
>
> If codespell changes `acount` → `account` but leaves `bcount` unchanged,
> this breaks an intentional naming pattern and should be reverted.

The heuristic: **Look for lone changes in paired contexts.**

#### 6.7c. Detect Test Data False Positives (Duplicate String Literals)

**CRITICAL**: Codespell can create duplicate test data by "fixing" intentional variations in test strings.

Test files often use intentionally similar strings to test comparison, sorting, or prefix handling:
- `"hello"` vs `"hellow"` - testing suffix differences
- `"torororororo"` vs `"torororororp"` - testing character-by-character comparison

When codespell "fixes" these, it creates **duplicate test data** that breaks the test.

**Detection: Find duplicate string literals created by codespell**

```bash
cd $REPOS_DIR/<repo-name>

# Check if codespell created any duplicate string literals in test files
git show HEAD --stat | grep "test.*\.\(cpp\|py\|jl\)$" > /tmp/test-files-changed.txt

# For each changed test file, check for duplicate string constants
while read -r line; do
    file=$(echo "$line" | awk '{print $1}')
    if [ -f "$file" ]; then
        echo "=== Checking $file for duplicate strings ==="
        # Extract string literals and find duplicates
        git show HEAD -- "$file" | grep -E '^\+.*"[^"]{3,}"' | \
            sed 's/.*"\([^"]*\)".*/\1/' | sort | uniq -c | \
            awk '$1 > 1 {print "  DUPLICATE: \"" $2 "\" appears " $1 " times"}'
    fi
done < /tmp/test-files-changed.txt
```

**Specific Check for test_art_keys.cpp Pattern:**

```bash
# Check if a test file has arrays with duplicate values after codespell
git show HEAD -- test/sql/index/test_art_keys.cpp | \
    grep -A 20 "keys.push_back.*CreateARTKey" | \
    grep '^\+.*".*"' | sed 's/.*"\([^"]*\)".*/\1/' | sort | uniq -c | \
    awk '$1 > 1'

# If duplicates found like:
#   2 hello
# This indicates codespell likely changed "hellow" → "hello"
```

**Analysis Process for Test Data:**

1. **Check if string appears in both old and new versions:**
   ```bash
   # Did we have both "hello" and "hellow" before?
   git show HEAD^:test/sql/index/test_art_keys.cpp | grep -o '"hello\w*"' | sort | uniq

   # If output shows: "hello" and "hellow" → these were distinct test values
   # If now both are "hello" → false positive
   ```

2. **Look for patterns indicating intentional variation:**
   - Strings differing by one character: `"hello"` vs `"hellow"`
   - Strings with repeated patterns: `"torororororo"` vs `"torororororp"`
   - Sequences with incremental changes: `"abc"`, `"abcd"`, `"abcde"`

3. **Check test purpose:**
   ```bash
   # Read test name and comments
   git show HEAD:test/sql/index/test_art_keys.cpp | grep -B5 "hellow" | head -20

   # If test is about key comparison, sorting, prefix matching → variations are intentional
   ```

**Action on Test Data False Positives:**

```bash
# Option A: Revert and add inline pragma
git show HEAD^:test/sql/index/test_art_keys.cpp > /tmp/original.cpp
cp /tmp/original.cpp test/sql/index/test_art_keys.cpp

# Add inline pragma to prevent future codespell changes
# In the test file, add:  // codespell:ignore
keys.push_back(ARTKey::CreateARTKey<const char *>(arena_allocator, "hellow"));  // codespell:ignore

git add test/sql/index/test_art_keys.cpp

# Option B: Add to .codespellrc if it's a common test pattern
# (Only if the pattern appears in multiple test files)
echo "# hellow: intentional test data variation" >> .codespellrc
echo "ignore-words-list = ...,hellow" >> .codespellrc
```

**Decision Matrix for Test Strings:**

| Context | Pattern | Duplicate After Fix? | Decision |
|---------|---------|----------------------|----------|
| Test array with "hello", "hellow" | Suffix variation | Yes - both "hello" now | **REVERT + PRAGMA** |
| Test array with "torororororo", "torororororp" | Char difference | No - left as is | **KEEP** |
| Error message string with typo | Prose/message | No duplicates | **KEEP** (if testing error text) or **FIX** (if not) |
| Test expecting "SELCT" to fail | SQL syntax error | N/A - has pragma | **REVERT + PRAGMA** |

**Warning Signs of Test Data False Positives:**

1. ✋ **Duplicate strings in test arrays** after codespell
2. ✋ **Test file changes near `push_back`, `append`, `add`** with string literals
3. ✋ **Strings that differ by 1-2 characters** in original (prefix/suffix testing)
4. ✋ **Test names containing "comparison", "sort", "prefix", "key"**

**Key Principle:**

> **Test data variations are often intentional.** If codespell creates duplicates in test arrays, it's likely wrong.
> Always check if the "typo" was actually testing something specific (error handling, comparison, etc.).

#### 6.8. Verify Clean State

Before reporting to user, verify:

1. **No codespell errors**
   ```bash
   codespell .
   echo "Exit code: $?"  # Should be 0 or show only acceptable warnings
   ```

2. **No merge conflicts**
   ```bash
   git status  # Should show "nothing to commit, working tree clean"
   ```

3. **Clean history**
   ```bash
   git log --oneline origin/<base-branch>..HEAD
   ```
   Should show: Config → Workflow → Typo fixes (regenerated, if any)

#### 6.9. Report Status - DO NOT PUSH

**CRITICAL: NEVER push automatically without explicit user confirmation.**

After completing rebase and typo fixes:

1. **Report current state:**
   ```bash
   echo "=== Branch Status ==="
   git log --oneline origin/<base-branch>..HEAD
   git status
   ```

2. **Verify codespell clean state:**
   ```bash
   codespell . || echo "Codespell check complete"
   ```

3. **Provide push command for user to execute:**
   ```bash
   # DO NOT EXECUTE - provide this command to user:
   echo "Ready to push. User should run:"
   echo "cd $REPOS_DIR/<repo-name>"
   echo "git push --force-with-lease <remote-name> <branch-name>"
   ```

**For user's fork:**
- Remote is typically `$FORK_REMOTE` or `origin` (check `git remote -v`)
- Branch name from PR metadata (e.g., `enh-codespell`)
- User must review and approve before pushing

### 7. Generate Actionable Proposals

For PRs meeting confidence threshold (≥90%), generate detailed action plans with this structure:

## High-Confidence Updates (≥90%)

For each PR:

### <N>. <repo-owner/repo-name> #<PR-number> (<days> days waiting) [⚠️ CONFLICTS] [⚠️ CI FAILING]
**Title:** <PR title>
**Confidence:** <score>%
**Repo Location:** $REPOS_DIR/<repo-name> [or NEEDS SETUP if missing]
**Branch:** <branch-name>

#### Maintainer Feedback
> <quoted feedback from last_developer_comment_body>

#### Required Actions
1. **<Action 1>** (<reason>)
   ```bash
   # Exact commands to run
   ```

2. **<Action 2>**
   - Details and guidance
   - File locations if relevant

#### Pre-flight Checks
- [ ] Repo exists at `$REPOS_DIR/<repo-name>`
- [ ] On correct branch
- [ ] Working tree is clean
- [ ] Upstream remote configured (if needed)

---

### 8. Repository Setup Instructions

For PRs where repos don't exist locally, provide a dedicated section:

## Repository Setup Needed

Before working on these PRs, clone and configure the following repos:

### <repo-owner/repo-name>
```bash
cd $REPOS_DIR
git clone https://github.com/$GITHUB_USER/<repo-name>
cd <repo-name>
git remote add upstream https://github.com/<owner>/<repo-name>
git fetch --all
# Find PR branch
gh pr view <PR-number> --repo <owner/repo-name> --json headRefName
git checkout <branch-name>
```

### 9. Manual Review Required

For PRs below confidence threshold, provide:

## Needs Manual Review (<90% confidence or complex)

### <repo-owner/repo-name> #<PR-number> (<days> days waiting) [flags]
**Title:** <PR title>
**Confidence:** <score>% (<reason for low confidence>)
**Issue:** <brief description of complexity>

#### Maintainer Feedback
> <quoted feedback>

#### Why Manual Review
- <Reason 1>
- <Reason 2>

#### Recommended Action
1. <Concrete next step>
2. <Alternative approach if applicable>

### 10. Summary Report

Generate executive summary at the top of output:

## Summary

**Total PRs Awaiting Your Response:** <total count from data>
**Analyzed:** <N> (top priority by wait time or as filtered)
**High-Confidence Updates:** <count> (≥90%)
**Manual Review Required:** <count> (<90%)
**Repository Setup Needed:** <count>

### Priority Actions (by impact)
1. **<Category>** (<count> PRs) - <Why priority>
2. **<Category>** (<count> PRs) - <Why priority>

### Next Steps
1. Review high-confidence proposals above
2. Set up missing repositories (section 7)
3. Work through PRs in priority order
4. For manual review items, assess individually

### PR Status Table

**CRITICAL: Always generate a status table at the end of the report.**

After preparing PRs, generate a comprehensive status table showing:
- Repository name and PR number (with URL)
- Local path to the repository
- Push status (checking if local is ahead of remote)
- Notes about the PR state

**Table Format:**

```markdown
## 🆕 Newly Prepared PRs (This Batch)

| Repository | PR | Local Path | Push Status | Notes |
|------------|----|-----------| ------------|-------|
| <owner/repo> | [#<num>](<url>) | `<path>` | 🔄 **READY TO PUSH** | <details> |

## 📦 Previously Prepared PRs (If Any)

| Repository | PR | Local Path | Push Status | Notes |
|------------|----|-----------| ------------|-------|
| <owner/repo> | [#<num>](<url>) | `<path>` | ✅ **PUSHED** / 🔄 **READY TO PUSH** | <details> |

## 🚀 Push Commands

```bash
# NEW: <repo-name>
cd <path>
git push --force-with-lease <remote> <branch>
```
```

**Push Status Detection:**

For each prepared PR, check push status by comparing local and remote hashes:

```bash
cd $REPOS_DIR/<repo-name>
git fetch <remote> <branch> 2>/dev/null

local_hash=$(git rev-parse <branch> 2>/dev/null)
remote_hash=$(git rev-parse <remote>/<branch> 2>/dev/null)

if [ "$local_hash" = "$remote_hash" ]; then
    echo "✅ **PUSHED** - Already synced"
else
    echo "🔄 **READY TO PUSH** - Local ahead of remote"
fi
```

**Status Icons:**
- ✅ **PUSHED** - Local and remote are in sync (already pushed)
- 🔄 **READY TO PUSH** - Local is ahead of remote (needs push)
- ❌ **NOT FOUND** - Repository doesn't exist locally

**Remote Name:**
- Default remote for user's fork: `$FORK_REMOTE`
- Fallback: `origin`
- Check with: `git remote -v`

**Example Output:**

```markdown
## 🆕 Newly Prepared PRs (This Batch)

| Repository | PR | Local Path | Push Status | Notes |
|------------|----|-----------| ------------|-------|
| duckdb/duckdb | [#19817](https://github.com/duckdb/duckdb/pull/19817) | `$REPOS_DIR/duckdb` | 🔄 **READY TO PUSH** | Rebased, fixed typos |
| foo/bar | [#123](https://github.com/foo/bar/pull/123) | `$REPOS_DIR/bar` | 🔄 **READY TO PUSH** | Removed problem-matcher |

## 📦 Previously Prepared PRs (Awaiting Push)

| Repository | PR | Local Path | Push Status | Notes |
|------------|----|-----------| ------------|-------|
| old/repo | [#456](https://github.com/old/repo/pull/456) | `$REPOS_DIR/repo` | ✅ **PUSHED** | Already synced |

## 🚀 Push Commands

```bash
# NEW: duckdb
cd $REPOS_DIR/duckdb
git push --force-with-lease $FORK_REMOTE enh-codespell

# NEW: bar
cd $REPOS_DIR/bar
git push --force-with-lease $FORK_REMOTE enh-codespell
```
```

**Benefits of Status Table:**
1. **At-a-glance status** - User immediately sees what's ready vs already pushed
2. **Prevents duplicate pushes** - Clear indication of what's already synced
3. **Copy-paste commands** - Ready-to-use push commands for unpushed PRs
4. **Tracking across sessions** - Shows PRs from previous sessions still awaiting push
5. **Full context** - URLs, paths, and notes in one place

## Operating Principles

### Data-Driven
- **Trust dashboard data**: Use existing `repositories.json` as source of truth
- **Leverage metadata**: CI status, conflicts, waiting days already calculated
- **No redundant API calls**: Only fetch additional data if explicitly needed
- **Respect rate limits**: Minimize GitHub API usage

### Focus on "Needs Your Response"
- **Primary target**: PRs with `response_status == "awaiting_submitter"`
- **Prioritize by wait time**: Address longest-waiting PRs first
- **CI failures first**: Broken CI blocks merge, fix it
- **Conflicts block merge**: Rebase PRs with conflicts

### Conservative Confidence
- **Default ≥90%**: Only propose changes you're highly confident about
- **Transparent scoring**: Explain why confidence is high or low
- **User override**: Allow `--min-confidence` to adjust threshold
- **Manual review escape**: Always provide option for user judgment

### Actionable Output
- **Concrete commands**: Every proposal includes exact bash commands
- **Pre-flight checks**: Verify repo exists, branch is correct, etc.
- **Copy-paste ready**: Commands should work without modification
- **Grouped by action type**: Conflicts, CI, questions, etc.

### Efficiency
- **Top N by default**: Don't overwhelm with all PRs at once (default: 10)
- **Progressive disclosure**: Summary → high-confidence → manual review → setup
- **Batch similar actions**: Group all rebases, all CI fixes, etc.
- **Repo reuse**: If repo is already set up, skip setup steps

## Error Handling

- **Missing dashboard data**: If `repositories.json` not found, exit with clear error
- **No awaiting PRs**: If none found, report success and suggest checking other statuses
- **Repo not found**: Generate setup instructions, don't fail
- **Ambiguous feedback**: Mark as manual review rather than guessing
- **GitHub CLI not auth**: Provide `gh auth login` instruction if needed for extra data
