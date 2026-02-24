# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for
software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [github-project-status](github-project-status/) | Assess whether a GitHub project is healthy, in maintenance mode, stagnant, or abandoned. Checks commits, releases, issues, PRs, forks, and package registries to produce a structured status report. |
| [introduce-codespell](introduce-codespell/) | Add [codespell](https://github.com/codespell-project/codespell) spell-checking to a project end-to-end: config, GitHub Actions workflow, pre-commit hook, exclusion tuning, ambiguous-typo review, and automated fixes via `datalad run`. |
| [introduce-git-bug](introduce-git-bug/) | Set up [git-bug](https://github.com/git-bug/git-bug) distributed issue tracking: configure GitHub bridge, sync issues, push `refs/bugs/*`, and document the workflow in DEVELOPMENT.md / CLAUDE.md. |
| [issue-triage](issue-triage/) | Triage open GitHub issues by cross-referencing the codebase and git history. Detects duplicates, drafts proposed comments, and serves results in a local web dashboard. Includes Python helper scripts for gathering and serving data. |
| [pr-review-update](pr-review-update/) | Scan an [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard) for PRs awaiting your response, assess confidence, auto-rebase codespell PRs, and produce copy-paste-ready push commands. |
| [scan-projects](scan-projects/) | Walk subdirectories of git repos, collect metadata (language, license, commit dates, remote URL), and generate concise LLM-produced summaries into a `projects.tsv` file. Ships with helper scripts for batch updates. |
| [tinuous-analyzer](tinuous-analyzer/) | Analyze CI log collections gathered by [con/tinuous](https://github.com/con/tinuous/) to pinpoint when a test started failing, diff environment/dependency changes between passing and failing runs, and recommend investigation steps. |

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
