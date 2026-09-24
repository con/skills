# CON Skills

A collection of [Agent Skills](https://agentskills.io/) for software project maintenance, triage, and automation.

## Included Skills

| Skill | Description |
|-------|-------------|
| [install-apm-skills](skills/install-apm-skills/) | Install reusable APM skills with pinned metadata, ignored deployment, and reproducible setup. |
| [author-apm-skills](skills/author-apm-skills/) | Author and assess reusable skills specifically for APM distribution. |
| [analyze-duplicates](skills/analyze-duplicates/) | Detect code and documentation duplication using jscpd, generate a Markdown report with collapsible `<details>` sections (suitable for GitHub/Gitea issues), and propose a mediation plan with refactoring strategies. |
| [github-project-status](skills/github-project-status/) | Assess whether a GitHub project is healthy, in maintenance mode, stagnant, or abandoned. Checks commits, releases, issues, PRs, forks, and package registries to produce a structured status report. |
| [introduce-codespell](skills/introduce-codespell/) | Add [codespell](https://github.com/codespell-project/codespell) spell-checking to a project end-to-end: config, GitHub Actions workflow, pre-commit hook, exclusion tuning, ambiguous-typo review, and automated fixes via `datalad run`. |
| [introduce-git-bug](skills/introduce-git-bug/) | Set up [git-bug](https://github.com/git-bug/git-bug) distributed issue tracking: configure GitHub bridge, sync issues, push `refs/bugs/*`, and document the workflow in DEVELOPMENT.md / CLAUDE.md. |
| [introduce-reuse-compliance](skills/introduce-reuse-compliance/) | Introduce [REUSE](https://reuse.software/) licensing compliance to a project: `LICENSES/`, `REUSE.toml`, SPDX headers, and integration with tox / pre-commit / Makefile / GitHub Actions. Handles BIDS dataset data-vs-code separation, [DUO](https://github.com/EBISPOT/DUO) data-use ontology codes, and DEP-3 patch tagging for vendoring repos. |
| [issue-triage](skills/issue-triage/) | Triage open GitHub issues by cross-referencing the codebase and git history. Detects duplicates, drafts proposed comments, and serves results in a local web dashboard. Includes Python helper scripts for gathering and serving data. |
| [pr-feedback-review](skills/pr-feedback-review/) | Load a PR's review feedback (human + bot), classify each comment by type and actionability, and recommend what to address vs dismiss — with draft code changes and responses. Works from a local repo or a PR URL. |
| [pr-review-update](skills/pr-review-update/) | Scan an [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard) for PRs awaiting your response, assess confidence, auto-rebase codespell PRs, and produce copy-paste-ready push commands. |
| [scan-projects](skills/scan-projects/) | Walk subdirectories of git repos, collect metadata (language, license, commit dates, remote URL), and generate concise LLM-produced summaries into a `projects.tsv` file. Ships with helper scripts for batch updates. |
| [tinuous-analyzer](skills/tinuous-analyzer/) | Analyze CI log collections gathered by [con/tinuous](https://github.com/con/tinuous/) to pinpoint when a test started failing, diff environment/dependency changes between passing and failing runs, and recommend investigation steps. |

## Installation

Reusable source is developed and tracked in this repository.
Consumer projects track `apm.yml`, `apm.lock.yaml`, and setup metadata; installed copies are Git-ignored.
Skill updates therefore change dependency pins and hashes in the consumer, keeping skill development out of its task history.

Add a tested `apm-cli==0.31.0` development/setup dependency using the consumer's existing environment manager.
From that environment, select a published commit and the skills needed (replace `<commit-sha>` with a full Git SHA):

```console
apm install con/skills#<commit-sha> --skill install-apm-skills --target agent-skills --dry-run
apm install con/skills#<commit-sha> --skill install-apm-skills --target agent-skills
```

The package becomes available from `con/skills` after the packaging PR merges; before that, tests must name the actual fork and commit explicitly.
Use `--target claude` for Claude's native skill directory.
Persist the chosen `targets:` in `apm.yml`, commit the manifest and generated lock, and ignore `/apm_modules/` plus the deployed skill directories recorded in the lock.
Do not ignore whole agent configuration trees that contain project-authored files.

Add an existing-manager setup task that runs `apm install --frozen`, document that task in the consumer README, and add a short `AGENTS.md` instruction to run it before work.
A new checkout restores the environment and runs that task before starting the agent.
First installation needs source/network access; private sources also need credentials. Run `apm audit --ci` after restoration. The [installation skill](skills/install-apm-skills/SKILL.md) includes migration and setup details.
Do not copy, edit, or commit installed skill bodies downstream.

## Developing and checking this collection

Keep each skill's canonical source in `skills/<name>/`.
The root `apm.yml` publishes `skills/` under `includes:`.
APM publishes these directories without a second editable source tree.
Required references, scripts, and assets belong inside the skill.
See [author-apm-skills](skills/author-apm-skills/SKILL.md) for the workflow; its scope is APM distribution, not generic skill creation.

With Python 3.12 and `tox==4.64.1` installed:

```console
tox -e validate,apm,security-static,security-deps
```

- `validate` checks skill metadata and bundled Python syntax/subprocess use.
- `apm` tests the full collection and a selected subset in temporary consumers, metadata-only frozen restoration, integrity audit, and tamper detection.
- `security-static` runs Cisco's skill scanner without an LLM key and fails on HIGH/CRITICAL findings.
- `security-deps` runs pip-audit against the installed APM, scanner, and validation dependency environment for known Python package vulnerabilities.

CI runs these checks on PRs, pushes to `master`, and weekly.
CI uses read-only permissions and needs no model/API credentials. Dependency scanning covers the listed tooling environment, not every external command a skill may invoke; static findings require review and are not proof of safety or skill quality. The optional LLM review proposed in [PR #9](https://github.com/con/skills/pull/9) complements these checks and is not duplicated here.

To verify an exact published revision, use `tox -e apm -- --source owner/repository#<full-commit-sha>` from a matching source checkout.
Package-test organization-policy discovery is explicitly disabled only inside its disposable, policy-free fixtures.

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

Supply project/user configuration when invoking the skill; do not edit installed dependency copies.

### pr-feedback-review

This skill has a `## Configuration` section at the top of its `SKILL.md` with the following variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SCAN_DIRS` | `~/proj` | Comma-separated parent directories to scan for git repos |
| `GITHUB_USER` | `yarikoptic` | Your GitHub username |
| `MAX_SCAN_DEPTH` | `3` | How deep to recurse when scanning for repos |

Supply project/user configuration when invoking the skill; do not edit installed dependency copies.

### Other skills

The remaining skills use runtime discovery (e.g., `git remote -v`, `gh auth status`) and do not require pre-configuration.

## Repo-wide conventions

See [`AGENTS.md`](AGENTS.md) (alias `CLAUDE.md`) for cross-cutting rules that apply to every skill in this collection — most notably the rule that any skill preparing a pull request must respect the upstream project's `PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`.

## License

TBD
