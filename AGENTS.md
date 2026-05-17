# Repo-wide conventions for skills in this collection

These rules apply to **every skill** in this repository. When authoring or
modifying a skill, ensure its instructions enforce them — and when a skill
is currently running, treat them as part of the skill's contract even if
the SKILL.md does not repeat them verbatim.

> Note for tooling: this file is named `AGENTS.md` for generic agent
> tooling. `CLAUDE.md` is a symlink to it so Claude Code picks it up
> automatically when working inside this repo.

---

## Respect upstream PR conventions when preparing a pull request

Any skill that prepares a pull request (currently:
`introduce-codespell`, `introduce-git-bug`, `introduce-reuse-compliance`,
plus any future skill that does the same) MUST, before drafting the PR
body and BEFORE handing the user a `gh pr create` / push command, perform
the steps below and report the result to the user.

### 1. Look for a PR description template

Check, in this order, and use the first one that exists:

- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/pull_request_template.md`
- `.github/PULL_REQUEST_TEMPLATE/*.md` (multiple templates — pick the one
  whose filename best matches the change, or ask the user)
- `docs/PULL_REQUEST_TEMPLATE.md`
- `PULL_REQUEST_TEMPLATE.md` at repo root
- For Codeberg / Forgejo / Gitea: the same names under `.gitea/`,
  `.forgejo/`, or repo root
- For GitLab: `.gitlab/merge_request_templates/*.md`

If a template is found:

- **Use it as the skeleton** for the PR body. Preserve its section
  headings (often `Title ----` underlined, or `## Heading`), reproduce
  any prose under each heading from the template (the placeholder
  text in `<!-- ... -->` HTML comments is guidance — read it, then
  remove the comments and write the actual content).
- **Fill out every section adequately.** Empty sections look like
  the contributor didn't read the template. If a section truly does
  not apply (e.g. "Linked issue" when there is none), say so
  explicitly (`N/A — no prior issue, this is a small bugfix.`)
  rather than deleting the heading.
- **Tick checklist items truthfully.** Only check `[x]` boxes for
  things actually done; leave unchecked items as `[ ]` so the
  maintainer sees what is outstanding. Common ones include:
  - tests added
  - documentation updated
  - changelog entry added (e.g. restic's `changelog/unreleased/`,
    scriv's `changelog.d/`, towncrier's `news/`, keep-a-changelog
    `CHANGELOG.md`)
  - DCO / sign-off
  - "ready for review" gate
- If the template references a contribution guide URL, follow that
  link's instructions as well (see step 2).

If no template is found, fall back to the skill's default PR body — but
still inform the user that no template was present.

### 2. Read CONTRIBUTING.md (and friends) and follow it

Check for these files at the repo root and in `docs/`:

- `CONTRIBUTING.md` / `CONTRIBUTING.rst` / `CONTRIBUTING`
- `.github/CONTRIBUTING.md`
- `DEVELOPMENT.md`, `HACKING.md`, `docs/development/`

If present, scan for and honor at minimum:

- **Branch naming** conventions (e.g. `enh-`, `fix-`, `feature/`)
- **Commit message** style (e.g. terse first-line summary,
  Conventional Commits, sign-off requirement, capitalization)
- **Changelog** requirements — many projects mandate a new file in
  a specific directory with a specific format (restic's
  `changelog/unreleased/issue-NNNN` and `changelog/TEMPLATE`, towncrier's
  `news/`, scriv's `changelog.d/`, keep-a-changelog edits to
  `CHANGELOG.md`). If required and missing, add it as part of the
  PR work — do not just check the box in the template.
- **Issue-first policy** — some projects (restic among them) require
  an issue or forum discussion before a non-trivial PR. If the rule
  applies to the change at hand, surface that to the user before
  pushing, and either link an existing discussion or recommend
  opening one first.
- **Linting / formatting** gates (e.g. `gofmt`, `ruff format`,
  `golangci-lint`) — run them before the final commit.
- **Maintainer-edits checkbox** — when the project's template asks
  the user to enable "allow edits from maintainers", remind the user
  to tick it in the GitHub PR UI (skills can't toggle that flag via
  `gh`).

### 3. Inform the user

Before handing over the push / `gh pr create` command, include in the
status report to the user:

- **Template:** which template file was found (or that none was found),
  and that the PR body now follows it.
- **CONTRIBUTING.md:** which guide was found (or that none was found),
  and a one-line summary of any contributor-facing requirements that
  shaped the PR (e.g. "added `changelog/unreleased/pull-NNNN` per
  CONTRIBUTING § Providing Patches", or "branch named `enh-codespell`
  to match the repo's existing `enh-*` convention").
- **Outstanding items the user must do manually**, e.g. enabling
  maintainer edits in the web UI, or linking the PR number back into
  the changelog file once GitHub assigns it.

### 4. When updating an existing PR description

The same rules apply to amending a PR body via `gh pr edit
--body-file`. If a PR was created before the template was respected
(e.g. earlier sessions, or before this convention existed), the skill
should — when next touched — offer to rewrite the PR body to the
template, *preserving* any maintainer dialogue that already happened
in PR comments (those live in comments, not in the body, so a body
rewrite is safe).

---

## Other repo-wide conventions

(Add new cross-cutting rules here as they emerge. Skill-specific rules
belong in the individual `SKILL.md` files.)
