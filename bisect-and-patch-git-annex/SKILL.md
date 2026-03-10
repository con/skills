---
name: bisect-and-patch-git-annex
description: Bisect git-annex regressions using tinuous CI logs, create reproducers, generate fix patches, and submit Red/Green PRs to datalad/git-annex. Use when investigating test failures in git-annex CI, creating reproducer scripts, or preparing upstream bug reports.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, AskUserQuestion, Agent
user-invocable: true
---

# Bisect and Patch git-annex Regressions

End-to-end workflow for identifying git-annex regressions from tinuous CI logs,
bisecting them, creating reproducers, generating fix patches, and submitting
Red/Green PRs that demonstrate both the failure and the fix.

## When to Use

- User mentions a git-annex test regression or CI failure
- User asks to investigate a git-annex bug from CI logs
- User wants to create a reproducer for a git-annex issue
- User wants to bisect a git-annex regression
- User asks to prepare a patch PR for datalad/git-annex
- User asks to file an upstream report for a git-annex bug

## Prerequisites

### Directories

- **CI logs repo**: `/home/yoh/proj/datalad/ci/git-annex` (tinuous collection of git-annex CI builds)
- **git-annex source**: `/home/yoh/proj/git-annex` (upstream source for building/bisecting)

### Tools

- `gh` CLI authenticated (via `GH_TOKEN` env var for bot account `yarikoptic-test`)
- Fork `yarikoptic-test/git-annex` exists on GitHub
- Stack or Cabal for building git-annex from source (check `stack.yaml` in source repo)
- `datalad` for managing the CI logs dataset

### Verify prerequisites

```bash
# Check gh auth
gh auth status

# Check git-annex source exists
ls /home/yoh/proj/git-annex/stack.yaml

# Check CI logs repo
ls /home/yoh/proj/datalad/ci/git-annex/builds/

# Check build tool
stack --version
```

## Workflow Overview

1. **Update tinuous logs** - Get latest CI build results
2. **Identify the regression** - Compare passing vs failing builds
3. **Create reproducer script** - Minimal self-contained bug trigger
4. **Test reproducer locally** - Confirm it catches the bug
5. **Bisect** (optional) - Find the exact commit that introduced the regression
6. **File GitHub issue** - On `datalad/git-annex` with full details
7. **Document the bisection** - Write up findings in `docs/ai_bits/bisections/`
8. **Generate fix patch** - Develop and export the fix
9. **Test the patch** - Verify the fix resolves the issue
10. **PR with Red/Green phases** - Demonstrate failure then fix
11. **Prepare upstream report** - Draft bug report for git-annex maintainers

## Step 0: Update Tinuous Logs

Ensure the CI logs dataset is current:

```bash
cd /home/yoh/proj/datalad/ci/git-annex
datalad update

# Get recent build logs (current month)
datalad get builds/$(date +%Y)/$(date +%m)/
```

If investigating older regressions, also get the relevant month:

```bash
datalad get builds/YYYY/MM/
```

## Step 1: Identify the Regression

### Browse build results

The tinuous collection organizes logs under `builds/YYYY/MM/DD/`. Each build
directory contains test output files with pass/fail status.

```bash
# List recent builds
ls /home/yoh/proj/datalad/ci/git-annex/builds/$(date +%Y)/$(date +%m)/

# Search for a specific failing test across recent builds
grep -r "FAIL.*test_name" builds/$(date +%Y)/$(date +%m)/
```

### Compare passing vs failing runs

Find the boundary between passing and failing:

```bash
# Look for the test in recent successful builds
grep -rl "PASS.*test_name" builds/$(date +%Y)/ | sort
# Look for the test in recent failed builds
grep -rl "FAIL.*test_name" builds/$(date +%Y)/ | sort
```

### Narrow the commit range

Once you know the date range, identify the git-annex commits involved:

```bash
cd /home/yoh/proj/git-annex
git log --oneline --since="YYYY-MM-DD" --until="YYYY-MM-DD" -- relevant/path/
```

## Step 2: Create Reproducer Script

Write a minimal bash script that reproduces the bug. The script must:

- Be **self-contained** (creates temp dirs, cleans up on exit)
- Exit **0** on success (bug NOT present, test passes)
- Exit **1** on failure (bug IS present, test fails)
- This convention makes it directly usable with `git bisect run`

### Template

