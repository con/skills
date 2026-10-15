# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for
software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [analyze-duplicates](analyze-duplicates/) | Detect code and documentation duplication using jscpd, generate a Markdown report with collapsible `<details>` sections (suitable for GitHub/Gitea issues), and propose a mediation plan with refactoring strategies. |
| [assess-alignment-with-stamped-principles](skills/assess-alignment-with-stamped-principles/) | Assess a project, dataset or analysis against the [STAMPED principles](https://github.com/stamped-principles/stamped-paper) and leave a filled checklist behind: a dated report, a response JSON with per-item evidence, and a link that opens the answers in the [checklist app](https://checklist.stamped-principles.org/). Read-only; ships eleven scripted probes over committed state. |
| [code-quality-report-conventions](code-quality-report-conventions/) | Shared report conventions read by the `review-*` skills (report location, provenance stamp, evidence rules, security-sensitive findings, re-review, confidence/status labels). Not invoked directly; install alongside them. |
| [align-with-stamped-principles](skills/align-with-stamped-principles/) | Align an existing project with [STAMPED](https://github.com/stamped-principles/stamped-paper): assess it, then write a proportionate STAMPED section into its own `AGENTS.md`/`CLAUDE.md` and install executable guards (a pre-commit guard against committing during a recorded run, a preflight check, a CI rerun job), then re-assess. |
| [create-stamped-project](skills/create-stamped-project/) | Start a new research project that satisfies the STAMPED principles from its first commit: inputs linked as modules, a pinned environment, a recorded execution mechanism, the guards that keep them true, and a README a stranger can follow. Hands off to `align-with-stamped-principles`. |
| [do-full-research-loop](skills/do-full-research-loop/) | Carry a study through to results inside a STAMPED project — plan, pilot, batches with QC, aggregate, controls, independent review, write-up, and a closing assessment. Deliberately quick and dirty; not a virtual scientist. |
| [github-project-status](github-project-status/) | Assess whether a GitHub project is healthy, in maintenance mode, stagnant, or abandoned. Checks commits, releases, issues, PRs, forks, and package registries to produce a structured status report. |
| [introduce-codespell](introduce-codespell/) | Add [codespell](https://github.com/codespell-project/codespell) spell-checking to a project end-to-end: config, GitHub Actions workflow, pre-commit hook, exclusion tuning, ambiguous-typo review, and automated fixes via `datalad run`. |
| [introduce-git-bug](introduce-git-bug/) | Set up [git-bug](https://github.com/git-bug/git-bug) distributed issue tracking: configure GitHub bridge, sync issues, push `refs/bugs/*`, and document the workflow in DEVELOPMENT.md / CLAUDE.md. |
| [introduce-reuse-compliance](introduce-reuse-compliance/) | Introduce [REUSE](https://reuse.software/) licensing compliance to a project: `LICENSES/`, `REUSE.toml`, SPDX headers, and integration with tox / pre-commit / Makefile / GitHub Actions. Handles BIDS dataset data-vs-code separation, [DUO](https://github.com/EBISPOT/DUO) data-use ontology codes, and DEP-3 patch tagging for vendoring repos. |
| [issue-triage](issue-triage/) | Triage open GitHub issues by cross-referencing the codebase and git history. Detects duplicates, drafts proposed comments, and serves results in a local web dashboard. Includes Python helper scripts for gathering and serving data. |
| [pr-feedback-review](pr-feedback-review/) | Load a PR's review feedback (human + bot), classify each comment by type and actionability, and recommend what to address vs dismiss — with draft code changes and responses. Works from a local repo or a PR URL. |
| [pr-review-update](pr-review-update/) | Scan an [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard) for PRs awaiting your response, assess confidence, auto-rebase codespell PRs, and produce copy-paste-ready push commands. |
| [review-org-code-quality](review-org-code-quality/) | Audit code health of an organization-wide ecosystem of similarly styled, interconnected data/ML/ETL pipelines: reference pattern, dependency graph, read-only per-repo 0–3 matrix, depth reviews of the critical repos via `review-repo-code-quality`, systemic findings, and a prioritized action plan. Writes a dated, version-stamped report to `docs/code-reviews/` in a location the user names. |
| [review-repo-code-quality](review-repo-code-quality/) | Functionality-preserving code-quality review of a single repository: dead code, duplication, consolidation, cleanup, and needs-verification items, each with location, proposed change, safety confidence, and a verification command. Writes a dated, version-stamped report to `docs/code-reviews/`. |
| [scan-projects](scan-projects/) | Walk subdirectories of git repos, collect metadata (language, license, commit dates, remote URL), and generate concise LLM-produced summaries into a `projects.tsv` file. Ships with helper scripts for batch updates. |
| [setup-chromatic](setup-chromatic/) | Set up [Chromatic](https://www.chromatic.com) visual regression testing for a web app with two feeds: Storybook stories (component states) and Playwright snapshots (whole-page states, several viewports). Covers configs, two GitHub Actions workflows, two Chromatic projects, and the README section explaining them. |
| [stamped-conventions](skills/stamped-conventions/) | Shared conventions for the STAMPED skills (not invoked directly): the checklist pinned at 0.3.1 with a vendoring lock, the verdict vocabulary, the response/report format and its URL encoder, project kinds, and the per-stack references. |
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

### pr-feedback-review

This skill has a `## Configuration` section at the top of its `SKILL.md`
with the following variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SCAN_DIRS` | `~/proj` | Comma-separated parent directories to scan for git repos |
| `GITHUB_USER` | `yarikoptic` | Your GitHub username |
| `MAX_SCAN_DEPTH` | `3` | How deep to recurse when scanning for repos |

Edit the defaults in `pr-feedback-review/SKILL.md` to match your setup.

### Other skills

The remaining skills use runtime discovery (e.g., `git remote -v`,
`gh auth status`) and do not require pre-configuration.

## Tests

Structural lint of every skill, and the STAMPED probe tests and mutant
calibration:

```console
tox -e validate        # frontmatter, size budgets, duplicate blocks, bundled Python
tox -e stamped-evals   # pytest over the probes + the defect-mutant calibration
```

Tests live outside the skill directories, under
[`evals/`](evals/stamped/README.md), so a skill ships its instructions and
scripts without its test suite.

## Repo-wide conventions

See [`AGENTS.md`](AGENTS.md) (alias `CLAUDE.md`) for cross-cutting rules
that apply to every skill in this collection — most notably the rule
that any skill preparing a pull request must respect the upstream
project's `PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`.

## License

TBD
