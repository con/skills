# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [analyze-duplicates](analyze-duplicates/) | Detect code and documentation duplication using jscpd, generate a Markdown report with collapsible `<details>` sections (suitable for GitHub/Gitea issues), and propose a mediation plan with refactoring strategies. |
| [assess-alignment-with-stamped-principles](skills/assess-alignment-with-stamped-principles/) | Assess a project, dataset or analysis against the [STAMPED principles](https://github.com/stamped-principles/stamped-paper) and leave a filled checklist behind: a dated report, a response JSON with per-item evidence, and a link that opens the answers in the [checklist app](https://checklist.stamped-principles.org/). Read-only; ships eleven scripted probes over committed state. |
| [code-quality-report-conventions](code-quality-report-conventions/) | Shared report conventions read by the `review-*` skills (report location, provenance stamp, evidence rules, security-sensitive findings, re-review, confidence/status labels). Not invoked directly; install alongside them. |
| [align-with-stamped-principles](skills/align-with-stamped-principles/) | Assess, repair scoped workflow gaps using the existing stack, and reassess with the same rubric. |
| [create-stamped-project](skills/create-stamped-project/) | Create the smallest executable research object with versioned inputs, an environment/replay route and tested delivery; preserve existing prepared projects. |
| [create-repronim-stamped-project](skills/create-repronim-stamped-project/) | Adapt project creation to ReproNim, BIDS-aware inputs and community neuroimaging workflows. |
| [datalad-annex](skills/datalad-annex/) | Preserve native DataLad records, test native rerun, and verify delivery of annex content and requested task logs. |
| [do-full-research-loop](skills/do-full-research-loop/) | Carry a study through protocol, inspected pilot, bounded batches, useful figures, scientific checks, fresh replay and a separate STAMPED assessment. |
| [entire-worktrees](skills/entire-worktrees/) | Prepare native capture and verify session identity across branches, worktrees, clones and delegated children. |
| [pixi-with-stamped](skills/pixi-with-stamped/) | Declare dependencies and actionable tasks, retain the chosen environment identity, and verify fresh replay. |
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

## STAMPED working branch

This branch builds on [Yarik's PR #26](https://github.com/con/skills/pull/26) at `4fe5d7be82ed6c297747e8b838031aec88e75903`, retaining its probes, templates and checklist format.
The research protocol, ReproNim adapter, scientific validation and comparison guidance incorporate the [first research skill bundle](https://github.com/con/skills/tree/8f3acaa4a7c353b6c8ea6928c278478f95328fc5) and its [compressed revisions](https://github.com/con/skills/tree/e31edc77078b78c9ce415bd41dc9e7e98de451b4).
The linked skills above include the working research workflow and common Pixi, DataLad/annex and Entire guidance; assessment is pinned separately by projects that compare evolving skill conditions. A [blind workflow trial](evals/stamped/blind-runs/2026-10-15-pixi-native/) retains a completed known-answer analysis, its exact instruction snapshot, observed friction and independently checked delivery/replay evidence.

## Installation

Copy or symlink the desired skill directories into `~/.claude/skills/`, or point your Claude Code configuration to this repository.

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

## Tests

Structural lint of every skill, and the STAMPED probe tests and mutant calibration:

```console
git submodule update --init evals   # the STAMPED eval harness and run records
tox -e validate        # frontmatter, size budgets, duplicate blocks, bundled Python
tox -e stamped-evals   # pytest over the probes + the defect-mutant calibration
```

Tests live outside the skill directories, under `evals/`, so a skill ships its instructions and scripts without its test suite.
For the STAMPED skills that directory is a **submodule**: the [`stamped-evals`](https://github.com/con/skills/tree/stamped-evals) branch of this same repository, which carries the graders, the fixtures, the defect mutants and the record of every blind run.
It is a branch rather than a second repository so the work stays self-contained, and a submodule rather than a directory because the records are append-only and were 85% of the diff that introduced the skills.

## Repo-wide conventions

See [`AGENTS.md`](AGENTS.md) (alias `CLAUDE.md`) for cross-cutting rules that apply to every skill in this collection — most notably the rule that any skill preparing a pull request must respect the upstream project's `PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`.

## License

TBD
