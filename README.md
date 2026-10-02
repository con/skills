# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [analyze-duplicates](analyze-duplicates/) | Detect code and documentation duplication using jscpd, generate a Markdown report with collapsible `<details>` sections (suitable for GitHub/Gitea issues), and propose a mediation plan with refactoring strategies. |
| [github-project-status](github-project-status/) | Assess whether a GitHub project is healthy, in maintenance mode, stagnant, or abandoned. Checks commits, releases, issues, PRs, forks, and package registries to produce a structured status report. |
| [introduce-codespell](introduce-codespell/) | Add [codespell](https://github.com/codespell-project/codespell) spell-checking to a project end-to-end: config, GitHub Actions workflow, pre-commit hook, exclusion tuning, ambiguous-typo review, and automated fixes via `datalad run`. |
| [introduce-git-bug](introduce-git-bug/) | Set up [git-bug](https://github.com/git-bug/git-bug) distributed issue tracking: configure GitHub bridge, sync issues, push `refs/bugs/*`, and document the workflow in DEVELOPMENT.md / CLAUDE.md. |
| [introduce-reuse-compliance](introduce-reuse-compliance/) | Introduce [REUSE](https://reuse.software/) licensing compliance to a project: `LICENSES/`, `REUSE.toml`, SPDX headers, and integration with tox / pre-commit / Makefile / GitHub Actions. Handles BIDS dataset data-vs-code separation, [DUO](https://github.com/EBISPOT/DUO) data-use ontology codes, and DEP-3 patch tagging for vendoring repos. |
| [issue-triage](issue-triage/) | Triage open GitHub issues by cross-referencing the codebase and git history. Detects duplicates, drafts proposed comments, and serves results in a local web dashboard. Includes Python helper scripts for gathering and serving data. |
| [pr-feedback-review](pr-feedback-review/) | Load a PR's review feedback (human + bot), classify each comment by type and actionability, and recommend what to address vs dismiss — with draft code changes and responses. Works from a local repo or a PR URL. |
| [pr-review-update](pr-review-update/) | Scan an [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard) for PRs awaiting your response, assess confidence, auto-rebase codespell PRs, and produce copy-paste-ready push commands. |
| [scan-projects](scan-projects/) | Walk subdirectories of git repos, collect metadata (language, license, commit dates, remote URL), and generate concise LLM-produced summaries into a `projects.tsv` file. Ships with helper scripts for batch updates. |
| [tinuous-analyzer](tinuous-analyzer/) | Analyze CI log collections gathered by [con/tinuous](https://github.com/con/tinuous/) to pinpoint when a test started failing, diff environment/dependency changes between passing and failing runs, and recommend investigation steps. |

## Installation

Copy or symlink the desired skill directories into `~/.claude/skills/`, or point your Claude Code configuration to this repository.

## Automated checks

With Python 3.12 and `tox==4.64.1` installed, run:

```console
tox -e validate,security-static,security-deps
```

CI runs these checks on pull requests, pushes to `master`, and weekly, using read-only permissions and pinned tools/actions. No model credentials are needed. The structural validator checks skill metadata and bundled Python recursively. Cisco's static skill scanner fails on HIGH/CRITICAL findings.
`pip-audit` checks the installed validation/scanner dependency environment for known Python vulnerabilities; it does not cover every external command a skill can invoke.
Review lower-severity findings too; passing scans do not prove a skill is safe.

The existing `tox -e security-llm` command remains available for explicitly configured local LLM review.
It is not run on untrusted PR content with CI credentials, and these static checks do not replace it.
The driver requires a Claude CLI supporting `--bare`, `--tools`, and `--setting-sources` (older CLIs fail closed).
It sends UTF-8 snapshots to the model with no built-in or MCP tools, no discovered hooks/skills/configuration, and a temporary working directory outside the candidate tree.
Use a trusted CLI installation and managed policy; these controls do not isolate a compromised launcher or host.
Only the model API credential and basic process environment are forwarded; unrelated credentials are omitted.
`SECURITY_CMD` is a trusted launcher override that must forward stdin and honor every appended security flag; wrappers that ignore them are unsupported.
Use a trusted checkout of the driver and its canonical review skill, passing candidate directories as arguments.
Do not execute the candidate checkout's own driver to audit it.
Snapshots reject symlinks, special files, binary content, more than 256 files, or more than 512,000 bytes, rather than silently reviewing a subset.
Keep candidate trees unchanged during capture.
Failed processes and malformed, unknown, or duplicate verdicts return status 2.
Findings at `FAIL_ON` levels return 1; a completed review below the threshold returns 0.
A tool-free model can still be fooled into an inaccurate verdict; reviews are advisory and are not a sandbox or proof of safety.
See the [Claude CLI reference](https://code.claude.com/docs/en/cli-reference) for the tool and bare-mode controls.

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

Edit the defaults in `pr-review-update/SKILL.md` to match your setup.

### pr-feedback-review

This skill has a `## Configuration` section at the top of its `SKILL.md` with the following variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SCAN_DIRS` | `~/proj` | Comma-separated parent directories to scan for git repos |
| `GITHUB_USER` | `yarikoptic` | Your GitHub username |
| `MAX_SCAN_DEPTH` | `3` | How deep to recurse when scanning for repos |

Edit the defaults in `pr-feedback-review/SKILL.md` to match your setup.

### Other skills

The remaining skills use runtime discovery (e.g., `git remote -v`, `gh auth status`) and do not require pre-configuration.

## Repo-wide conventions

See [`AGENTS.md`](AGENTS.md) (alias `CLAUDE.md`) for cross-cutting rules that apply to every skill in this collection — most notably the rule that any skill preparing a pull request must respect the upstream project's `PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`.

## License

TBD