```bash
#!/bin/bash
# Reproducer for git-annex issue #{N}: {description}
# Co-Authored-By: Claude Code <VERSION> / Claude <MODEL> <noreply@anthropic.com>

set -eu

# Create isolated working directory
TMPDIR=$(mktemp -d "${TMPDIR:-/tmp}/ga-repro-XXXXXXX")
trap 'rm -rf "$TMPDIR"' EXIT
cd "$TMPDIR"

# Set up PATH to use the git-annex under test
# (when used with bisect, the built binary is already in PATH;
#  for standalone testing, caller should set PATH appropriately)

# --- Reproducer logic ---
# Set up test repositories, perform operations that trigger the bug,
# and assert expected behavior.
# Example:
git init repo
cd repo
git annex init
# ... operations that trigger the regression ...

# --- Assertion ---
# Exit 0 if behavior is correct (bug not present)
# Exit 1 if behavior is wrong (bug present)
if [ "$actual" = "$expected" ]; then
    echo "PASS: behavior is correct"
    exit 0
else
    echo "FAIL: expected '$expected' but got '$actual'"
    exit 1
fi
```

### Save location

Save the reproducer as:

```
/home/yoh/proj/datalad/ci/git-annex/docs/ai_bits/bisections/issue-{N}-{slug}-reproducer.sh
```

Where `{N}` is the GitHub issue number and `{slug}` is a short kebab-case description.

Make it executable:

```bash
chmod +x docs/ai_bits/bisections/issue-{N}-{slug}-reproducer.sh
```

## Step 3: Test Reproducer Locally

### Build git-annex from source

```bash
cd /home/yoh/proj/git-annex
make BUILDER=stack git-annex
```

If the build fails, try:

```bash
stack clean
make BUILDER=stack git-annex
```

### Run the reproducer

```bash
# Test against the current (presumably broken) version
PATH=/home/yoh/proj/git-annex:$PATH /path/to/reproducer.sh
# Expected: exit 1 (bug is present)
```

### Run git-annex's own tests

If the regression is in a specific test suite:

```bash
cd /home/yoh/proj/git-annex
./git-annex test --pattern 'relevant-test-name'
```

## Step 4: Bisect (Optional)

Only needed if the suspect commit is not already known from CI log analysis.

### Manual bisect

```bash
cd /home/yoh/proj/git-annex
git bisect start
git bisect bad <known-bad-commit>
git bisect good <known-good-commit>
```

### Automated bisect with reproducer

Create a bisect wrapper script that builds git-annex and runs the reproducer:

```bash
#!/bin/bash
set -eu

cd /home/yoh/proj/git-annex

# Build (exit 125 to skip if build fails)
make BUILDER=stack git-annex || exit 125

# Run reproducer with the freshly built binary
PATH="$(pwd):$PATH" /path/to/reproducer.sh
```

Then:

```bash
git bisect run /path/to/bisect-wrapper.sh
```

**Note:** Exit code 125 tells `git bisect` to skip the commit (e.g., if it
does not build). This is important for automated bisection.

## Step 5: File GitHub Issue

### Check for duplicates first

```bash
gh issue list --repo datalad/git-annex --search "keyword describing the regression"
```

### Create the issue

Include in the issue:

- **Title**: Clear, concise description of the regression
- **Body**:
  - What regressed (which test/behavior)
  - Suspected commit (from bisection or CI log analysis)
  - Reproducer script (inline or link)
  - CI log links (links to specific build logs in the tinuous collection)
  - git-annex version range (last known good, first known bad)

