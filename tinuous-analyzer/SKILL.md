---
name: tinuous-analyzer
description: Analyze con/tinuous CI log collections to identify test regressions, compare successful vs failing runs, and provide investigation recommendations. Use when users mention test failures, CI regressions, or need to understand what changed between CI runs.
---

# Tinuous CI Log Analyzer

This skill helps analyze CI/CD logs collected by con/tinuous (https://github.com/con/tinuous/) to identify when tests started failing and what changed.

## When to Use This Skill

Automatically invoke this skill when the user:
- Mentions a specific test is failing or started failing recently
- Asks about CI regressions or what changed in CI
- Wants to know why tests that were passing are now failing
- Needs to compare successful vs failing CI runs
- Asks to investigate test failures in a tinuous collection

## con/tinuous Directory Structure

con/tinuous organizes logs hierarchically:
```
{year}/{month}/{day}/{type}/{timestamp}/{commit}/
  └── {ci}-{workflow}-{number}-{status}/
      ├── 0_test.txt       # Main test log
      └── test/
          └── system.txt    # System information
```

Key files:
- `tinuous.yaml` - Configuration defining collection patterns
- `.tinuous.state.json` - State tracking for collection

Status indicators: `success`, `failed`, `errored`, `incomplete`

## Step-by-Step Analysis Process

### 1. Locate the Tinuous Collection

First, find the CI log directory:
- Look for `tinuous.yaml` in the project or a separate CI directory
- Common locations:
  - `{project}-ci/` (e.g., `datalad-fuse-ci/`)
  - `ci/` subdirectory
  - Adjacent to the main project repository
- Use `find` or ask the user if the location is not obvious

### 2. Identify the Failing Test

If the user provides a test name, search for recent failures:
```bash
datalad foreach-dataset -s --o-s relpath -r git grep "FAILED.*{test_name}"
```

Or use regular grep:
```bash
grep -r "FAILED.*{test_name}" {ci_directory}/YYYY/MM/DD/
```

This identifies:
- Which dates have failures
- The full test path
- Build numbers and status

### 3. Find the Regression Date Range

Determine when failures started:
- Note the earliest failure date from step 2
- Look backward in time (day by day) to find the last success
- Use directory structure: `YYYY/MM/DD/cron/` or `YYYY/MM/DD/push/`

Example search pattern:
```bash
# Look for specific days
ls {ci_dir}/YYYY/MM/23/cron/*/commit/github-*-success/
ls {ci_dir}/YYYY/MM/24/cron/*/commit/github-*-failed/
```

### 4. Extract Key Information for Comparison

For both the last successful run and the first failing run, extract:

**a) Test Results Summary:**
- Total tests: passed/failed counts
- Specific failure messages and assertions
- Test execution time

**b) System Environment:**
```bash
# Look in test log files for system information
grep -A 20 "## system\|platform linux\|Runner Image" {log_file}
```

Key items to compare:
- Python version and implementation
- OS distribution and version
- Kernel version
- Runner image version (for GitHub Actions)
- Filesystem information

**c) Dependencies:**
```bash
# Look for pip freeze or dependency installation
grep -A 100 "pip freeze\|install_package\|installed packages" {log_file}
```

Compare versions of:
- Core dependencies (datalad, fsspec, pytest, etc.)
- System packages
- Related libraries

**d) Test Execution Context:**
- Working directory
- Test configuration
- Environment variables (if visible)
- Timing differences

### 5. Perform Focused Comparison

**DO NOT** just diff the entire files - timestamps and build IDs will differ.

Instead, extract and compare specific sections:

```bash
# Extract system info section
grep -A 30 "## system" success_log.txt > success_system.txt
grep -A 30 "## system" failed_log.txt > failed_system.txt

# Extract dependency versions
grep -A 200 "py3: freeze>" success_log.txt > success_deps.txt
grep -A 200 "py3: freeze>" failed_log.txt > failed_deps.txt

# Extract test execution
grep -A 50 "test session starts" success_log.txt > success_tests.txt
grep -A 50 "test session starts" failed_log.txt > failed_tests.txt
```

