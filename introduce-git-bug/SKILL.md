---
name: introduce-git-bug
description: Introduce git-bug distributed issue tracking to a git project. Configures GitHub bridge, syncs issues, pushes refs, and documents workflow in DEVELOPMENT.md and CLAUDE.md. Use when setting up git-bug in a new project.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# Introduce git-bug to a Project

Set up [git-bug](https://github.com/git-bug/git-bug) distributed, offline-first issue tracking
in a git project. Configures a GitHub bridge to sync issues, stores them as native git objects
under `refs/bugs/*`, and documents the workflow for developers and AI assistants.

## When to Use

- User wants to add local/offline issue tracking to a project
- User mentions "git-bug" or wants distributed issue tracking
- User asks to sync GitHub issues into git
- User asks to "introduce git-bug" or run "/introduce-git-bug"

## Prerequisites

### git-bug binary

Check if `git bug` is available:

```bash
git bug version
```

If not installed, guide the user through installation (pick one):

1. **Pre-built binary** (recommended):
   ```bash
   # Download latest release for your platform
   # https://github.com/git-bug/git-bug/releases
   curl -L -o git-bug https://github.com/git-bug/git-bug/releases/latest/download/git-bug_linux_amd64
   chmod +x git-bug
   # Move to a directory in PATH, e.g.:
   mv git-bug ~/.local/bin/
   ```

2. **Homebrew** (macOS/Linux):
   ```bash
   brew install git-bug
   ```

3. **Nix**:
   ```bash
   nix profile install nixpkgs#git-bug
   ```

4. **From source** (requires Go):
   ```bash
   go install github.com/git-bug/git-bug@latest
   ```

5. **Custom path** (e.g., `~/.claude/bin/git-bug`):
   Ensure the directory is in PATH before proceeding.

### Other prerequisites

- `gh` CLI for PR creation (optional but recommended)
- Git repository with a GitHub remote
- GitHub token with at least `public_repo` scope (for bridge)

## Workflow Overview

1. **Check existing** - Look for existing git-bug configuration
2. **Gather project info** - Detect GitHub remote, org/repo, main branch
3. **Create feature branch** - `enh-git-bug`
4. **Configure bridge** - Set up GitHub bridge with authentication
5. **Pull issues** - Sync GitHub issues into git-bug
6. **Push refs** - Push `refs/bugs/*` to remote for team access
7. **Update DEVELOPMENT.md** - Document git-bug workflow
8. **Update CLAUDE.md** - Add AI assistant context hints
9. **Commit & PR** - Commit documentation, prepare PR

## Step 0: Check for Existing git-bug Configuration

```bash
# Check for existing bridge configuration
git bug bridge ls 2>&1

# Check for existing refs/bugs
git for-each-ref refs/bugs/ --count=1
```

### If git-bug is already configured:

1. Check bridge status: `git bug bridge ls`
2. Try pulling: `git bug bridge pull`
3. May only need documentation updates - skip to Step 6

### If no configuration exists:

Proceed with Step 1.

## Step 1: Gather Project Information

### Detect GitHub remote

```bash
# List remotes to find the upstream GitHub URL
git remote -v
```

Look for:
- `origin` pointing to `github.com/<org>/<repo>` (most common for upstream)
- Fork remotes like `gh-<username>` for personal forks
- Choose the **upstream** remote (typically `origin` for org repos)

### Detect project details

```bash
# Get org/repo from remote URL
git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||'

# Get default/main branch
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'

# Count open issues on GitHub (if gh is authenticated)
gh api repos/<org>/<repo> --jq '.open_issues_count'
```

### Ask about remote choice

If multiple GitHub remotes exist, ask the user which is the upstream:

```
Which remote is the upstream GitHub repository?
- origin (https://github.com/org/repo)
- other-remote (https://github.com/other/repo)
```

## Step 2: Create Feature Branch

```bash
# Branch from the main branch
git checkout -b enh-git-bug master  # or main, depending on project
```

If there are uncommitted changes, warn the user and suggest stashing.

## Step 3: Configure GitHub Bridge

### Determine authentication token

Try these sources in order:

1. **gh CLI**: `gh auth token`
2. **Git config**: `git config --global hub.oauthtoken`
3. **Environment**: `$GH_TOKEN` or `$GITHUB_TOKEN`

If none available, ask the user to provide one.

### Create bridge

```bash
git bug bridge new \
  --name github \
  --target github \
  --url "https://github.com/<org>/<repo>" \
  --token "<token>"
```

**Notes:**
- The bridge name `github` is conventional but can be anything
- The token needs at least `public_repo` scope for public repos
- For private repos, `repo` scope is needed

### Verify bridge

```bash
git bug bridge ls
```

## Step 4: Pull Issues

```bash
git bug bridge pull
```

This will:
- Import all open and closed issues
- Import comments and labels
- Import issue metadata (author, dates, assignees)
- May take several minutes for large repos

### Report sync statistics

```bash
# Count synced issues
echo "Open issues:"
git bug ls status:open 2>&1 | wc -l

echo "Closed issues:"
git bug ls status:closed 2>&1 | wc -l

# Show a sample issue
git bug ls status:open 2>&1 | head -5
```

### Known limitation: Images/Media

git-bug's bridge importers **do not** fetch embedded images. The feature matrix
confirms media support is not available across all importers (GitHub, GitLab, Jira, Launchpad).

Image URLs from GitHub issues (e.g., `user-images.githubusercontent.com`,
`github.com/user-attachments`) are preserved as markdown text in issue bodies,
but the actual image blobs are not stored in git objects.

**Potential workaround** (future enhancement): A post-processing script could:
1. Parse issue bodies from `git bug show` output
2. Extract image URLs matching GitHub CDN patterns
3. Download them into a `.git-bug-media/` directory
4. Create a mapping file for URL-to-local-path translation

## Step 5: Push Refs to Remote

### Ask user about pushing

This pushes `refs/bugs/*` to the remote, making issues available to all collaborators
who clone/fetch the repo. Ask the user:

```
Should I push git-bug refs to the remote?
- Yes, push to origin (team can access issues offline)
- No, keep local only for now
```

### Push refs

```bash
git bug push <remote>
```

**Note:** This requires write access to the remote. If the user only has fork access,
push to their fork remote instead.

### Verify push

```bash
git ls-remote <remote> 'refs/bugs/*' | head -5
```

## Step 6: Update DEVELOPMENT.md

Find the appropriate location in DEVELOPMENT.md (or equivalent developer docs).
Good insertion points:
- Before the "Releasing" section
- After "Environment variables" section
- As a new top-level section

### Section template

Insert the following section, adapting to the project's documentation style:

```markdown
## Git-bug: Local Issue Tracking

This project uses [git-bug](https://github.com/git-bug/git-bug) for distributed,
offline-first issue tracking. Issues from GitHub are synced and stored as native
git objects under `refs/bugs/*`.

### Installation

Install git-bug from [releases](https://github.com/git-bug/git-bug/releases)
or via package manager:

```bash
# macOS/Linux (Homebrew)
brew install git-bug

# Nix
nix profile install nixpkgs#git-bug

# Binary download
curl -L -o git-bug https://github.com/git-bug/git-bug/releases/latest/download/git-bug_linux_amd64
chmod +x git-bug && mv git-bug ~/.local/bin/
```

### Quick Start

```bash
# Fetch latest issues from GitHub
git bug pull

# List open issues
git bug ls status:open

# Show a specific issue (by prefix)
git bug show <id-prefix>

# Search issues
git bug ls "label:bug"
git bug ls "author:username"
```

### Query Language

git-bug supports a rich query language for filtering:

```bash
git bug ls status:open label:enhancement      # Open enhancements
git bug ls status:open "title:upload"          # Issues mentioning upload
git bug ls "author:username"                   # Issues by author
git bug ls status:open sort:creation-desc      # Newest first
```

### Syncing with GitHub

```bash
# Pull latest from GitHub
git bug bridge pull

# Push local changes to GitHub (if you have write access)
git bug bridge push

# Push git-bug refs to remote (for team access)
git bug push origin
```

### Known Limitations

- **Images/media**: Bridge importers preserve image URLs as markdown text but
  do not download image blobs. Images from `user-images.githubusercontent.com`
  are accessible only while GitHub hosts them.
- **Two-way sync**: While git-bug supports pushing changes back to GitHub,
  the primary workflow is pull-from-GitHub for offline access.
```

**Important**: Adapt the backtick fencing to match the project's existing style.
Some projects use 4-space indentation for code blocks instead of triple backticks.

## Step 7: Update CLAUDE.md

Append a git-bug section to CLAUDE.md (or equivalent AI assistant instructions):

```markdown
## Issue Tracking with git-bug

This project has GitHub issues synced locally via git-bug. Use these commands
to get issue context without needing GitHub API access:

- `git bug ls status:open` - list open issues
- `git bug show <id-prefix>` - show issue details and comments
- `git bug ls "title:keyword"` - search issues by title
- `git bug ls "label:bug"` - filter by label
- `git bug bridge pull` - sync latest issues from GitHub

When working on a bug fix or feature, check `git bug ls` for related issues
to understand context and prior discussion.
```

## Step 8: Commit Documentation Changes

Only documentation files are committed (DEVELOPMENT.md, CLAUDE.md).
The git-bug refs are pushed separately (Step 5).

```bash
git add DEVELOPMENT.md CLAUDE.md
git commit -m "Add git-bug distributed issue tracking documentation

Document git-bug installation, CLI usage, query language, and GitHub
sync workflow. Add AI assistant hints for using git-bug for issue context."
```

**Note**: Pre-commit hooks may modify the files (trailing whitespace, end-of-file fixer).
If the commit fails with "files were modified", just re-run the commit.

## Step 9: Prepare and Create Pull Request

### Write PR description

Save to `.git/PR_BODY.md`:

```markdown
## Summary

- Configured git-bug GitHub bridge to sync issues as native git objects
- Synced N open + N closed issues with comments
- Pushed `refs/bugs/*` to remote for team offline access
- Documented git-bug workflow in DEVELOPMENT.md
- Added AI assistant hints in CLAUDE.md

## What is git-bug?

[git-bug](https://github.com/git-bug/git-bug) is a distributed, offline-first
bug tracker that stores issues as native git objects. It bridges with GitHub
to sync issues bidirectionally.

Benefits:
- **Offline access**: Browse and search issues without internet
- **Git-native**: Issues travel with the repo, no external service needed
- **AI-friendly**: Claude Code and other tools can query issues locally
- **Fast**: Local queries are instant, no API rate limits

## Changes

- **DEVELOPMENT.md**: Added git-bug section with installation, CLI usage,
  query language, sync workflow, and known limitations
- **CLAUDE.md**: Added issue tracking hints for AI assistants
- **refs/bugs/***: Synced GitHub issues (pushed to remote)

## Known Limitations

- Bridge importers do not fetch embedded images (URLs preserved as text)
- Primary workflow is pull-from-GitHub; push-back is supported but secondary

---

Generated with [Claude Code](https://claude.com/claude-code)
```

### Provide push + PR creation command

```bash
git push origin enh-git-bug && gh pr create --repo <org>/<repo> --title "Add git-bug distributed issue tracking" --body-file .git/PR_BODY.md
```

## Interactive Decision Points

When running this skill, ask the user about:

1. **Which remote** is the upstream GitHub repository
2. **Authentication token** source (gh auth, env var, git config)
3. **Whether to push refs** to remote (team access vs local-only)
4. **Where in DEVELOPMENT.md** to insert the git-bug section
5. **PR creation** - whether to create PR or just prepare commits

### Autonomous Decisions

The LLM should decide WITHOUT asking:

- Bridge name (`github` is conventional)
- Section content (adapt to existing doc style)
- Commit message wording
- Whether to include known limitations section (always yes)

## Troubleshooting

### "token is not valid"
- Token may lack required scopes. Need at least `public_repo` for public repos.
- Try: `gh auth token` for a fresh token

### "git bug: command not found"
- Ensure the binary is in PATH
- Try: `export PATH="$HOME/.local/bin:$PATH"`

### Bridge pull fails with rate limiting
- GitHub API rate limit (5000/hour for authenticated, 60/hour unauthenticated)
- Wait and retry, or use a token with higher rate limits

### Push fails with permission denied
- Need write access to the remote
- Push to a fork remote instead: `git bug push gh-<username>`

### Pre-commit hooks fail on commit
- Run the commit again - hooks may auto-fix trailing whitespace/EOF
- If second attempt also fails, investigate the specific hook error

## Output

After completing the skill:
- Feature branch `enh-git-bug` with documentation changes
- GitHub bridge configured and issues synced
- `refs/bugs/*` pushed to remote (if approved)
- DEVELOPMENT.md updated with git-bug workflow documentation
- CLAUDE.md updated with issue tracking hints
- PR description saved to `.git/PR_BODY.md`
- Ready-to-use command: `git push <remote> <branch> && gh pr create ...`