Append the co-authorship signature at the end of the issue body (see
[AI Attribution](#ai-attribution)).

```bash
gh issue create --repo datalad/git-annex \
  --title "Regression: ..." \
  --body-file .git/issue-body.md
```

The resulting issue number `{N}` becomes the prefix for all artifacts.

## Step 6: Document the Bisection

Create documentation at:

```
/home/yoh/proj/datalad/ci/git-annex/docs/ai_bits/bisections/issue-{N}-{slug}.md
```

### Content template

```markdown
# Issue {N}: {title}

## Summary

Brief description of the regression.

## Timeline

- **Last known good**: {commit-hash} ({date}) - version X.Y
- **First known bad**: {commit-hash} ({date}) - version X.Y
- **Bisection result**: {commit-hash} `commit message`

## Root Cause

Explanation of what the offending commit changed and why it breaks things.

## Reproducer

See [`issue-{N}-{slug}-reproducer.sh`](issue-{N}-{slug}-reproducer.sh)

## Fix

See patch: `patches/{date}-issue-{N}-{commit}-{slug}.patch`

## Links

- GitHub issue: https://github.com/datalad/git-annex/issues/{N}
- PR: https://github.com/datalad/git-annex/pull/{M}
- Upstream report: (if filed)

---
Co-Authored-By: [Claude Code](https://claude.com/claude-code) <VERSION> / Claude <MODEL> <noreply@anthropic.com>
```

## Step 7: Generate Fix Patch

### Develop the fix

Work in the git-annex source tree:

```bash
cd /home/yoh/proj/git-annex
# Make changes to fix the regression
```

### Export as patch

```bash
cd /home/yoh/proj/git-annex
git diff > /home/yoh/proj/datalad/ci/git-annex/patches/{date}-issue-{N}-{commit-hash}-{slug}.patch
```

Naming convention for the patch file:

```
patches/{YYYYMMDD}-issue-{N}-{short-commit}-{slug}.patch
```

Where:
- `{YYYYMMDD}` is today's date
- `{N}` is the GitHub issue number
- `{short-commit}` is the abbreviated hash of the commit being patched
- `{slug}` is a short kebab-case description

The `patches/` directory is in the CI repo. CI workflows apply all `patches/*.patch`
files during the git-annex build step.

## Step 8: Test the Patch Locally

```bash
cd /home/yoh/proj/git-annex

# Apply the patch (if not already applied from development)
git apply /path/to/patch-file.patch

# Rebuild
make BUILDER=stack git-annex

# Run reproducer - should now PASS (exit 0)
PATH="$(pwd):$PATH" /path/to/reproducer.sh

# Run the relevant git-annex test suite
./git-annex test --pattern 'relevant-test-name'
```

## Step 9: PR with Red/Green Phases

A single PR to `datalad/git-annex` with two sequential pushes that demonstrate
both the failure and the fix.

### Branch setup

```bash
cd /home/yoh/proj/datalad/ci/git-annex
git checkout -b issue-{N}-{slug} master
```

### Push 1 (Red phase)

Add the documentation, reproducer, and a **dummy patch** (empty or comment-only)
so CI builds git-annex WITHOUT the real fix:

```bash
# Add docs and reproducer
git add docs/ai_bits/bisections/issue-{N}-{slug}.md
git add docs/ai_bits/bisections/issue-{N}-{slug}-reproducer.sh

# Create a dummy patch file (placeholder so CI sees the file)
echo "# Placeholder - real fix in next push" > patches/{date}-issue-{N}-{commit}-{slug}.patch
git add patches/{date}-issue-{N}-{commit}-{slug}.patch

git commit -m "Add reproducer and docs for issue {N}: {description}

Dummy patch included; CI should show the test failure (Red phase).

Co-Authored-By: Claude Code <VERSION> / Claude <MODEL> <noreply@anthropic.com>"
```

Push and create PR:

```bash
export GH_TOKEN=<bot-token-for-yarikoptic-test>
git push yarikoptic-test issue-{N}-{slug}

# Write PR body
cat > .git/PR_BODY.md << 'PREOF'
## Summary

- Reproducer for issue #{N}: {description}
- Bisection docs with root cause analysis
- Fix patch for {suspected-commit}

## Red/Green Strategy

- **Push 1 (Red)**: Reproducer + dummy patch. CI builds git-annex without fix. Tests fail, confirming the reproducer catches the regression.
- **Push 2 (Green)**: Real fix patch replaces dummy. CI rebuilds with fix. Tests pass, confirming the patch resolves the issue.

## Artifacts

- `docs/ai_bits/bisections/issue-{N}-{slug}.md` - Bisection documentation
- `docs/ai_bits/bisections/issue-{N}-{slug}-reproducer.sh` - Reproducer script
- `patches/{date}-issue-{N}-{commit}-{slug}.patch` - Fix patch

## Links

- Issue: #{N}

Co-Authored-By: [Claude Code](https://claude.com/claude-code) <VERSION> / Claude <MODEL> <noreply@anthropic.com>
PREOF

gh pr create --repo datalad/git-annex \
  --head yarikoptic-test:issue-{N}-{slug} \
  --base master \
  --title "Fix regression: {description} (issue #{N})" \
  --body-file .git/PR_BODY.md
```

Wait for CI to run and confirm the Red (failure) result.

### Push 2 (Green phase)

Replace the dummy patch with the real fix:

```bash
cp /path/to/real-fix.patch patches/{date}-issue-{N}-{commit}-{slug}.patch
git add patches/{date}-issue-{N}-{commit}-{slug}.patch
git commit -m "Replace dummy patch with real fix for issue {N}

CI should now pass (Green phase).

Co-Authored-By: Claude Code <VERSION> / Claude <MODEL> <noreply@anthropic.com>"

git push yarikoptic-test issue-{N}-{slug}
```

Wait for CI to run and confirm the Green (success) result.

## Step 10: Prepare Upstream Report

Draft a human-curated bug report for git-annex upstream (branchable / git-annex
bug tracker). This is for the user to review and submit manually.

### Guidelines

- **Include**: suspected commit, CI log output excerpts, links to GH issue/PR
- **Do NOT include**: AI-generated code, scripts, or troubleshooting steps
- Only provide **pointers** -- the upstream maintainer will investigate themselves
- Keep it factual and concise

### Save draft

```bash
cat > .git/upstream-report.md << 'EOF'
## {Title}

### What happened

{Brief description of the regression}

### Suspected commit

{commit-hash} `commit message`

### How to reproduce

{Brief natural-language description, NOT the script itself}

### CI evidence

- Passing build (version X.Y): {link}
- Failing build (version X.Y): {link}

### GitHub tracking

- Issue: https://github.com/datalad/git-annex/issues/{N}
- PR with fix: https://github.com/datalad/git-annex/pull/{M}

---
Co-Authored-By: [Claude Code](https://claude.com/claude-code) <VERSION> / Claude <MODEL> <noreply@anthropic.com>
EOF
```

Present the draft to the user for review before any upstream submission.

## Interactive Decision Points

Ask the user about:

1. **Which regression to investigate** - if not specified or if multiple candidates exist
2. **Whether the reproducer adequately captures the bug** - show the script and ask for confirmation
3. **Whether to proceed with PR creation** - confirm before pushing to fork and creating the PR
4. **Review of upstream report** - always present the draft before the user posts it upstream

## AI Attribution

**All AI-produced content MUST include a co-authorship signature.** Get the
Claude Code version via `claude --version` and use the format:

```
Co-Authored-By: Claude Code <VERSION> / Claude <MODEL> <noreply@anthropic.com>
```

Example:
```
Co-Authored-By: Claude Code 2.1.63 / Claude Opus 4.6 <noreply@anthropic.com>
```

Where to include:
- **Git commit messages**: as a trailer line
- **GitHub issue bodies** (`.git/issue-body.md`): at the end, on its own line
- **PR bodies** (`.git/PR_BODY.md`): at the end; in markdown use
  `Co-Authored-By: [Claude Code](https://claude.com/claude-code) <VERSION> / Claude <MODEL> <noreply@anthropic.com>`
- **Bisection docs** (`docs/ai_bits/bisections/issue-{N}-*.md`): at the end, hyperlinked form (same as PR bodies)
- **Reproducer scripts** (`.sh`): as a `#` comment in the header block (plain text, no hyperlink)
- **Upstream report drafts** (`.git/upstream-report.md`): at the end, hyperlinked form

## Autonomous Decisions

The LLM should decide WITHOUT asking:

- Patch file naming (follow the convention: `{YYYYMMDD}-issue-{N}-{commit}-{slug}.patch`)
- Bisection documentation content and structure
- Commit message wording
- Branch naming (follow the convention: `issue-{N}-{slug}`)
- Reproducer script implementation details (within the established template)
- Issue body formatting

## Troubleshooting

### Build fails

- Check Stack resolver in `/home/yoh/proj/git-annex/stack.yaml`
- Try `stack clean` and rebuild
- Singularity container `docker://datalad/buildenv-git-annex` available for consistent builds
- If Haskell dependency resolution fails, check if the resolver needs updating

### Reproducer is flaky

- Ensure temp dirs are truly isolated (`mktemp -d`)
- Add `set -eu` for strict error handling
- Avoid relying on timing; add explicit waits or retries where needed
- Test multiple consecutive runs to confirm determinism
- Check for leftover state from prior runs (git config, annex metadata)

### CI does not trigger on PR

- Workflows trigger on changes to `patches/*.patch` or workflow files
- Ensure the patch file is in the `patches/` directory (not a subdirectory)
- Fork PRs from first-time contributors need one manual approval before CI runs
- Check that the fork is up to date with upstream master

### git bisect skip loops

- If too many commits fail to build, narrow the range manually
- Use `git bisect skip` for individual broken commits
- Consider bisecting on a coarser granularity (e.g., tagged releases) first

### Patch does not apply cleanly

- The patch targets a specific commit; if git-annex master has moved, rebase
- Use `git apply --check` to test before applying
- Regenerate the patch against the current HEAD if needed

## Output

After completing the skill, the following artifacts should exist:

- **GitHub issue** filed on `datalad/git-annex` with issue number `{N}`
- **`docs/ai_bits/bisections/issue-{N}-{slug}.md`** - Bisection documentation with root cause analysis
- **`docs/ai_bits/bisections/issue-{N}-{slug}-reproducer.sh`** - Self-contained reproducer script
- **`patches/{YYYYMMDD}-issue-{N}-{commit}-{slug}.patch`** - Fix patch applied by CI during build
- **PR on `datalad/git-annex`** with Red/Green CI demonstration (created from `yarikoptic-test` fork)
- **`.git/upstream-report.md`** - Draft upstream bug report for user review
