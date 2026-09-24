---
description: Create a scriv changelog fragment in changelog.d/ following project conventions
---

# Make scriv changelog entry

Create a changelog fragment under `changelog.d/` for the current branch's changes.

## Steps

1. Read `changelog.d/scriv.ini` (or `[tool.scriv]` in `pyproject.toml`) to understand the scriv configuration (categories, format, template).
2. Read the fragment template — check `changelog.d/templates/new_fragment.md.j2` or the scriv config's `new_fragment_template` setting.
3. Read a few existing fragments in `changelog.d/*.md` (not scriv.ini) to match the established style.
4. Examine the current branch's commits (vs the base branch) via `git log` and `git diff` to understand what changed.
5. Determine the appropriate category from the scriv config (e.g. Bug Fixes, Enhancements, etc.).
6. Generate the filename in scriv's format: `changelog.d/YYYYMMDD_HHMMSS_author_slug.md`
   - Use the current date/time
   - Use the git user name (from `git config user.name`, lowercased, spaces to underscores) as author
   - Use a short slug derived from the change description
7. Write the fragment with exactly one uncommented category section, following the style of existing fragments.
8. If a PR number is provided or can be guessed (as the next number after existing issue and PR numbers), include it. If an issue number is referenced in commits, include it.
9. Show the created file to the user for review.

## Important

- Only ONE category section should be uncommented in the fragment
- Follow the exact link format from the template (typically `[#NNN](https://github.com/ORG/REPO/issues/NNN)`) — infer org/repo from `git remote get-url origin`
- Match the tone and style of existing fragments (concise, user-facing description)
- The user may provide `$ARGUMENTS` with hints like PR number or description
