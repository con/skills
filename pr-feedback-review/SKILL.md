---
name: pr-feedback-review
description: Load a PR's review feedback (human + bot), classify each comment, and recommend what to address vs dismiss with draft responses. Works from a local repo directory or a PR URL.
allowed-tools: Bash, Read, Edit, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
user-invocable: true
---

# PR Feedback Review

Load all review feedback on a GitHub pull request — from human reviewers and
bots (Copilot, CodeRabbit, etc.) — classify each comment, and generate
actionable recommendations: code changes to apply, responses to post, and
comments safe to dismiss.

## Configuration

This skill uses the following values. Adjust for your setup by editing this section:

- **SCAN_DIRS**: `~/proj` — comma-separated parent directories to scan for git repos
- **GITHUB_USER**: `yarikoptic` — your GitHub username
- **MAX_SCAN_DEPTH**: `3` — how deep to recurse when scanning for repos
- **AI_COMPANION_TOKEN_FILE**: `~/.claude/gh-token` — path to a shell-sourceable
  file that exports `GH_TOKEN` for an AI companion GitHub account (e.g.
  `yarikoptic-gitmate`). When present, reply scripts use this token so
  responses are posted from the companion account rather than the user's
  personal account. The file should contain `export GH_TOKEN=github_pat_...`.
  Set to empty string to disable and post as yourself.

Throughout this document, these names refer to the configured values above.

## Arguments

Parse the user's invocation for these optional arguments:

| Arg | Default | Description |
|-----|---------|-------------|
| `--path <dir>` | cwd | Local directory to detect PR from |
| `--pr <URL>` | *(none)* | GitHub PR URL (`https://github.com/owner/repo/pull/N`) |
| `--pr <number>` | *(none)* | PR number (combined with cwd git context) |
| `--bot-only` | `false` | Only show bot comments (Copilot, CodeRabbit, etc.) |
| `--unresolved` | `false` | Only show unresolved threads |

At most one of `--path` and `--pr <URL>` should be provided. `--pr <number>`
uses the current directory's git remote to resolve the full repo identity.

## Execution

### Step 1 — Prerequisites

```bash
gh auth status
```

If this fails, tell the user to run `gh auth login` first.

### Step 2 — Parse Input & Resolve PR Identity

Determine `OWNER`, `REPO`, and `PR_NUMBER` from the input.

**Case A: From local folder** (no `--pr` or `--pr <number>`):

1. Determine the repo root:
   ```bash
   git -C <dir> rev-parse --show-toplevel
   ```
2. Get the current branch:
   ```bash
   git -C <dir> branch --show-current
   ```
3. Extract GitHub owner/repo from remote:
   ```bash
   git -C <dir> remote -v
   ```
   Parse the `origin` (or first `github.com`) remote URL to extract `OWNER/REPO`.

4. Find the PR for this branch:
   ```bash
   gh pr list --repo OWNER/REPO --head BRANCH --json number,url --limit 1
   ```
5. If no PR found via branch, try `gh pr list --repo OWNER/REPO --state open --json number,headRefName --limit 50` and match by branch name prefix or HEAD SHA.

**Case B: From PR URL** (`--pr https://github.com/owner/repo/pull/N`):

1. Parse the URL to extract `OWNER`, `REPO`, `PR_NUMBER`.
2. Get the PR's branch name:
   ```bash
   gh pr view PR_NUMBER --repo OWNER/REPO --json headRefName --jq .headRefName
   ```
3. Find a local repo (see Step 3).

**Case C: From PR number** (`--pr N` without URL):

1. Resolve `OWNER/REPO` from the cwd's git remote (same as Case A steps 1-3).
2. Set `PR_NUMBER` from the argument.

If none of the above resolves a PR, report the failure and stop.

### Step 3 — Find Local Repository

When starting from a PR URL (Case B), find a local checkout:

1. For each directory in `$SCAN_DIRS` (comma-separated), use `find` to locate
   `.git` directories up to `$MAX_SCAN_DEPTH` levels deep:
   ```bash
   find <scan_dir> -maxdepth MAX_SCAN_DEPTH -name .git -type d 2>/dev/null
   ```
2. For each found repo, check if its remote matches `OWNER/REPO`:
   ```bash
   git -C <repo_dir> remote -v 2>/dev/null | grep -i 'github.com.*OWNER/REPO'
   ```
3. Once a matching repo is found, check for worktrees on the PR branch:
   ```bash
   git -C <repo_dir> worktree list --porcelain
   ```
4. Prefer: worktree on the PR branch > main repo on the PR branch > main repo
   on default branch.
5. If no local repo is found, report this and continue with remote-only analysis
   (skip Step 6 — local code context loading).

Store the resolved local path as `LOCAL_PATH` (or empty if not found).

### Step 4 — Fetch PR Data

Fetch all of these in parallel where possible via `gh` CLI:

1. **PR metadata:**
   ```bash
   gh pr view PR_NUMBER --repo OWNER/REPO --json title,body,headRefName,baseRefName,state,reviewDecision,additions,deletions,changedFiles,headRefOid
   ```

2. **PR diff:**
   ```bash
   gh pr diff PR_NUMBER --repo OWNER/REPO
   ```

3. **Formal reviews** (approve/request-changes/comment):
   ```bash
   gh api repos/OWNER/REPO/pulls/PR_NUMBER/reviews --paginate
   ```

4. **Inline review comments** (file-level, with diff position):
   ```bash
   gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments --paginate
   ```

5. **Issue-level comments** (general PR conversation):
   ```bash
   gh api repos/OWNER/REPO/issues/PR_NUMBER/comments --paginate
   ```

### Step 5 — Load Local Code Context

Skip this step if `LOCAL_PATH` is empty.

1. From the PR diff (Step 4.2), extract the list of changed files.
2. For each changed file, read its current content from `LOCAL_PATH` using the
   Read tool. This provides full context for understanding comments.
3. Check if local HEAD is ahead of the PR's remote HEAD (i.e., newer local
   commits that may address feedback):
   ```bash
   git -C LOCAL_PATH fetch origin
   git -C LOCAL_PATH log --oneline REMOTE_SHA..HEAD 2>/dev/null
   ```
   where `REMOTE_SHA` is `headRefOid` from Step 4.1.

Store any newer commits as `LOCAL_AHEAD_COMMITS` — these may already address
some review feedback.

### Step 6 — Classify Each Comment

Process every comment collected in Step 4 (from reviews, inline comments, and
issue comments). For each comment, determine:

#### Source

Categorize the comment author:

| Source | Match criteria |
|--------|---------------|
| `self` | Author login matches `$GITHUB_USER` — **skip these** |
| `bot-copilot` | Author login contains `copilot` or ends with `[bot]` and is Copilot |
| `bot-coderabbit` | Author login contains `coderabbit` |
| `bot-other` | Author login ends with `[bot]` (other bots) |
| `human-reviewer` | Everything else |

Skip comments from `self` — they are your own responses and don't need action.

#### Type

Classify the comment content into one of:

| Type | Indicators |
|------|-----------|
| `suggestion` | Contains a ` ```suggestion ` block, or proposes a specific code change |
| `question` | Asks "why", "how", "could you explain", ends with `?` |
| `nitpick` | Prefixed "nit:", "nitpick:", or about style/formatting only |
| `issue` | Identifies a bug, correctness concern, missing edge case |
| `informational` | General observation, context sharing, no action requested |
| `approval` | "LGTM", approval review state, "+1", "looks good" |

#### Resolution Status

Determine if the comment has already been addressed:

- **Resolved on GitHub**: Check if the review thread is marked resolved
  (inline comments may have `"resolved": true` or similar field in the API
  response).
- **Already replied**: Check if `$GITHUB_USER` has posted a reply in the same
  thread (look for subsequent comments with matching `in_reply_to_id` or same
  `pull_request_review_id`).
- **Addressed by commit**: If `LOCAL_AHEAD_COMMITS` is non-empty, check if
  any of those commits touch the file/line referenced by the comment.

#### Actionable Assessment

- `yes` — the comment identifies a real issue or useful improvement
- `no` — the comment is incorrect, already addressed, or informational-only
- `maybe` — uncertain; needs human judgment

#### Confidence

0–100% confidence in the classification.

#### Filtering

After classification, apply filters:
- If `--bot-only`: keep only `bot-copilot`, `bot-coderabbit`, `bot-other`
- If `--unresolved`: keep only comments not marked resolved and not already replied-to

### Step 7 — Generate Recommendations

For each remaining comment (after filtering and skipping `self`), generate a
recommendation based on its type and actionability:

**Actionable suggestions/issues** (actionable=yes, type=suggestion|issue):
- Show the comment text and the relevant code context
- If a ` ```suggestion ` block exists, show exactly what it would change
  (before/after)
- **Fix the issue directly** using red/green TDD:
  1. **Red**: Write or extend a test that exposes the bug/missing behavior.
     Prefer extending an existing test over creating a new one. Run it to
     confirm it fails.
  2. **Green**: Apply the minimal code fix. Run the test to confirm it passes.
  3. **Verify**: Run the broader test suite to ensure no regressions.
  4. **Commit**: Create a commit with a message referencing the review comment
     (e.g. "Spotted by Copilot review on PR #NNN").
  5. Include the commit SHA in the reply so the reviewer can verify the fix.
- If the fix is too complex or risky to apply immediately, propose the edit
  and note it as a follow-up instead of committing.

**Dismissible comments** (actionable=no):
- Draft a concise response explaining why no change is needed
- Reference relevant code, docs, or project conventions
- Common bot dismissal patterns:
  - Copilot suggesting wrong API/kwargs: "Thanks for the review. This kwarg is
    correct for the X plugin — see [link/code reference]."
  - CodeRabbit flagging intentional patterns: "This is intentional — [reason]."

**Questions** (type=question):
- Draft an answer based on the code context, git history, and PR description

**Already addressed** (resolution != unresolved):
- Note how it was addressed (reply, commit, thread resolution)
- No action needed

**Bot comments with low accuracy** (bot source + actionable=no, confidence ≥ 80%):
- Flag known bot weaknesses and draft a brief dismissal

### Step 8 — Output Structured Report

Print the following report:

```markdown
## PR Feedback Review: OWNER/REPO#PR_NUMBER

### PR Summary
- **Title**: <title>
- **Branch**: <headRefName> -> <baseRefName>
- **State**: <state> | **Review Decision**: <reviewDecision>
- **Local path**: <LOCAL_PATH or "not found locally">
- **Changed files**: <changedFiles> (+<additions> -<deletions>)

### Feedback Summary
- **Total comments**: N (M from bots, K from humans)
- **Skipped (self)**: N
- **Unresolved**: N
- **Actionable**: N | **Dismissible**: N | **Already addressed**: N

### Action Items

#### 1. [TYPE] Comment by @author on `file:line`
> <quoted comment, truncated to ~5 lines if long>

**Source**: <source> | **Actionable**: <yes/no/maybe> | **Confidence**: N%

**Recommendation**: <address|dismiss|discuss|already-addressed>

<proposed code change or draft response>

---

(repeat for each comment, ordered: actionable first, then dismissible, then addressed)

### Draft Batch Response

<If there are multiple dismissible bot comments, draft a single issue comment
addressing them all in one reply. Use a polite, concise tone. Example:

"Thanks for the automated review! A few notes on the suggestions:
- **file.py:42** — this kwarg is correct for pytest-timeout (not pytest-xdist)
- **file.py:88** — intentional; we use this pattern for [reason]
- **file.py:120** — good catch, addressed in <commit>

Let me know if anything else needs attention."
>
```

