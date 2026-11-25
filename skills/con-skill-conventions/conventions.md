## Respect the target project's conventions

Before making a choice the target project will see, look for the project's own answer and use it instead of the skill's default:

- configuration the project already has for the tool, such as a `.jscpd.json` threshold, a `.codespellrc`, or a `[tool.*]` section in `pyproject.toml`;
- repository settings that limit the action, such as which merge methods are allowed;
- the project's contribution rules: pull request template, contribution guide, branch and commit style (see below).

Commit messages, sign-off, and AI-attribution trailers such as `Co-Authored-By` follow the user's or the project's conventions; do not invent a format.

Users customize a skill in their agent instruction files (`CLAUDE.md` / `AGENTS.md`, user-level or in the project), for example in a section named after the skill (`## setup-codespell`).
Those instructions override both the project's configuration and the skill's defaults; a request in the conversation overrides all of them.

If nothing answers the question, use the skill's default and tell the user it was a default.
If a source above disagrees with the skill's default, follow the source and say so.

## Respect upstream PR conventions when preparing a pull request

Any skill that prepares a pull request (currently: `setup-chromatic`,
`setup-codespell`, `setup-duplicates-analysis`, `setup-git-bug`,
`setup-intuit-auto`, `setup-reuse-compliance`, plus any future skill that
does the same) MUST, before drafting the PR body and BEFORE handing the
user a `gh pr create` / push command, perform the steps below and report
the result to the user.

### 1. Use PR description templates if they exist

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