Focus on:
- Version number changes (e.g., `3.8.17` → `3.8.18`)
- New or removed dependencies
- System configuration changes
- Error messages and stack traces (in failing run)

### 6. Generate Investigation Summary

Provide a structured report with:

**Regression Summary:**
- Test name and path
- Date range: "Last success: YYYY-MM-DD, First failure: YYYY-MM-DD"
- Number of consecutive failures
- Commit hash if it changed

**Key Differences Identified:**

Categorize findings:

1. **Environment Changes:**
   - Runner/VM image updates
   - OS or kernel version changes
   - Python version changes

2. **Dependency Changes:**
   - List packages with version changes
   - Highlight security updates or major version bumps
   - Note any new dependencies added

3. **Test Behavior Changes:**
   - Error type and message
   - Timing differences (if significant)
   - Changed test output patterns

4. **Suspicious Patterns:**
   - Race conditions (if timing-related)
   - File system issues (if FUSE or I/O related)
   - Concurrency problems (if parallel test)

**Recommendations for Investigation:**

Provide 3-5 specific, actionable items:
- "Investigate {package} version change from X.Y.Z to A.B.C"
- "Check release notes for {system component} on date YYYY-MM-DD"
- "Review test for race condition given parallel execution failure"
- "Consider if runner image change affects FUSE functionality"
- "Examine if dependency security patch changed behavior"

**Next Steps:**
- Commands to run locally to reproduce
- Links to relevant issue trackers or changelogs
- Suggestions for fixing or working around the issue

## Using DataLad Commands

If the CI collection is a DataLad dataset, you can use:

```bash
# Search across the dataset
datalad foreach-dataset -s --o-s relpath -r git grep "pattern"

# Get file content (retrieves from annex if needed)
datalad get path/to/log/file.txt

# Check dataset structure
datalad subdatasets

# See what changed
datalad diff --to HEAD~10
```

## Example Invocation

**User:** "The test_parallel_access test in datalad-fuse started failing recently"

**Your Response:**
1. Find the datalad-fuse-ci directory
2. Search for FAILED + test_parallel_access across recent dates
3. Identify: failing since 2025-10-24, was passing 2025-10-23
4. Extract and compare:
   - Runner image versions
   - Python and dependency versions
   - Test output and error messages
5. Report: "Runner image updated from 20251014.106 to 20251015.xxx, updated packages include fsspec 2025.2.0→2025.3.0, error shows SHA256 mismatch suggesting file content corruption during parallel access"
6. Recommend: "Check fsspec 2025.3.0 release notes for changes to HTTP caching or parallel access, consider pinning to 2025.2.0 to test if this is the cause"

## Important Notes

- Focus on **meaningful** differences, not timestamps or build IDs
- Consider **temporal correlation** (external changes around regression date)
- Test failures can be due to:
  - Dependency updates (most common)
  - CI environment changes (runner images)
  - Test flakiness exposed by timing changes
  - Upstream service changes (for integration tests)
- Always provide **actionable** recommendations
- If causes are unclear, suggest **bisection** or **local reproduction** steps

## Output Format

Structure your response as:

```
# Regression Analysis: {test_name}

## Timeline
- Last Success: YYYY-MM-DD (build #{number})
- First Failure: YYYY-MM-DD (build #{number})
- Consecutive Failures: {count} days

## Critical Differences

### Environment Changes
{list changes}

### Dependency Changes
{list changes}

### Test Failure Details
{error message and context}

## Root Cause Hypothesis
{your best guess based on evidence}

## Investigation Recommendations
1. {specific action}
2. {specific action}
3. {specific action}

## Commands to Run
{concrete commands user can execute}
```

## Tips for Effective Analysis

1. **Start broad, then narrow:** Begin with date ranges, then focus on specific logs
2. **Pattern matching:** Look for similar failures across multiple days
3. **External context:** Consider if regression date aligns with known events (GitHub Actions updates, package releases)
4. **Test characteristics:** Parallel, FUSE, I/O, or network tests have specific failure modes
5. **Be hypothesis-driven:** Form theories and look for evidence rather than reading everything
