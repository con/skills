# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [analyze-duplicates](skills/analyze-duplicates/) | Detect code and documentation duplication using jscpd, generate a Markdown report with collapsible `<details>` sections (suitable for GitHub/Gitea issues), and propose a mediation plan with refactoring strategies. |
| [author-apm-skills](skills/author-apm-skills/) | Create and maintain portable skills for APM distribution. |
| [github-project-status](skills/github-project-status/) | Assess whether a GitHub project is healthy, in maintenance mode, stagnant, or abandoned. Checks commits, releases, issues, PRs, forks, and package registries to produce a structured status report. |
| [install-apm-skills](skills/install-apm-skills/) | Install and update pinned reusable skills with metadata-only consumer setup. |
| [introduce-codespell](skills/introduce-codespell/) | Add [codespell](https://github.com/codespell-project/codespell) spell-checking to a project end-to-end: config, GitHub Actions workflow, pre-commit hook, exclusion tuning, ambiguous-typo review, and automated fixes via `datalad run`. |
| [introduce-git-bug](skills/introduce-git-bug/) | Set up [git-bug](https://github.com/git-bug/git-bug) distributed issue tracking: configure GitHub bridge, sync issues, push `refs/bugs/*`, and document the workflow in DEVELOPMENT.md / CLAUDE.md. |
| [introduce-reuse-compliance](skills/introduce-reuse-compliance/) | Introduce [REUSE](https://reuse.software/) licensing compliance to a project: `LICENSES/`, `REUSE.toml`, SPDX headers, and integration with tox / pre-commit / Makefile / GitHub Actions. Handles BIDS dataset data-vs-code separation, [DUO](https://github.com/EBISPOT/DUO) data-use ontology codes, and DEP-3 patch tagging for vendoring repos. |
| [issue-triage](skills/issue-triage/) | Triage open GitHub issues by cross-referencing the codebase and git history. Detects duplicates, drafts proposed comments, and serves results in a local web dashboard. Includes Python helper scripts for gathering and serving data. |
| [pr-feedback-review](skills/pr-feedback-review/) | Load a PR's review feedback (human + bot), classify each comment by type and actionability, and recommend what to address vs dismiss — with draft code changes and responses. Works from a local repo or a PR URL. |
| [pr-review-update](skills/pr-review-update/) | Scan an [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard) for PRs awaiting your response, assess confidence, auto-rebase codespell PRs, and produce copy-paste-ready push commands. |
| [scan-projects](skills/scan-projects/) | Walk subdirectories of git repos, collect metadata (language, license, commit dates, remote URL), and generate concise LLM-produced summaries into a `projects.tsv` file. Ships with helper scripts for batch updates. |
| [tinuous-analyzer](skills/tinuous-analyzer/) | Analyze CI log collections gathered by [con/tinuous](https://github.com/con/tinuous/) to pinpoint when a test started failing, diff environment/dependency changes between passing and failing runs, and recommend investigation steps. |

## Installation

Use APM for reproducible installation. Pin the tested `apm-cli` version from
`[testenv:apm]` in `tox.ini` through your existing environment manager.
Replace FULL_COMMIT_SHA with a reviewed, published 40-hex commit:

```console
apm install con/skills#FULL_COMMIT_SHA --skill install-apm-skills --target agent-skills --dry-run
apm install con/skills#FULL_COMMIT_SHA --skill install-apm-skills --target agent-skills
apm install --frozen
apm audit --ci
```

Track the manifest, lock, environment/setup files and concise agent guidance.
Ignore `apm_modules/` and the specific deployed skill directories; keep native
project skills tracked. See [consumer setup](skills/install-apm-skills/references/consumer-setup.md).

The collection uses `skills/` so the tested APM version can install selected
skills through one package manifest. A root `includes` list of the former
arbitrary top-level directories did not deploy them in our installation test.
Individual per-skill packages worked, but require separate manifests and package
coordinates. The directory moves keep one collection package and leave existing
skill content unchanged; they are isolated in a separate commit for review.

## Automated checks

With Python 3.12 and `tox==4.64.1` installed, run:

```console
tox -e validate,apm,security-static,security-deps
```

CI runs these checks on pull requests, pushes to `master`, and weekly, using read-only permissions and pinned tools/actions. No model credentials are needed. The structural validator checks skill metadata and bundled Python recursively. Cisco's static skill scanner fails on HIGH/CRITICAL findings.
`pip-audit` checks the installed APM/validation/scanner dependency environment for known Python vulnerabilities; it does not cover every external command a skill can invoke.
Review lower-severity findings too; passing scans do not prove a skill is safe.

Optional local review: `tox -e security-llm` requires Claude Code 2.1.248+ and authentication.
The runner restricts tools to Read/Glob/Grep and file access to the reviewed directory, disables discovered customizations and MCP, and is excluded from CI.
Use a trusted driver, CLI installation, and `SECURITY_CMD` launcher that honors these restrictions; model verdicts remain advisory.

The APM check installs this collection into a disposable consumer, restores its
metadata in a fresh directory, and checks the installed resources and audit.
To verify the documented Git installation path and a selected subset after
publishing a commit, run:

```console
tox -e apm -- --source con/skills#FULL_COMMIT_SHA
```

Use the actual fork coordinate when the revision is not published in con/skills.
Pull-request CI runs this Git check against the published PR head as well.

## Configuration

Some skills require user-specific configuration.
Following the [Agent Skills specification](https://agentskills.io/specification), configuration is handled via documented variables in each skill's `SKILL.md` rather than environment variables or config files — the Claude agent reads these values and substitutes them at runtime.

### pr-review-update

This skill has a `## Configuration` section at the top of its `SKILL.md` with the following variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_DIR` | `~/proj/improveit-dashboard` | Path to improveit-dashboard checkout |
| `REPOS_DIR` | `~/proj/misc` | Directory where PR repos are cloned |
| `GITHUB_USER` | `yarikoptic` | Your GitHub username |
| `FORK_REMOTE` | `gh-yarikoptic` | Git remote name for your fork |

Edit the defaults in `skills/pr-review-update/SKILL.md` to match your setup.

### pr-feedback-review

This skill has a `## Configuration` section at the top of its `SKILL.md` with the following variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SCAN_DIRS` | `~/proj` | Comma-separated parent directories to scan for git repos |
| `GITHUB_USER` | `yarikoptic` | Your GitHub username |
| `MAX_SCAN_DEPTH` | `3` | How deep to recurse when scanning for repos |

Edit the defaults in `skills/pr-feedback-review/SKILL.md` to match your setup.

### Other skills

The remaining skills use runtime discovery (e.g., `git remote -v`, `gh auth status`) and do not require pre-configuration.

## Repo-wide conventions

See [`AGENTS.md`](AGENTS.md) (alias `CLAUDE.md`) for cross-cutting rules that apply to every skill in this collection — most notably the rule that any skill preparing a pull request must respect the upstream project's `PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`.

## License

TBD
