# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [analyze-duplicates](skills/analyze-duplicates/) | Detect code and documentation duplication using jscpd, generate a Markdown report with collapsible `<details>` sections (suitable for GitHub/Gitea issues), and propose a mediation plan with refactoring strategies. |
| [author-apm-skills](skills/author-apm-skills/) | Create and maintain portable skills for APM distribution. |
| [code-quality-report-conventions](skills/code-quality-report-conventions/) | Shared report conventions read by the `review-*` skills (report location, provenance stamp, evidence rules, security-sensitive findings, re-review, confidence/status labels). Not invoked directly; install alongside them. |
| [github-project-status](skills/github-project-status/) | Assess whether a GitHub project is healthy, in maintenance mode, stagnant, or abandoned. Checks commits, releases, issues, PRs, forks, and package registries to produce a structured status report. |
| [install-apm-skills](skills/install-apm-skills/) | Install and update pinned reusable skills with metadata-only consumer setup. |
| [introduce-codespell](skills/introduce-codespell/) | Add [codespell](https://github.com/codespell-project/codespell) spell-checking to a project end-to-end: config, GitHub Actions workflow, pre-commit hook, exclusion tuning, ambiguous-typo review, and automated fixes via `datalad run`. |
| [introduce-git-bug](skills/introduce-git-bug/) | Set up [git-bug](https://github.com/git-bug/git-bug) distributed issue tracking: configure GitHub bridge, sync issues, push `refs/bugs/*`, and document the workflow in DEVELOPMENT.md / CLAUDE.md. |
| [introduce-reuse-compliance](skills/introduce-reuse-compliance/) | Introduce [REUSE](https://reuse.software/) licensing compliance to a project: `LICENSES/`, `REUSE.toml`, SPDX headers, and integration with tox / pre-commit / Makefile / GitHub Actions. Handles BIDS dataset data-vs-code separation, [DUO](https://github.com/EBISPOT/DUO) data-use ontology codes, and DEP-3 patch tagging for vendoring repos. |
| [issue-triage](skills/issue-triage/) | Triage open GitHub issues by cross-referencing the codebase and git history. Detects duplicates, drafts proposed comments, and serves results in a local web dashboard. Includes Python helper scripts for gathering and serving data. |
| [pr-feedback-review](skills/pr-feedback-review/) | Load a PR's review feedback (human + bot), classify each comment by type and actionability, and recommend what to address vs dismiss — with draft code changes and responses. Works from a local repo or a PR URL. |
| [pr-review-update](skills/pr-review-update/) | Scan an [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard) for PRs awaiting your response, assess confidence, auto-rebase codespell PRs, and produce copy-paste-ready push commands. |
| [review-org-code-quality](skills/review-org-code-quality/) | Audit code health of an organization-wide ecosystem of similarly styled, interconnected data/ML/ETL pipelines: reference pattern, dependency graph, read-only per-repo 0–3 matrix, depth reviews of the critical repos via `review-repo-code-quality`, systemic findings, and a prioritized action plan. Writes a dated, version-stamped report to `docs/code-reviews/` in a location the user names. |
| [review-repo-code-quality](skills/review-repo-code-quality/) | Functionality-preserving code-quality review of a single repository: dead code, duplication, consolidation, cleanup, and needs-verification items, each with location, proposed change, safety confidence, and a verification command. Writes a dated, version-stamped report to `docs/code-reviews/`. |
| [scan-projects](skills/scan-projects/) | Walk subdirectories of git repos, collect metadata (language, license, commit dates, remote URL), and generate concise LLM-produced summaries into a `projects.tsv` file. Ships with helper scripts for batch updates. |
| [setup-chromatic](skills/setup-chromatic/) | Set up [Chromatic](https://www.chromatic.com) visual regression testing for a web app with two feeds: Storybook stories (component states) and Playwright snapshots (whole-page states, several viewports). Covers configs, two GitHub Actions workflows, two Chromatic projects, and the README section explaining them. |
| [tinuous-analyzer](skills/tinuous-analyzer/) | Analyze CI log collections gathered by [con/tinuous](https://github.com/con/tinuous/) to pinpoint when a test started failing, diff environment/dependency changes between passing and failing runs, and recommend investigation steps. |

## Getting started

Install [install-apm-skills](skills/install-apm-skills/SKILL.md) once at user scope so your agent can use it across projects.
With APM installed:

```console
apm install --global con/skills --skill install-apm-skills --target agent-skills
```

This installs the installer skill in `~/.agents/skills/`.
Reload your agent if needed, then ask it:

> Use install-apm-skills to install introduce-codespell from con/skills into this project.

Or run manually from any project directory: `apm install con/skills --skill introduce-codespell --target agent-skills`.

The installer uses APM to select and install skills, record their commit and content hashes, ignore downloaded skill directories, and verify restoration.
Projects track `apm.yml`, `apm.lock.yaml`, and setup instructions—not the installed skills themselves.
It also supports other APM-compatible sources and user-level installations.
Provide any skill-specific configuration in your request rather than editing installed copies.

## Development

Skill sources live in `skills/`.
See [author-apm-skills](skills/author-apm-skills/SKILL.md) for authoring and validation guidance.
CI checks skill structure, package restoration, and security; passing checks do not guarantee safety.

## Repo-wide conventions

See [`AGENTS.md`](AGENTS.md) (alias `CLAUDE.md`) for cross-cutting rules that apply to every skill in this collection — most notably the rule that any skill preparing a pull request must respect the upstream project's `PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`.

## License

TBD
