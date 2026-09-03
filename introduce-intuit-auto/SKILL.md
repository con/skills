---
name: introduce-intuit-auto
description: Introduce automated releases using intuit/auto to a project. Creates .autorc, GitHub Actions release workflow, GitHub labels (with optional prefix to avoid dependabot conflicts), CHANGELOG transition, and release documentation. Use when setting up auto-release for GitHub projects (Python/PyPI, JS/npm, or pure GitHub releases).
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# Introduce intuit/auto for Automated Releases

Set up [intuit/auto](https://intuit.github.io/auto/) release automation in a project:
create the `.autorc` config, GitHub Actions release workflow, GitHub labels, CHANGELOG
transition, and release-process documentation.

## When to Use

- User wants to automate releases (tagging, changelog, PyPI/npm upload)
- User mentions "auto", "intuit/auto", or "automated releases"
- User asks to "introduce auto-release" or "/introduce-intuit-auto"

## Prerequisites

- `gh` CLI available and authenticated (user's own credentials)
- Git repository with a GitHub remote
- Python `build` + `twine` for PyPI uploads (Python projects only)
- `auto` binary (downloaded during workflow setup, not required locally)

## Commit Co-Authorship

All commits MUST include a `Co-Authored-By` trailer. Get the version via `claude --version`.
Format: `Co-Authored-By: Claude Code <VERSION> / Claude <MODEL> <noreply@anthropic.com>`

Write all commit messages to `.git-meta/COMMIT_MSG` and use `git commit -F .git-meta/COMMIT_MSG`.

---

## Step 0: Check Existing Configuration

Before creating anything, check if auto is already set up:

```bash
ls .autorc .autorc.json .autorc.yml 2>/dev/null
ls .github/workflows/release.yml .github/workflows/auto-release.yml 2>/dev/null
grep -r "intuit/auto\|auto shipit\|auto version" .github/workflows/ 2>/dev/null | head -5
```

If auto is already configured, review the existing setup and offer to update it rather than
replace it wholesale.

### Detect Project Type

```bash
# Python/PyPI?
ls pyproject.toml setup.py setup.cfg 2>/dev/null

# JavaScript/npm?
ls package.json 2>/dev/null

# Check GitHub remote (for label creation)
git remote -v | grep github.com
```

### Detect Base Branch and Version Scheme

```bash
# Base branch
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|.*/||'
# or
git remote show origin 2>/dev/null | grep 'HEAD branch'

# Existing version tags — detect prefix (v1.0.0 vs 1.0.0)
git tag --sort=-v:refname | head -5
```

---

## Step 1: Ask User for Configuration

Ask the following questions (or infer from context if clear):

### 1.1 Label Prefix

The standard auto labels (`major`, `minor`, `patch`) conflict with Dependabot's PR labels
of the same name — Dependabot adds `major`/`minor`/`patch` labels to its own PRs,
which would trigger accidental auto releases.

Offer choices:
- **`release-` prefix** (recommended): labels become `release-major`, `release-minor`,
  `release-patch`, `release`. Avoids all Dependabot conflicts.
- **No prefix**: standard labels `major`, `minor`, `patch`. Simpler but requires
  disabling Dependabot labels or careful `onlyPublishWithReleaseLabel: true` config.
- **Custom prefix**: e.g., `ver-`, `bump-`, etc.

### 1.2 PyPI Upload

If `pyproject.toml` / `setup.py` exists:
- Should the release workflow upload to PyPI? (yes/no)
- Does the project use `hatch-vcs` / `setuptools-scm` for versioning?
  (if so, version comes from git tags — auto creates them, no version-file edits needed)

### 1.3 GitHub Release Token

Two options for the `GH_TOKEN` secret:
- **Fine-grained PAT** (recommended): needs `contents: write`, `pull-requests: write`
- **Classic PAT with `repo` scope**

If using `protected-branch` plugin (branch protection rules): needs additional
`workflow` scope and a second `PROTECTED_BRANCH_REVIEWER_TOKEN` with admin rights.

### 1.4 `onlyPublishWithReleaseLabel`

When `true`, a release is only cut when a PR explicitly carries the `release` label.
When `false`, any PR with a version-bump label (`major`/`minor`/`patch`) triggers a release.

Recommended: `true` (gives more control, prevents accidental releases).

---

## Step 2: Create `.autorc`

Write `.autorc` to the repo root (JSON format — auto reads it automatically).

### 2.1 Base Template

```json
{
  "baseBranch": "<DETECTED_BASE_BRANCH>",
  "noVersionPrefix": <true_if_tags_have_no_v_prefix>,
  "onlyPublishWithReleaseLabel": true,
  "plugins": [
    "git-tag",
    "released"
  ],
  "labels": [
    {
      "name": "<PREFIX>major",
      "releaseType": "major",
      "changelogTitle": "💥 Breaking Change",
      "description": "Increment the major version when merged",
      "color": "C5000B"
    },
    {
      "name": "<PREFIX>minor",
      "releaseType": "minor",
      "changelogTitle": "🚀 Enhancement",
      "description": "Increment the minor version when merged",
      "color": "F1A60E"
    },
    {
      "name": "<PREFIX>patch",
      "releaseType": "patch",
      "changelogTitle": "🐛 Bug Fix",
      "description": "Increment the patch version when merged",
      "color": "870048"
    },
    {
      "name": "release",
      "releaseType": "release",
      "description": "Create a release when this PR is merged",
      "color": "16a34a"
    },
    {
      "name": "skip-release",
      "releaseType": "skip",
      "description": "Preserve the current version when merged",
      "color": "bf5416"
    },
    {
      "name": "internal",
      "releaseType": "none",
      "changelogTitle": "🏠 Internal",
      "description": "Changes only affect the internal API",
      "color": "696969"
    },
    {
      "name": "documentation",
      "releaseType": "none",
      "changelogTitle": "📝 Documentation",
      "description": "Changes only affect the documentation",
      "color": "cfd3d7"
    },
    {
      "name": "tests",
      "releaseType": "none",
      "changelogTitle": "🧪 Tests",
      "description": "Add or improve existing tests",
      "color": "e4e669"
    },
    {
      "name": "performance",
      "releaseType": "patch",
      "changelogTitle": "🏎 Performance",
      "description": "Improve performance of an existing feature",
      "color": "f4b2d8"
    },
    {
      "name": "released",
      "releaseType": "released",
      "description": "This PR has been released",
      "color": "84cc16"
    }
  ]
}
```

### 2.2 Add PyPI Upload (Python projects)

If publishing to PyPI, add the `exec` plugin **before** `released`:

```json
["exec", {
  "afterRelease": "python -m build && twine upload dist/*"
}]
```

Full `plugins` array with PyPI:
```json
"plugins": [
  "git-tag",
  ["exec", {"afterRelease": "python -m build && twine upload dist/*"}],
  "released"
]
```

### 2.3 Protected Branch Plugin (optional)

If branch protection rules require a PR even for the auto release commit, add:
```json
"plugins": ["protected-branch", "git-tag", ...]
```

This requires a `PROTECTED_BRANCH_REVIEWER_TOKEN` secret with admin rights.

### 2.4 `noVersionPrefix` Detection

```bash
# If most recent tag starts with v: noVersionPrefix = false (keep v)
# If most recent tag has no v:    noVersionPrefix = true  (no v)
git describe --tags --abbrev=0 2>/dev/null | head -1
```

**Always emit this field explicitly.** Omitting `noVersionPrefix` from `.autorc` is NOT
equivalent to `false` — auto's default strips the `v` prefix, producing `0.14.0` instead
of `v0.14.0`. If the project uses `v`-prefixed tags (the common case), set
`"noVersionPrefix": false` explicitly so the intent is clear and cannot silently break
if auto's default ever changes.

---

## Step 3: Create GitHub Actions Release Workflow

Create `.github/workflows/release.yml`:

### 3.1 Detect auto Version to Pin

Find the latest stable v11.x release:
```bash
# Check GitHub releases (requires gh auth)
gh release list --repo intuit/auto --limit 10
```

Pin to a specific version, not `latest`, for reproducibility. Do not hardcode a version
in this skill — find the current latest via the command above at time of setup.

### 3.2 Workflow Template (Python/PyPI)

```yaml
name: Release

on:
  push:
    branches: [<BASE_BRANCH>]

jobs:
  release:
    name: Release
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, 'ci skip') && !contains(github.event.head_commit.message, 'skip ci')"

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GH_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: pip install build twine

      - name: Download auto
        run: |
          curl -fsSL https://github.com/intuit/auto/releases/download/<AUTO_VERSION>/auto-linux.gz \
            | gunzip > ~/auto
          chmod a+x ~/auto

      - name: Create release
        env:
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: ~/auto shipit
```

### 3.3 Workflow Template (JS/npm)

```yaml
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          registry-url: "https://registry.npmjs.org"

      - name: Install dependencies
        run: npm ci

      - name: Create release
        env:
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npx auto shipit
```

### 3.4 Workflow Template (GitHub release only, no package upload)

```yaml
      - name: Create release
        env:
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
        run: ~/auto shipit
```

### 3.5 Inspect existing workflow conventions

Check existing workflows for pinning conventions (SHA vs tag):
```bash
grep 'uses:' .github/workflows/*.yml 2>/dev/null | head -10
```

If existing workflows pin to full SHA (`actions/checkout@abc123...`), do the same for
the release workflow. Copy the `actions/checkout` SHA from an existing workflow rather
than resolving it fresh.

---

## Step 4: CHANGELOG Transition

intuit/auto generates changelog entries in its own emoji-based format:

```
# v1.2.0 (2026-09-03)

#### 🚀 Enhancement
- Feature description [#42](link) (@author)

#### 🐛 Bug Fix
- Fix description [#41](link) (@author)

#### Authors: 2
- Alice (@alice)
- Bob (@bob)
```

This differs from the common "Keep a Changelog" format. Handle the transition:

### 4.1 If No Existing CHANGELOG.md

Create a minimal placeholder:
```markdown
# Changelog

<!-- auto will prepend new release entries above this line -->
```

### 4.2 If Existing "Keep a Changelog" CHANGELOG.md

**Do NOT delete existing content.** Add a transition header at the top:

```markdown
# Changelog

<!-- Entries below v<FIRST_AUTO_VERSION> use Keep a Changelog format. -->
<!-- Entries from v<FIRST_AUTO_VERSION> onward are auto-generated by intuit/auto. -->

```

**Important: handle the `[Unreleased]` section.** auto does not read or consume a
Keep-a-Changelog `## [Unreleased]` block — it will prepend its generated entry directly
after the `# Changelog` title, leaving the old `[Unreleased]` block orphaned between the
new auto entry and the previous versioned entries. Remove or close the `[Unreleased]`
section before the first auto release:
- If it is empty or trivial, delete it.
- If it has valuable hand-written notes, move them into a pending PR description or
  commit message (they will be picked up by auto's PR-metadata scanning), then delete
  the block from CHANGELOG.md.

### 4.3 If Existing auto-format CHANGELOG.md

No changes needed — auto will prepend to the existing file.

---

## Step 5: Create/Update Release Documentation

Add a "Release Process" section to `CONTRIBUTING.md` (create it if it doesn't exist)
or `DEVELOPMENT.md` (whichever exists, or the more appropriate one).

### 5.1 Template for Release Documentation

````markdown
## Release Process

Releases are automated via [intuit/auto](https://intuit.github.io/auto/).
Every PR merged to `<BASE_BRANCH>` is evaluated; a new release is cut when the merged
PR carries one or more of these labels:

| Label             | Version bump | When to use                                    |
| ----------------- | ------------ | ---------------------------------------------- |
| `<PREFIX>major`   | X.0.0        | Breaking API changes                           |
| `<PREFIX>minor`   | 0.X.0        | New backward-compatible features               |
| `<PREFIX>patch`   | 0.0.X        | Bug fixes, docs, minor improvements            |
| `release`         | (trigger)    | Required alongside a bump label to cut release |
| `skip-release`    | (none)       | Merge without triggering a release             |

A release is only created when the merged PR has **both** a version-bump label and the
`release` label (controlled by `onlyPublishWithReleaseLabel` in `.autorc`).

### First-Time Setup (maintainers)

1. Create GitHub labels: run `auto create-labels` or use the `gh` commands in
   `.github/workflows/release.yml` comments.
2. Add secrets to the repository (Settings → Secrets and variables → Actions):
   - `GH_TOKEN`: a PAT with `contents: write` and `pull-requests: write` scopes
   - `PYPI_TOKEN`: a PyPI API token scoped to this project (Python projects only)
   - `PROTECTED_BRANCH_REVIEWER_TOKEN`: PAT with admin rights (only if branch protection
     rules require a reviewer for the auto commit)

### Cutting a Release

1. Merge a PR that has the `release` label plus a version-bump label.
2. The `Release` GitHub Actions workflow triggers automatically.
3. auto calculates the next version, updates `CHANGELOG.md`, creates a git tag,
   publishes a GitHub Release, and (for Python) uploads to PyPI.
4. The `released` label is applied to all PRs included in this release, and a comment
   with the release version is posted on each.

### If Automated Release Fails

auto is robust but occasionally fails. Common causes and fixes:

**GitHub API / token issues:**
- Symptom: `Error: Resource not accessible by integration`
- Fix: Verify `GH_TOKEN` secret is set and the PAT has `contents: write` +
  `pull-requests: write` scopes. Re-run the failed workflow after updating the secret.

**CHANGELOG too large (GitHub release body limit):**
- Symptom: `422 Unprocessable Entity` or `RequestError: body is too long` in the
  release step.
- Fix: Manually create the release via `gh release create vX.Y.Z --notes "See CHANGELOG.md"`,
  then push the updated `CHANGELOG.md` commit that auto staged but didn't push.
  Alternatively, trim old CHANGELOG entries into a separate `CHANGELOG-archive.md`.

**PyPI upload fails (Python):**
- Symptom: `twine upload` error in the `Create release` step.
- Fix: The git tag and GitHub Release are already created. Run manually:
  `python -m build && twine upload dist/*` (with `TWINE_USERNAME=__token__` and
  `TWINE_PASSWORD=<pypi-token>`).
- Check if `PYPI_TOKEN` secret is set and scoped to this project.

**Protected branch blocks auto's commit:**
- Symptom: `remote: error: GH006: Protected branch update failed`
- Fix: Add the `protected-branch` plugin to `.autorc` and set up a
  `PROTECTED_BRANCH_REVIEWER_TOKEN` secret with admin rights, **or** temporarily
  exempt the `github-actions` bot from branch protection rules.

**Duplicate release / tag already exists:**
- Symptom: `fatal: tag 'vX.Y.Z' already exists`
- Fix: Delete the duplicate tag locally and on GitHub before re-running:
  `git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`

**Dry-run to preview what auto would do (without releasing):**
```bash
~/auto version   # prints next version that would be created
~/auto changelog # prints changelog diff that would be prepended
```

### Manual Release (bypass auto)

If auto is broken or unavailable:

```bash
# 1. Decide version
NEW_VERSION=X.Y.Z

# 2. Update CHANGELOG.md manually, commit
git commit -am "chore: release $NEW_VERSION"

# 3. Tag and push
git tag "v$NEW_VERSION"
git push origin master "v$NEW_VERSION"

# 4. Create GitHub release
gh release create "v$NEW_VERSION" --title "v$NEW_VERSION" --notes-file CHANGELOG_snippet.md

# 5. Upload to PyPI (Python)
python -m build && twine upload dist/*
```
````

---

## Step 6: Create GitHub Labels

Create the labels defined in `.autorc` using `gh`. This requires the user's own GitHub
authentication (do NOT use Claude's read-only token in any scripts).

### 6.1 Label Creation Script

Write a helper script `.github/create-labels.sh` (or provide as a one-shot command block
for the user to copy-paste):

```bash
#!/bin/bash
# Create intuit/auto release labels.
# Run once per repository: bash .github/create-labels.sh
# Requires: gh auth login (your own GitHub account)
set -euo pipefail

REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
echo "Creating labels for $REPO ..."

create_label() {
  local name=$1 color=$2 description=$3
  gh label create "$name" --color "$color" --description "$description" \
    --repo "$REPO" --force
}

create_label "<PREFIX>major"  "e11d48" "Increment the major version when merged"
create_label "<PREFIX>minor"  "7c3aed" "Increment the minor version when merged"
create_label "<PREFIX>patch"  "0284c7" "Increment the patch version when merged"
create_label "release"        "16a34a" "Create a release when this PR is merged"
create_label "skip-release"   "6b7280" "Do not create a release for this PR"
create_label "released"       "84cc16" "This PR has been released"

echo "Done. Labels created/updated."
```

Note: `--force` updates existing labels rather than erroring on conflicts.

### 6.2 Creating Labels Now (if `gh` is authenticated)

If the user wants labels created immediately (not just via the script):

```bash
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
gh label create "<PREFIX>major" --color "e11d48" --description "Increment the major version when merged" --repo "$REPO" --force
gh label create "<PREFIX>minor" --color "7c3aed" --description "Increment the minor version when merged" --repo "$REPO" --force
gh label create "<PREFIX>patch" --color "0284c7" --description "Increment the patch version when merged" --repo "$REPO" --force
gh label create "release"       --color "16a34a" --description "Create a release when this PR is merged" --repo "$REPO" --force
gh label create "skip-release"  --color "6b7280" --description "Do not create a release for this PR" --repo "$REPO" --force
gh label create "released"      --color "84cc16" --description "This PR has been released" --repo "$REPO" --force
```

---

## Step 7: Commit and Prepare PR

### 7.1 Commit Order

Commit in logical chunks (one concern per commit):

1. `feat(release): add intuit/auto configuration (.autorc)`
2. `feat(release): add GitHub Actions release workflow`
3. `feat(release): add label creation script`
4. `docs: add release process documentation to CONTRIBUTING.md`
5. `chore: prepare CHANGELOG.md for auto-managed entries` (if CHANGELOG needs editing)

### 7.2 PR Body Template

Write to `.git-meta/PR_BODY.md`:

```markdown
## Summary

Introduces [intuit/auto](https://intuit.github.io/auto/) for automated releases.

- `.autorc`: configures git-tag + exec (PyPI upload) + released plugins, using
  `<PREFIX>major`/`<PREFIX>minor`/`<PREFIX>patch` labels (prefixed to avoid conflicts
  with Dependabot's own `major`/`minor`/`patch` labels)
- `.github/workflows/release.yml`: triggers on every push to `<BASE_BRANCH>`;
  calls `auto shipit` which cuts the release only when the merged PR has both
  a version-bump label and the `release` label
- `CONTRIBUTING.md`: documents labels, how to cut a release, and how to recover
  from common failure modes

## Manual Steps After Merge

- [ ] Add `GH_TOKEN` secret (PAT: `contents: write`, `pull-requests: write`)
- [ ] Add `PYPI_TOKEN` secret (PyPI API token scoped to this project) ← Python only
- [ ] Run `bash .github/create-labels.sh` to create GitHub labels
- [ ] (Optional) Enable branch protection bypass for `github-actions` bot, or add
      `protected-branch` plugin + `PROTECTED_BRANCH_REVIEWER_TOKEN` if needed

## Test plan

- [ ] After merge, open a test PR, add `<PREFIX>patch` + `release` labels, and merge
- [ ] Verify the `Release` workflow triggers and succeeds
- [ ] Verify git tag, GitHub Release, and PyPI upload (if applicable) are created
```

### 7.3 PR Creation Command

```bash
git push -u origin <BRANCH> && \
  gh pr create --repo <OWNER>/<REPO> --title "feat(release): introduce intuit/auto for automated releases" \
    --body-file .git-meta/PR_BODY.md
```

---

## Final Checklist

After completing all steps, confirm with the user:

- [ ] `.autorc` created and reviewed
- [ ] `.github/workflows/release.yml` created
- [ ] `.github/create-labels.sh` created (or labels created directly)
- [ ] `CONTRIBUTING.md` / `DEVELOPMENT.md` updated with release docs
- [ ] `CHANGELOG.md` prepared for auto-managed entries
- [ ] All changes committed (one logical commit per concern)
- [ ] PR created (or ready-to-run command provided)
- [ ] Manual steps documented (secrets, label creation, branch protection)

## Known Gotchas

- **auto v11.x is the stable major version** as of 2026. Pin to a specific patch version
  in the workflow (whatever `gh release list --repo intuit/auto --limit 5` shows as
  latest stable at time of setup). Do not hardcode a version number in this skill —
  it will go stale immediately and mislead future users.
- **`fetch-depth: 0` is mandatory** in the checkout step — auto reads the full git
  history to determine which PRs are included in the release.
- **`token:` in checkout matters**: using `secrets.GH_TOKEN` (not `secrets.GITHUB_TOKEN`)
  allows auto to push the CHANGELOG commit back to the protected branch. The built-in
  `GITHUB_TOKEN` cannot trigger subsequent workflows, which breaks the release loop.
- **GitHub Release body limit**: GitHub caps release notes at ~125 KB. If your
  CHANGELOG grows very large, the release step will fail with a 422 error. See the
  "CHANGELOG too large" recovery step in the release docs.
- **Dependabot label conflicts**: Dependabot adds `major`, `minor`, `patch` labels to
  its update PRs. Without a label prefix in `.autorc`, merging a Dependabot PR can
  accidentally trigger a release. The `release-` prefix (or any other prefix) avoids this.
- **`onlyPublishWithReleaseLabel: true`** is a second safety net: even if a PR has a
  version-bump label, no release is cut unless it also has the `release` label. This
  prevents accidental releases from label-happy contributors.
