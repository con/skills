# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for
software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [github-project-status](github-project-status/) | Check health and maintenance status of a GitHub project. Analyzes commit history, releases, issues, PRs, and searches for active forks or community discussions. |
| [introduce-codespell](introduce-codespell/) | Introduce codespell spell-checking to a project. Creates branch, config file, GitHub Actions workflow, and pre-commit hook. |
| [introduce-git-bug](introduce-git-bug/) | Introduce git-bug distributed issue tracking to a git project. Configures GitHub bridge, syncs issues, and documents workflow. |
| [issue-triage](issue-triage/) | Triage open GitHub issues by cross-referencing against codebase and git history. Includes a web-based dashboard. |
| [pr-review-update](pr-review-update/) | Review dashboard PRs needing your response and generate high-confidence update proposals. |
| [scan-projects](scan-projects/) | Scan git repository subdirectories and create/update a `projects.tsv` with metadata and LLM-generated summaries. |
| [tinuous-analyzer](tinuous-analyzer/) | Analyze [con/tinuous](https://github.com/con/tinuous/) CI log collections to identify test regressions and compare successful vs failing runs. |

## Installation

Copy or symlink the desired skill directories into `~/.claude/skills/`, or
point your Claude Code configuration to this repository.

## Configuration

Some skills require user-specific configuration. Following the
[Agent Skills specification](https://agentskills.io/specification),
configuration is handled via documented variables in each skill's
`SKILL.md` rather than environment variables or config files — the
Claude agent reads these values and substitutes them at runtime.

### pr-review-update

This skill has a `## Configuration` section at the top of its `SKILL.md`
with the following variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_DIR` | `~/proj/improveit-dashboard` | Path to improveit-dashboard checkout |
| `REPOS_DIR` | `~/proj/misc` | Directory where PR repos are cloned |
| `GITHUB_USER` | `yarikoptic` | Your GitHub username |
| `FORK_REMOTE` | `gh-yarikoptic` | Git remote name for your fork |

Edit the defaults in `pr-review-update/SKILL.md` to match your setup.

### Other skills

The remaining skills use runtime discovery (e.g., `git remote -v`,
`gh auth status`) and do not require pre-configuration.

## License

TBD
