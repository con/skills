# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [analyze-duplicates](skills/analyze-duplicates/) | Detect code and documentation duplication using jscpd, generate a Markdown report with collapsible `<details>` sections (suitable for GitHub/Gitea issues), and propose a mediation plan with refactoring strategies. |
| [author-apm-skills](skills/author-apm-skills/) | Create and maintain portable skills for APM distribution. |
| [bot-pr-sweep](skills/bot-pr-sweep/) | Sweep repositories for open `dependabot[bot]` and `pre-commit-ci[bot]` pull requests, verify authors by account ID, gate on complete and passing CI with a tested stdlib script, squash-merge the green ones guarded by the head SHA (optionally approving the ones branch protection holds back), assign the maintainer, and report the rest. |
| [code-quality-report-conventions](skills/code-quality-report-conventions/) | Shared report conventions read by the `review-*` skills (report location, provenance stamp, evidence rules, security-sensitive findings, re-review, confidence/status labels). Not invoked directly; APM installs it with them. |
| [code-quality-review-awk](skills/code-quality-review-awk/) | AWK guide for `review-repo-code-quality`: which POSIX awk and gawk programs it covers, including programs embedded in shell scripts, Makefiles, and CI steps, and their portability to mawk, BusyBox awk, and the one-true-awk; its tools marked static (parse-only `gawk --lint` and `--dump-variables`, `mawk -W dump`, `shfmt --to-json` to extract embedded programs) or needing execution consent (run-time `gawk --lint`, `gawk --profile`, BusyBox awk and the one-true-awk, tests), awk checks (a closed set spelled as a chain of comparisons becomes one lookup array, gawk features under a POSIX shebang, string and numeric comparison, commands built from data), currency (gawk 5.4, POSIX.1-2024), false positives such as `-v` variables, library functions, and idioms like `!seen[$0]++`, and verification commands. Not invoked directly; APM installs it with `review-repo-code-quality`. |
| [code-quality-review-go](skills/code-quality-review-go/) | Go guide for `review-repo-code-quality`: where a module states its rules, its tools marked static (`gofmt`, `gocyclo`) or needing execution consent (`go vet`, `staticcheck`, `deadcode`, `golangci-lint`), Go checks (typed constants for closed sets, error wrapping, interface placement, `internal/`), false positives such as exported API and build tags, and verification commands. Not invoked directly; APM installs it with `review-repo-code-quality`. |
| [code-quality-review-haskell](skills/code-quality-review-haskell/) | Haskell guide for `review-repo-code-quality`: where a Cabal or Stack project states its rules, its tools marked static (`hlint` with the guide's hint file, `ormolu` or `fourmolu` in check mode, `cabal check` on a copy, `graphmod`) or needing execution consent (anything that builds, since a build runs Template Haskell and preprocessors: GHC warnings, `weeder`, `stan`, tests), Haskell checks (a closed set of strings becomes a sum type deriving `Enum` and `Bounded`, partial functions, missing export lists, orphan instances, `String` for text, laziness), currency (GHC releases, `GHC2024`, Cabal and Stackage versions, archived CI actions), false positives such as exposed modules, Template Haskell names, and `Paths_` modules, and verification commands. Not invoked directly; APM installs it with `review-repo-code-quality`. |
| [code-quality-review-python](skills/code-quality-review-python/) | Python guide for `review-repo-code-quality`: where a project states its rules, its tools marked static (`vulture`, isolated `ruff`) or needing execution consent (the project's linters, type checker, `deptry`, tests), Python checks (a long or growing `Literal` list becomes one `Enum`, import-time effects, cycles, ruff idiom rules), currency (supported Python versions, the PEPs and PyPA packaging standards that come with them, pixi for environments and locks), false positives such as entry points and fixtures, and verification commands. Not invoked directly; APM installs it with `review-repo-code-quality`. |
| [code-quality-review-rust](skills/code-quality-review-rust/) | Rust guide for `review-repo-code-quality`: where a crate or Cargo workspace states its rules, its tools marked static (`rustfmt --check`, `cargo-machete` on a copy, `cargo-audit`) or needing execution consent (anything that compiles or runs `cargo` in the checkout: `cargo check`, `cargo clippy`, `cargo-udeps`, `cargo-hack`, `cargo-deny`, tests), Rust checks (a set of values matched as strings becomes one enum, panics and error types in library code, `pub` wider than needed, settings repeated across a workspace, feature combinations), currency (Rust releases and `rust-version`, editions, `lazy_static` and `once_cell`, archived `actions-rs` actions, RustSec advisories), false positives such as items used only under a feature or `#[cfg(test)]`, a library's `pub` items, and FFI exports, and verification commands. Not invoked directly; APM installs it with `review-repo-code-quality`. |
| [code-quality-review-shell](skills/code-quality-review-shell/) | Shell guide for `review-repo-code-quality`: which POSIX sh and Bash scripts it covers, including shell embedded in CI workflows, its static tools (`shellcheck --norc`, `actionlint`, `hadolint`, `shfmt -d`), shell checks (strict mode, quoting, Bash features under `/bin/sh`, snippets copied between workflows), false positives such as sourced libraries and Bats hooks, and verification commands. Not invoked directly; APM installs it with `review-repo-code-quality`. |
| [code-quality-review-ts](skills/code-quality-review-ts/) | TypeScript and JavaScript guide for `review-repo-code-quality`: where a project states its rules, its tools marked static (`oxlint`, `biome`, `madge` without the project's configuration) or needing execution consent (ESLint, `knip`, `tsc`, tests), checks (a long or growing string-literal union becomes one `as const` list, cycles, promise handling), false positives such as package exports and file-system routes, and verification commands. Not invoked directly; APM installs it with `review-repo-code-quality`. |
| [github-project-status](skills/github-project-status/) | Assess whether a GitHub project is healthy, in maintenance mode, stagnant, or abandoned. Checks commits, releases, issues, PRs, forks, and package registries to produce a structured status report. |
| [install-apm-skills](skills/install-apm-skills/) | Install and update pinned reusable skills with metadata-only consumer setup. |
| [issue-triage](skills/issue-triage/) | Triage open GitHub issues by cross-referencing the codebase and git history. Detects duplicates, drafts proposed comments, and serves results in a local web dashboard. Includes Python helper scripts for gathering and serving data. |
| [pr-feedback-review](skills/pr-feedback-review/) | Load a PR's review feedback (human + bot), classify each comment by type and actionability, and recommend what to address vs dismiss — with draft code changes and responses. Works from a local repo or a PR URL. |
| [pr-review-update](skills/pr-review-update/) | Scan an [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard) for PRs awaiting your response, assess confidence, auto-rebase codespell PRs, and produce copy-paste-ready push commands. |
| [review-human-prose](skills/review-human-prose/) | Revise prose that is difficult to follow or needs a requested clarity review; make actors, actions, and connections explicit while preserving meaning. |
| [review-org-code-quality](skills/review-org-code-quality/) | Audit code health of an organization-wide ecosystem of similarly styled, interconnected data/ML/ETL pipelines: reference pattern, dependency graph, read-only per-repo 0–3 matrix (using only the static tools of the `code-quality-review-<language>` guides), depth reviews of the critical repos via `review-repo-code-quality`, systemic findings, and a prioritized action plan. Writes a dated, version-stamped report to `docs/code-reviews/` in a location the user names. |
| [review-repo-code-quality](skills/review-repo-code-quality/) | Language-agnostic, functionality-preserving code-quality review of a single repository: architecture, dead code, duplication, consolidation, cleanup, currency of versions, standards and tooling, and needs-verification items, each with location, proposed change, safety confidence, and a verification command. Loads a `code-quality-review-<language>` guide for each language the repository uses; house tool preferences (default: the guides', such as pixi) are set per run. Writes a dated, version-stamped report to `docs/code-reviews/`. |
| [scan-projects](skills/scan-projects/) | Walk subdirectories of git repos, collect metadata (language, license, commit dates, remote URL), and generate concise LLM-produced summaries into a `projects.tsv` file. Ships with helper scripts for batch updates. |
| [setup-chromatic](skills/setup-chromatic/) | Set up [Chromatic](https://www.chromatic.com) visual regression testing for a web app with two feeds: Storybook stories (component states) and Playwright snapshots (whole-page states, several viewports). Covers configs, the GitHub Actions workflows (built without a token, uploaded from the default branch, so forks' pull requests get snapshots and merges become the baseline), two Chromatic projects, and the README section explaining them. |
| [setup-codespell](skills/setup-codespell/) | Add [codespell](https://github.com/codespell-project/codespell) spell-checking to a project end-to-end: config, GitHub Actions workflow, pre-commit hook, exclusion tuning, ambiguous-typo review, and automated fixes via `datalad run`. |
| [setup-duplicates-analysis](skills/setup-duplicates-analysis/) | Make [jscpd](https://github.com/kucherenko/jscpd) code/text duplication checking part of a project's workflow: `.jscpd.json`, a pre-commit hook or tox env / pixi task / Makefile target / npm script, CI wiring, then refactor duplicates (using `analyze-duplicates` reports) and tighten the threshold until clean. |
| [setup-git-bug](skills/setup-git-bug/) | Set up [git-bug](https://github.com/git-bug/git-bug) distributed issue tracking: configure GitHub bridge, sync issues, push `refs/bugs/*`, and document the workflow in DEVELOPMENT.md / CLAUDE.md. |
| [setup-intuit-auto](skills/setup-intuit-auto/) | Set up automated releases with [intuit/auto](https://intuit.github.io/auto/): `.autorc`, GitHub Actions release workflow, GitHub labels (optional prefix to avoid dependabot clashes), CHANGELOG transition, and release docs for Python/PyPI, JS/npm, or pure GitHub releases. |
| [setup-reuse-compliance](skills/setup-reuse-compliance/) | Set up [REUSE](https://reuse.software/) licensing compliance in a project: `LICENSES/`, `REUSE.toml`, SPDX headers, and integration with tox / pre-commit / Makefile / GitHub Actions. Handles BIDS dataset data-vs-code separation, [DUO](https://github.com/EBISPOT/DUO) data-use ontology codes, and DEP-3 patch tagging for vendoring repos. |
| [suggest-skill-fixes](skills/suggest-skill-fixes/) | Shared, optional procedure that other skills read at the end of a run: when the run showed the skill falling short, report suggested fixes to it, and in an attended run of a skill installed from `con/skills`, ask before preparing a pull request there. Not invoked directly; install alongside the skills that use it. |
| [tinuous-analyzer](skills/tinuous-analyzer/) | Analyze CI log collections gathered by [con/tinuous](https://github.com/con/tinuous/) to pinpoint when a test started failing, diff environment/dependency changes between passing and failing runs, and recommend investigation steps. |

## Getting started

Install [install-apm-skills](skills/install-apm-skills/SKILL.md) once at user scope so your agent can use it across projects.
With APM installed:

```console
apm install --global con/skills/skills/install-apm-skills --target agent-skills
```

This installs the installer skill in `~/.agents/skills/`.
Reload your agent if needed, then ask it:

> Use install-apm-skills to install tinuous-analyzer from con/skills into this project.

Or install at project scope from the project directory, pinning a reviewed commit: `apm install con/skills/skills/tinuous-analyzer#<full-commit-SHA> --target agent-skills`.

Each skill is its own APM package (`skills/<name>/apm.yml` carries its version), so `apm.lock.yaml` and `apm deps list` show which version of each skill a project has.
A skill that needs another one from this collection declares it as a dependency, and APM installs it with the skill.
Install individual skills only; `con/skills` is a monorepo of independent skills, not a package to install as a whole.

The installer uses APM to select and install skills, record their commit and content hashes, ignore downloaded skill directories, and verify restoration.
Projects track `apm.yml`, `apm.lock.yaml`, and setup instructions—not the installed skills themselves.
It also supports other APM-compatible sources and user-level installations.
For configuration options, see each skill’s `SKILL.md` (for example, [pr-review-update](skills/pr-review-update/SKILL.md#configuration) and [pr-feedback-review](skills/pr-feedback-review/SKILL.md#configuration)); supply values in your request rather than editing installed copies.

## Development

Skill sources live in `skills/<name>/`, each with its own `apm.yml`.
Versioning is described in [`AGENTS.md`](AGENTS.md#skill-versions).
See [author-apm-skills](skills/author-apm-skills/SKILL.md) for authoring and validation guidance.
Run `tox -e validate,apm,reuse,security-static,security-deps` before submitting changes (environment requirements are in `tox.ini`).
`pre-commit install` adds the [REUSE](https://reuse.software/) licensing check and the check that each `apm.yml` `license` matches it as commit hooks.
CI checks skill structure, package restoration, licensing, and security; passing checks do not guarantee safety.

## Repo-wide conventions

See [`AGENTS.md`](AGENTS.md) (alias `CLAUDE.md`) for cross-cutting rules that apply to every skill in this collection — most notably the rule that any skill preparing a pull request must respect the upstream project's `PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`.

## License

MIT; see [`LICENSE`](LICENSE). Per-file terms follow [REUSE](https://reuse.software/) (`REUSE.toml`, `LICENSES/`), and each skill's `apm.yml` declares its license and credits the skill's authors.
Material quoted from other sources, such as the CRediT role definitions abridged in [credit-contributions](skills/credit-contributions/CREDIT_ROLES.md), keeps its source's terms.
