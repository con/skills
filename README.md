# CON Skills

A collection of [Claude Code Agent Skills](https://agentskills.io/) for software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [analyze-duplicates](skills/analyze-duplicates/) | Detect code and documentation duplication using jscpd, generate a Markdown report with collapsible `<details>` sections (suitable for GitHub/Gitea issues), and propose a mediation plan with refactoring strategies. |
| [author-apm-skills](skills/author-apm-skills/) | Create and maintain portable skills for APM distribution. |
| [bisect-and-patch-git-annex](skills/bisect-and-patch-git-annex/) | Bisect git-annex regressions using [con/tinuous](https://github.com/con/tinuous/) CI logs, create reproducers, generate fix patches, and submit Red/Green PRs to datalad/git-annex. |
| [bot-pr-sweep](skills/bot-pr-sweep/) | Sweep repositories for open `dependabot[bot]` and `pre-commit-ci[bot]` pull requests, verify authors by account ID, gate on complete and passing CI with a tested stdlib script, squash-merge the green ones guarded by the head SHA (optionally approving the ones branch protection holds back), assign the maintainer, and report the rest. |
| [code-quality-report-conventions](skills/code-quality-report-conventions/) | Shared report conventions read by the `review-*` skills (report location, provenance stamp, evidence rules, security-sensitive findings, re-review, confidence/status labels). Not invoked directly; APM installs it with them. |
| [credit-contributions](skills/credit-contributions/) | Annotate a paper with [CRediT](https://credit.niso.org/) author contributions: keep them in a `.tributors.credit.yaml` overlay (compatible with con/tributors), render the "Author Contributions" section in LaTeX or Markdown, emit JATS XML, and render the `\author{}` byline with affiliations. |
| [github-project-status](skills/github-project-status/) | Assess whether a GitHub project is healthy, in maintenance mode, stagnant, or abandoned. Checks commits, releases, issues, PRs, forks, and package registries to produce a structured status report. |
| [install-apm-skills](skills/install-apm-skills/) | Install and update pinned reusable skills with metadata-only consumer setup. |
| [issue-triage](skills/issue-triage/) | Triage open GitHub issues by cross-referencing the codebase and git history. Detects duplicates, drafts proposed comments, and serves results in a local web dashboard. Includes Python helper scripts for gathering and serving data. |
| [make-scriv-changelog](skills/make-scriv-changelog/) | Create a [scriv](https://scriv.readthedocs.io/) changelog fragment in `changelog.d/` following the project's conventions. |
| [pr-feedback-review](skills/pr-feedback-review/) | Load a PR's review feedback (human + bot), classify each comment by type and actionability, and recommend what to address vs dismiss — with draft code changes and responses. Works from a local repo or a PR URL. |
| [pr-review-update](skills/pr-review-update/) | Scan an [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard) for PRs awaiting your response, assess confidence, auto-rebase codespell PRs, and produce copy-paste-ready push commands. |
| [review-human-prose](skills/review-human-prose/) | Revise prose that is difficult to follow or needs a requested clarity review; make actors, actions, and connections explicit while preserving meaning. |
| [review-org-code-quality](skills/review-org-code-quality/) | Audit code health of an organization-wide ecosystem of similarly styled, interconnected data/ML/ETL pipelines: reference pattern, dependency graph, read-only per-repo 0–3 matrix, depth reviews of the critical repos via `review-repo-code-quality`, systemic findings, and a prioritized action plan. Writes a dated, version-stamped report to `docs/code-reviews/` in a location the user names. |
| [review-repo-code-quality](skills/review-repo-code-quality/) | Functionality-preserving code-quality review of a single repository: dead code, duplication, consolidation, cleanup, and needs-verification items, each with location, proposed change, safety confidence, and a verification command. Writes a dated, version-stamped report to `docs/code-reviews/`. |
| [scan-projects](skills/scan-projects/) | Walk subdirectories of git repos, collect metadata (language, license, commit dates, remote URL), and generate concise LLM-produced summaries into a `projects.tsv` file. Ships with helper scripts for batch updates. |
| [setup-chromatic](skills/setup-chromatic/) | Set up [Chromatic](https://www.chromatic.com) visual regression testing for a web app with two feeds: Storybook stories (component states) and Playwright snapshots (whole-page states, several viewports). Covers configs, the GitHub Actions workflows (built without a token, uploaded from the default branch, so forks' pull requests get snapshots and merges become the baseline), two Chromatic projects, and the README section explaining them. |
| [setup-codespell](skills/setup-codespell/) | Add [codespell](https://github.com/codespell-project/codespell) spell-checking to a project end-to-end: config, GitHub Actions workflow, pre-commit hook, exclusion tuning, ambiguous-typo review, and automated fixes via `datalad run`. |
| [setup-duplicates-analysis](skills/setup-duplicates-analysis/) | Make [jscpd](https://github.com/kucherenko/jscpd) code/text duplication checking part of a project's workflow: `.jscpd.json`, a pre-commit hook or tox env / pixi task / Makefile target / npm script, CI wiring, then refactor duplicates (using `analyze-duplicates` reports) and tighten the threshold until clean. |
| [setup-git-bug](skills/setup-git-bug/) | Set up [git-bug](https://github.com/git-bug/git-bug) distributed issue tracking: configure GitHub bridge, sync issues, push `refs/bugs/*`, and document the workflow in DEVELOPMENT.md / CLAUDE.md. |
| [setup-intuit-auto](skills/setup-intuit-auto/) | Set up automated releases with [intuit/auto](https://intuit.github.io/auto/): `.autorc`, GitHub Actions release workflow, GitHub labels (optional prefix to avoid dependabot clashes), CHANGELOG transition, and release docs for Python/PyPI, JS/npm, or pure GitHub releases. |
| [setup-reuse-compliance](skills/setup-reuse-compliance/) | Set up [REUSE](https://reuse.software/) licensing compliance in a project: `LICENSES/`, `REUSE.toml`, SPDX headers, and integration with tox / pre-commit / Makefile / GitHub Actions. Handles BIDS dataset data-vs-code separation, [DUO](https://github.com/EBISPOT/DUO) data-use ontology codes, and DEP-3 patch tagging for vendoring repos. |
| [skill-security-review](skills/skill-security-review/) | Security audit of a skill directory: reads `SKILL.md` and bundled scripts, and checks for prompt-injection vectors, capability mismatch, dangerous permissions, exfiltration patterns, and unsafe subprocess use. Emits a structured report. |
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

## Claude Code plugins

This repository is also a Claude Code [plugin marketplace](https://code.claude.com/docs/en/discover-plugins), `con-skills` ([`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)).
Each plugin installs a group of the skills above:

| Plugin | For |
|--------|-----|
| `con-common` | Skills the other plugins build on |
| `con-code-quality` | Code-quality reviews of a repository or an organization |
| `con-project-setup` | Setting up project tooling |
| `con-maintenance` | Pull requests, issues, changelogs and CI regressions |
| `con-skill-authoring` | Writing, installing and security-reviewing skills |
| `con-writing` | Papers and prose |

[`marketplace.json`](.claude-plugin/marketplace.json) lists each plugin's skills.
`con-code-quality` and `con-project-setup` use skills from `con-common`, which is installed with them.
In a Claude Code 2.1.275 or later session, install the plugins you want in one step:

```text
/plugin install con-common --marketplace con/skills
/plugin install con-code-quality --marketplace con/skills
/plugin install con-project-setup --marketplace con/skills
/plugin install con-maintenance --marketplace con/skills
/plugin install con-skill-authoring --marketplace con/skills
/plugin install con-writing --marketplace con/skills
```

In older versions, add the marketplace first (`/plugin marketplace add con/skills`), then install by name (`/plugin install con-code-quality@con-skills`).
A plugin's skills are named after it, for example `/con-code-quality:review-repo-code-quality`.

The plugins declare no version, so every commit to `master` is a new version.
Auto-update is off for third-party marketplaces: turn it on for `con-skills` in `/plugin` (Marketplaces tab), or update a plugin with `claude plugin update con-code-quality@con-skills`.
A plugin install records nothing in your project; use APM (above) when a project should pin the skills it uses.

In Claude Code on the web, neither plugins installed on your computer nor marketplaces declared in a repository's settings are added to a session.
Add the marketplace or its plugins to your claude.ai account at [claude.ai/customize/plugins](https://claude.ai/customize/plugins), including `con-common` with `con-code-quality` or `con-project-setup`, and start a new session.

## Codex

Codex reads skills from `.agents/skills/` in a repository and from `~/.agents/skills/`, where APM's `--target agent-skills` installs them, so the APM instructions above work for Codex unchanged.
Codex can also install the plugins above from this repository's Claude Code marketplace (tested with Codex CLI 0.172.0):

```console
codex plugin marketplace add con/skills
codex plugin add con-common@con-skills
codex plugin add con-code-quality@con-skills
```

Codex does not install a plugin's `dependencies`, so add `con-common` yourself with `con-code-quality` or `con-project-setup`.
Mention a skill with `$` and its listed name, for example `$con-code-quality:review-repo-code-quality`.
Codex ignores the Claude Code frontmatter fields `allowed-tools` and `user-invocable`: its sandbox and approval settings decide what a skill may run, and helper skills such as `code-quality-report-conventions` appear in its skill list.
The skills were written for Claude Code, so a step that names a Claude Code tool, such as `AskUserQuestion`, may need a nudge. `issue-triage` keeps its state under `.git/`, which Codex's sandbox keeps read-only.

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
