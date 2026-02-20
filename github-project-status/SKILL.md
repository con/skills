---
name: github-project-status
description: Check the health and maintenance status of a GitHub project. Use when user asks about project status, whether a project is maintained, abandoned, or looking for alternatives. Analyzes commit history, releases, issues, PRs, and searches for active forks or community discussions about project future.
allowed-tools: WebFetch, WebSearch, Bash(gh:*)
user-invocable: true
---

# GitHub Project Status Checker

Analyze the health and maintenance status of GitHub projects, especially those that may be unmaintained, abandoned, or in need of community takeover.

## When to Use

- User asks "is X project still maintained?"
- User wants to evaluate a dependency's health
- User asks about project status, activity, or alternatives
- User mentions a GitHub URL and asks about its status
- User asks to check if there's a more active fork

## Input Handling

Accept GitHub project references in these formats:
- Full URL: `https://github.com/owner/repo`
- Short form: `owner/repo`
- Organization URL: `https://github.com/org` (analyze main repos)

## Analysis Steps

### 1. Fetch Core Metadata

Use WebFetch on `https://api.github.com/repos/{owner}/{repo}` to extract:
- `created_at`, `pushed_at`, `updated_at`
- `stargazers_count`, `forks_count`, `open_issues_count`
- `archived`, `disabled`
- `description`, `license`

### 2. Analyze Commit Activity

Use WebFetch on `https://github.com/{owner}/{repo}/commits/master` (or main) to find:
- Date of last commit
- Author of recent commits (single maintainer vs. community?)
- Frequency of commits in past year

### 3. Check Release History

Use WebFetch on `https://github.com/{owner}/{repo}/tags` to find:
- Latest release/tag version and date
- Release frequency pattern
- Time since last release

### 4. Assess Issue/PR Backlog

Use WebFetch on `https://github.com/{owner}/{repo}/pulls?q=is:pr+is:open+sort:updated-desc`:
- Count of open PRs
- Age of oldest open PRs
- Whether PRs are being merged

Use WebFetch on `https://github.com/{owner}/{repo}/issues?q=is:issue+is:open+sort:updated-desc`:
- Count of open issues
- Recent issue activity
- Response patterns

### 5. Search for Maintenance Discussions

Search for issues about project status:
- WebFetch: `https://github.com/{owner}/{repo}/issues?q=is:issue+maintainer+OR+abandoned+OR+unmaintained+OR+looking+for`
- Look for labels like "help wanted", "seeking maintainer"

### 6. Find Active Forks

Use WebSearch: `{repo} fork active maintained site:github.com`

Check `https://github.com/{owner}/{repo}/network/members` if accessible.

### 7. Check Package Registry (if applicable)

For Python projects: WebFetch `https://pypi.org/project/{package}/`
For Node.js: WebFetch `https://www.npmjs.com/package/{package}`

## Health Assessment Criteria

Generate a status based on these indicators:

### Healthy/Active
- Commits within last 3 months
- Releases within last year
- Issues/PRs being addressed
- Multiple active contributors

### Maintenance Mode (Stable)
- Project explicitly states stable/mature
- Occasional updates for compatibility
- May have slow PR/issue response
- Core features complete

### Stagnant (Concerning)
- No commits in 6+ months
- No releases in 1+ years
- PRs accumulating without review
- Issues unanswered
- Single maintainer gone quiet

### Abandoned
- No commits in 1+ years
- No releases in 2+ years
- Archived flag set
- Issues explicitly asking about status unanswered
- Community forks emerging

## Output Format

Provide a structured report:

```
## Project Status Report: {owner}/{repo}

### Quick Summary
- **Status**: [Healthy | Maintenance Mode | Stagnant | Abandoned]
- **Last Commit**: {date} ({time ago})
- **Last Release**: {version} ({date})
- **Open Issues/PRs**: {issues} / {prs}

### Activity Analysis
{Detailed findings about commit patterns, maintainer activity}

### Community Health
{Discussion activity, contributor diversity, response times}

### Maintenance Concerns (if any)
{List specific red flags found}

### Active Forks / Alternatives
{Any community forks with significant activity}
{Alternative projects if found}

### Recommendation
{Brief actionable advice for the user}
```

## Important Notes

- Always check if project explicitly states it's in maintenance mode (many mature projects are intentionally quiet)
- Distinguish between "abandoned" and "stable/complete"
- Note if the project is used by many dependents (indicates community investment)
- Check if there's a migration path announced