### Step 8b — Generate Per-Comment Reply Script

After the report, generate a shell script that replies to each individual
review comment thread using `gh api`. This lets the user review, edit, and
selectively run replies.

1. Determine the git directory for script storage:
   - If `.git` is a file (worktree), read its `gitdir:` target
   - Otherwise use `.git/`
   - Store the script at `<gitdir>/PR-replies.sh`

2. For each non-self comment (skipping comments already replied to by
   `$GITHUB_USER`), generate a `gh api` call. **Important**: pipe all
   `gh api` output through `> /dev/null` to suppress JSON responses, and
   use `&&` to print a short status on success or catch errors:
   ```bash
   # <file>:<line> — <short description> [ADDRESSED|DISMISSED|DISCUSS]
   # https://github.com/OWNER/REPO/pull/PR_NUMBER#discussion_rCOMMENT_ID
   gh api "repos/OWNER/REPO/pulls/PR_NUMBER/comments/COMMENT_ID/replies" \
     -f body="<reply text>" > /dev/null && echo "  replied to COMMENT_ID" \
     || echo "  FAILED to reply to COMMENT_ID"
   ```
   For `[ADDRESSED]` comments that were fixed via commit (Step 7), include
   the short commit SHA and first line of the commit message in the reply
   body, e.g.: "Fixed in abc1234 `BF: forward recursion_limit ...` — ..."
   so the reviewer can click through to verify the fix.

3. Script format requirements:
   - Header with `#!/bin/bash`, `set -e`, `REPO`/`PR` variables, and
     companion token setup. When `$AI_COMPANION_TOKEN_FILE` is configured
     and the file exists, source it at the top of the script so all `gh api`
     calls authenticate as the companion account:
     ```bash
     #!/bin/bash
     set -e
     REPO="OWNER/REPO"
     PR=NUMBER

     # Authenticate as AI companion account
     source ~/.claude/gh-token  # exports GH_TOKEN
     export GH_TOKEN
     ```
     Also add a verification line that prints which account is posting:
     ```bash
     echo "Posting replies as: $(gh api user --jq .login)"
     ```
   - Each comment block has:
     - A comment line with file, line number, short description, and
       `[ADDRESSED]`, `[DISMISSED]`, or `[DISCUSS]` tag
     - The full `html_url` of the comment as a clickable link in a comment
     - The `gh api` command to post the reply, with output suppressed
       (`> /dev/null`) and a short success/failure echo
   - Group by status: ADDRESSED first, then DISMISSED, then DISCUSS
   - Blank line between each comment block

4. Get the `html_url` for each comment from the API response data collected
   in Step 4.4 (inline review comments). The URL format is:
   `https://github.com/OWNER/REPO/pull/PR_NUMBER#discussion_rCOMMENT_ID`

5. Tell the user the script path and provide the run command:
   ```
   Review and run: bash <gitdir>/PR-replies.sh
   ```
   Remind them they can comment out lines they want to skip or edit replies
   before running.

### Step 9 — Interactive Follow-up

Actionable issues should already be fixed and committed in Step 7.
After presenting the report, ask the user:

- "Should I push and post the reply script?" (if fixes were committed)
- "Any comments you want to re-classify or handle differently?"

Wait for the user's response before taking any further action.

## Notes

- Pagination: The GitHub API may paginate results. Always use `--paginate`
  with `gh api` to fetch all pages.
- Rate limits: If `gh api` returns 403/rate-limit errors, report this to
  the user and suggest waiting or using a token with higher limits.
- Large PRs: If the diff is very large (>5000 lines), focus on files that
  have review comments rather than reading every changed file.
- Bot detection: New bots appear regularly. If an author's login ends with
  `[bot]`, treat it as a bot even if not specifically recognized.
