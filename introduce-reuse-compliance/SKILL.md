---
name: introduce-reuse-compliance
description: Introduce REUSE specification compliance (LICENSES/ directory, REUSE.toml, SPDX headers) to a software project or BIDS dataset, then validate it. Covers BIDS data-vs-code separation, DUO (Data Use Ontology) integration, DEP-3 patch tagging for vendoring repos, and integration with tox / pre-commit / Makefile / GitHub Actions. Use when adding licensing metadata to a project, fixing `reuse lint` failures, licensing a BIDS dataset, or annotating patches in a vendoring repo.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# Introduce REUSE Compliance to a Project

Implement the [REUSE specification](https://reuse.software/) for clear,
machine-readable licensing and copyright information. Includes special
support for BIDS datasets, Data Use Ontology (DUO) integration, and
DEP-3 patch tagging for vendoring repositories.

## When to Use

- User wants to add REUSE / SPDX licensing metadata to a project
- User asks to "introduce REUSE" or runs `/introduce-reuse-compliance`
- `reuse lint` is failing and needs to be brought to 100% compliance
- User is licensing a BIDS dataset (data + code + docs separately)
- User is annotating `*.patch` files in a vendoring repo with DEP-3 headers
- User wants to integrate REUSE checks into tox / pre-commit / CI

## Overview

**REUSE Specification** provides standardized practices for declaring copyright and licensing information in software projects and datasets.

**DUO (Data Use Ontology)** from GA4GH provides machine-readable codes for data use restrictions and conditions, particularly for health/biomedical research data.

**Integration**: REUSE handles copyright/licensing (legal permissions), while DUO handles consent-based data use restrictions (ethical/regulatory constraints).

## Guiding principles

These override anything later in the skill that suggests otherwise:

1. **Stay close to what the project already says.** Your job is to make
   existing licensing *machine-readable*, not to relicense parts of the
   project. If the project already ships a single `LICENSE` (e.g.
   Apache-2.0), the default outcome is **one** annotation block covering
   everything under that same license. Do **not** introduce additional
   licenses (CC-BY-4.0 for docs, CC0-1.0 for configs, MIT for scripts,
   etc.) on your own initiative — those are governance decisions for the
   maintainers, not cleanup the linter requires.
2. **Only introduce a second license when the repo already declares
   one.** Triggers: `dataset_description.json` has its own `License`
   field; `package.json`/`pyproject.toml` declares a different license
   for a sub-package; a docs directory has its own `LICENSE`; in-file
   SPDX headers in vendored code; an explicit user request. Absent
   those, do not split.
3. **Scope = git-tracked files.** `reuse lint` walks the working tree
   and will surface untracked-but-not-gitignored paths (caches, tool
   output, scratch dirs). Treat those as *out of scope*: add them to
   `.gitignore` (REUSE honors it) rather than annotating them. If the
   user explicitly wants a path linted, it should be tracked or covered
   by an annotation block.
4. **Prefer one block over many.** Multi-block `REUSE.toml` is only
   warranted when the project genuinely has multi-license parts
   (per principle 2). A single `path = ["**"]` block with
   `precedence = "aggregate"` is the right default for most projects.
5. **Ask before relicensing.** If you find yourself reaching for a
   license the project does not currently use, stop and ask the
   maintainer. Never silently add `CC-BY-4.0` / `CC0-1.0` / `MIT`
   annotations to a project that has only ever stated one license.

## Key Concepts

### REUSE Core Components

1. **LICENSES/** directory: Contains full license texts (e.g., Apache-2.0.txt, CC0-1.0.txt)
2. **REUSE.toml**: Configuration file with copyright and license annotations
3. **`.gitignore`**: REUSE 3.x honors `.gitignore` for excluding build artifacts/caches.
   (`.reuseignore` was deprecated; do not create new `.reuseignore` files.)
4. **SPDX headers**: In-file copyright/license declarations

### REUSE.toml `precedence` field

Each `[[annotations]]` block takes a `precedence` value that controls how the
block-level annotation interacts with in-file SPDX headers:

- `"aggregate"` — block annotation + any in-file SPDX header are combined
  (good default for most blocks).
- `"closest"` — in-file SPDX header wins if present; otherwise the block
  applies. **Use this whenever per-file overrides are expected** (e.g.
  patch files with DEP-3/SPDX headers, vendored sub-trees with mixed
  authorship).
- `"override"` — block always wins, even over in-file SPDX. Rarely the
  right choice; use only when you cannot trust file headers (e.g.
  generated/vendored files with stale or missing tags).

### REUSE scope: per-working-tree, not per-branch

`REUSE.toml` describes the working tree it lives in. If a repository has
substantially different content across branches (e.g. a vendoring repo
with an `upstream/` branch tracking unmodified upstream alongside a
`master` branch with local patches), state this in the README and let
each branch carry its own `REUSE.toml` (or none, deferring to upstream's
own copyright file). This is uncommon — most projects only need one
`REUSE.toml` on the default branch.

### Existing root `LICENSE` / `COPYING` files

**What REUSE requires:** the spec (3.x §2.2) mandates that license texts
live under `LICENSES/<SPDX-ID>.<ext>`. It does **not** forbid additional
copies elsewhere — a top-level `LICENSE` is allowed but redundant from
REUSE's point of view.

**What other ecosystems expect:**
- **GitHub** (licensee gem): scans the root for `LICENSE`, `LICENCE`,
  `COPYING`, etc. to populate the "License" badge on the repo page.
  Modern licensee follows symlinks and also recognizes `LICENSES/<id>.txt`,
  but root visibility is the most reliable trigger.
- **Apache-2.0 §4(d)**: a derivative work must reproduce the LICENSE
  and any NOTICE — convention is to ship them at the repo root.
- **Python packaging** (`pyproject.toml`): `[project] license-files =
  ["LICENSE", "NOTICE"]` declares which files end up in sdists/wheels.
  Hatch/setuptools resolve these literally; if you delete `LICENSE`,
  update this list (e.g. to `["LICENSES/Apache-2.0.txt", "NOTICE"]`).
- **Other languages**: `package.json` has no equivalent file pinning
  by default, but some npm tooling looks for `LICENSE` at root.

**Three reconciliation options** — pick based on the project's
ecosystem and pyproject/package metadata findings from Step 1:

1. **Keep both files (duplicate text).** Simplest, zero portability
   risk. Downside: 10–15 KB of duplicated text per license. Default
   recommendation for projects that already ship a root `LICENSE`
   referenced by `pyproject.toml` / `package.json` / similar manifests.

2. **Symlink root → `LICENSES/<id>.txt`.** No duplication, REUSE-pure,
   GitHub licensee follows symlinks (since ~2018). Downsides:
   symlinks are awkward on Windows checkouts without
   `core.symlinks=true`; hatch/setuptools follow them in most
   versions, but verify with `python -m build --sdist` on a clean
   checkout. Recommended when the project has no Windows contributors
   and you want to avoid the duplication.

3. **Delete root `LICENSE` entirely; only keep `LICENSES/<id>.txt`.**
   Most REUSE-pure. Requires updating `pyproject.toml`
   `license-files`, regenerating sdist tests, and possibly losing
   GitHub's auto-detection on older licensee versions. Only do this
   if you've verified all downstream consumers (packaging, GitHub UI,
   any CI license-check tooling) cope with `LICENSES/`. Same applies
   to `COPYING`/`NOTICE` if present.

**Apache `NOTICE` files** stay at the root regardless — Apache-2.0
§4(d) treats NOTICE as separate from the license text.

**Default for skill runs:** propose option (1) and ask the user. Do
**not** silently delete or symlink an existing root `LICENSE` —
licensing files are governance artifacts, and downstream consumers
(packaging metadata, CI gates, contributors' bookmarks) often depend
on them.

### BIDS Dataset Considerations

Per [bids-specification#2015](https://github.com/bids-standard/bids-specification/issues/2015):
- **dataset_description.json**: Contains `License` field for data portion
- **Multiple licenses**: Code components may need separate licensing from data
- **REUSE.toml in BIDS**: Should clarify data vs. code licensing
- **DUO annotations**: Can supplement licenses with data use conditions

### DUO Integration

Per [bids-specification#2078](https://github.com/bids-standard/bids-specification/issues/2078) and [reuse-tool#1148](https://github.com/fsfe/reuse-tool/issues/1148):
- DUO codes describe data use conditions beyond licensing
- Examples: "no re-identification" (DUO:0000028), "general research use" (DUO:0000042)
- Can be included in REUSE.toml or dataset_description.json
- See: https://github.com/EBISPOT/DUO

## Commit Co-Authorship

All commits created during this workflow MUST include a `Co-Authored-By` trailer identifying
both Claude Code version and the model used. Get the version via `claude --version` and
use the model name from the environment. Format:

```
Co-Authored-By: Claude Code <VERSION> / Claude <MODEL> <noreply@anthropic.com>
```

Example:
```
Co-Authored-By: Claude Code 2.1.123 / Claude Opus 4.7 <noreply@anthropic.com>
```

## Execution Steps

When this skill is invoked, follow these steps:

### 1. Assess Current State

**Discover the project's existing licensing statements** (this is the
input you must respect — see Guiding principles):
- `LICENSE` / `LICENCE` / `COPYING` / `COPYING.*` at the repo root
- `NOTICE` (Apache-2.0 conventional file)
- License field in `pyproject.toml` (`[project] license = ...`),
  `package.json` (`"license"`), `setup.cfg`, `Cargo.toml`, `Gemfile`,
  `dataset_description.json` (`License`), `CITATION.cff`
- Per-directory `LICENSE` / `COPYING` files (sub-packages, docs/, data/)
- In-file SPDX-License-Identifier headers (`grep -r SPDX-License-Identifier`)
- README / DEVELOPMENT.md sections explicitly stating a license
- Copyright lines in headers / NOTICE / README (extract author + year)

The set of licenses you propose must be a **subset** of what these
sources already declare. If they all say one thing (e.g. Apache-2.0),
your `REUSE.toml` says one thing.

**Check for existing REUSE infrastructure:**
- Look for `LICENSES/` directory
- Check if `REUSE.toml` or `.reuse/dep5` exists
- Scan for existing SPDX headers in files
- If a legacy `.reuseignore` exists, plan to migrate its entries to
  `.gitignore` and remove it

**Determine the working scope (git-tracked vs. untracked):**
- Run `git ls-files | wc -l` to know the tracked file count
- Run `git status --short` to enumerate untracked paths
- Compare against `reuse lint` output: any untracked path that appears
  in the lint output is a candidate for `.gitignore` (not annotation).
  Common offenders: tool output dirs (`.duct/`, `.idea/` if not
  ignored), local scratch dirs, generated logs, screenshots, exports.
- If `git ls-files --error-unmatch <path>` fails for a path the linter
  flagged, the path is untracked and out of scope by default.

**Check for BIDS dataset (only relevant if applicable):**
- Look for `dataset_description.json`
- Check if it contains `License` field
- Identify data files vs. code files (`scripts/`, `code/`)

**Check for build system integration:**
- `tox.ini` exists → propose adding `[testenv:reuse]`
- `.pre-commit-config.yaml` exists → propose adding the reuse hook
- `Makefile` exists → propose adding a `reuse-lint` target
- `.github/workflows/` exists → propose adding a reuse check step

### 2. Propose REUSE Structure

The shape of `LICENSES/` and `REUSE.toml` follows directly from what
you found in Step 1. **Do not add license texts the project has not
declared.**

**Default — single declared license (most projects):**
```
LICENSES/
└── <existing-license>.txt   # e.g. Apache-2.0.txt, MIT.txt — only this

REUSE.toml                    # one [[annotations]] block, path = ["**"]
```

**Multi-license — only when the project already uses multiple
licenses** (e.g. data under CC0 + code under MIT, or vendored sub-tree
under a different SPDX ID):
```
LICENSES/
├── <code-license>.txt
└── <other-license>.txt       # only those already declared

REUSE.toml                    # one block per license-bearing path set
```

**For BIDS datasets:** likewise driven by what `dataset_description.json`
and any in-tree code license declares — not by adding plausible
defaults.

### 3. Create REUSE.toml

Generate annotations using the licenses surfaced in Step 1.

**Default single-license template (recommended for most projects):**
```toml
version = 1

[[annotations]]
path = "**"
precedence = "aggregate"
SPDX-FileCopyrightText = "YEAR-RANGE AUTHORS"   # e.g. "2019-2026 Acme, Inc. and project contributors"
SPDX-License-Identifier = "LICENSE-ID"           # the license already in LICENSE/COPYING
```

This single block covers the entire git-tracked tree. Use it whenever
the project has one declared license. Resist adding more blocks unless
Step 1 surfaced explicit per-area licenses.

**Multi-block template — only when justified by Step 1 findings:**
```toml
version = 1

[[annotations]]
path = "**"
precedence = "aggregate"
SPDX-FileCopyrightText = "YEAR AUTHOR"
SPDX-License-Identifier = "LICENSE-ID"

# Add additional blocks ONLY for paths the project itself licenses
# differently (e.g. dataset_description.json says License=CC0 for data,
# or vendored/ ships its own LICENSE).
[[annotations]]
path = ["data/**"]
precedence = "aggregate"
SPDX-FileCopyrightText = "YEAR DATA-PROVIDER"
SPDX-License-Identifier = "CC0-1.0"   # because dataset_description.json says so
```

**BIDS Dataset Template (only when applicable):**
```toml
version = 1

# BIDS data files
[[annotations]]
path = [
    "sub-*/**/*.nii.gz",
    "sub-*/**/*.json",
    "sub-*/**/*.tsv",
    "participants.tsv",
    "participants.json",
    "*.tsv",
    "*.json",
]
precedence = "aggregate"
SPDX-FileCopyrightText = "YEAR DATA-COLLECTORS"
SPDX-License-Identifier = "CC0-1.0"
# Optional DUO annotation (if applicable)
# DataUseOntology = ["DUO:0000042"]  # General research use

# BIDS code/derivatives
[[annotations]]
path = [
    "code/**",
    "derivatives/**/*.py",
    "derivatives/**/*.sh",
]
precedence = "aggregate"
SPDX-FileCopyrightText = "YEAR DEVELOPERS"
SPDX-License-Identifier = "MIT"

# Documentation
[[annotations]]
path = ["README*", "CHANGES*", "dataset_description.json"]
precedence = "aggregate"
SPDX-FileCopyrightText = "YEAR AUTHORS"
SPDX-License-Identifier = "CC-BY-4.0"
```

### 4. Handle BIDS dataset_description.json

**Current format (BIDS 1.x):**
```json
{
  "Name": "Dataset Name",
  "BIDSVersion": "1.9.0",
  "License": "CC0"
}
```

**Proposed enhanced format (per bids-spec#2015 and #2078):**
```json
{
  "Name": "Dataset Name",
  "BIDSVersion": "1.9.0",
  "License": "CC0",
  "DataUseOntology": [
    "DUO:0000042",
    "DUO:0000028"
  ],
  "DataUseDescription": "General research use; No re-identification"
}
```

**Common DUO codes:**
- `DUO:0000042` - General research use
- `DUO:0000028` - No re-identification
- `DUO:0000006` - Health or medical or biomedical research
- `DUO:0000007` - Disease-specific research
- `DUO:0000021` - Ethics approval required
- `DUO:0000043` - Clinical care use

### 5. Keep scope to git-tracked files via `.gitignore`

`reuse lint` walks the working tree, but it honors `.gitignore` —
anything matched there is automatically skipped. It does **not**
auto-skip untracked-but-not-gitignored files; those will appear in the
lint output as "missing licensing." The right fix is almost always to
add such paths to `.gitignore`, **not** to add SPDX annotations for
them. **Do not create a `.reuseignore` file** (deprecated).

Workflow:

1. Run `reuse lint`. Any flagged path that is not under git control
   (`git ls-files --error-unmatch <path>` returns non-zero) is a
   gitignore candidate.
2. Add those paths to `.gitignore` (or to a project-appropriate ignore
   file). Common offenders: tool output (`.duct/`, `.idea/`), local
   caches, generated logs, dev scratch dirs, `staticfiles/`, test
   artifacts, screenshots.
3. Re-run `reuse lint` until the only remaining flagged files are
   tracked. Those — and only those — are the ones your annotation
   blocks need to cover.

Standard build-artifact entries to ensure are present in `.gitignore`:

```gitignore
# Build artifacts and caches
.tox/
.venv*/
__pycache__/
*.egg-info/
build/
dist/
.pytest_cache/
.mypy_cache/
.ruff_cache/
node_modules/
```

**BIDS-specific excludes:**
```gitignore
# BIDS working directories (if any)
sourcedata/
work/
.bidsignore
.datalad/
```

If a legacy `.reuseignore` exists, migrate its entries to `.gitignore`
and delete the file. Large generated/binary artifacts that you
intentionally want tracked but excluded from REUSE (rare) should instead
be covered by an `[[annotations]]` block in `REUSE.toml` with
appropriate SPDX tags.

### 6. Integrate with Build Systems

**A. tox.ini Integration:**
```ini
[testenv:reuse]
skip_install = true
deps = reuse
description = Check REUSE specification compliance
commands =
    reuse lint

[gh-actions]
python =
    3.12: py312, lint, type, reuse
```

**B. pre-commit Integration:**
```yaml
repos:
  - repo: https://github.com/fsfe/reuse-tool
    rev: v4.0.3
    hooks:
      - id: reuse
```

**C. Makefile Integration:**
```makefile
.PHONY: reuse-lint reuse-download

reuse-lint:
	@echo "=== Checking REUSE compliance ==="
	reuse lint

reuse-download:
	@echo "=== Downloading missing licenses ==="
	reuse download --all

reuse-annotate:
	@echo "=== Annotating file with license header ==="
	@read -p "File to annotate: " file; \
	reuse annotate --license Apache-2.0 --copyright "YEAR AUTHOR" $$file
```

**D. GitHub Actions Integration:**
```yaml
- name: Check REUSE compliance
  uses: fsfe/reuse-action@v5
```

### 7. Validate and Report

Run validation:
```bash
reuse lint
```

Expected output sections:
- **Bad licenses**: License files with issues
- **Missing licenses**: Referenced but not in LICENSES/
- **Files with copyright information**: X / Y
- **Files with license information**: X / Y

Goal: 100% compliance (all files have both copyright and license info)

### 8. DUO Validation (BIDS Datasets)

If DUO codes are present, validate them:
1. Check codes exist in DUO ontology: https://www.ebi.ac.uk/ols/ontologies/duo
2. Ensure codes are consistent with License field
3. Verify DataUseDescription matches codes
4. Check for conflicting restrictions

**Common patterns:**
- CC0 + DUO:0000042 → "Open data, general research use"
- CC-BY-4.0 + DUO:0000028 → "Attribution required, no re-identification"
- Custom + DUO:0000021 → "Restricted access, ethics approval required"

## Optional: Patches against external upstream + DEP-3

**Skip this section unless** the repository carries `*.patch` files that
modify some other project's source (e.g. a vendoring/CI repo with
`patches/` applied at build time). This is a relatively rare setup —
most projects do not need it.

When it does apply, REUSE alone is not enough: each patch should also
carry a [DEP-3](https://dep-team.pages.debian.net/deps/dep3/) header so
its provenance, upstream-forwarding status, and license are documented
in-band.

### Licensing of patch files

Patches are derivative works of the upstream they modify and must
inherit the upstream license. Choose the SPDX identifier from upstream's
license:
- git-annex / GPL upstreams → `AGPL-3.0-or-later` / `GPL-2.0-or-later` / etc.
- BSD/MIT upstreams → match exactly.

In `REUSE.toml`, use `precedence = "closest"` on the patches subtree so
the per-patch SPDX header (added below) wins over the block-level
fallback:

```toml
[[annotations]]
path = "patches/**"
precedence = "closest"
SPDX-FileCopyrightText = "YEAR PROJECT TEAM <email>"
SPDX-License-Identifier = "AGPL-3.0-or-later"  # match upstream
```

### DEP-3 + SPDX header template

Prepend the following RFC-2822-style block to every `*.patch`. The
trailing `---` line terminates the metadata; everything after it is the
ordinary `git diff` content. Patch tools (`git apply`, `git apply -R
--check`, `quilt`, `patch`) accept and ignore the preamble.

```
Description: <one-line summary>
 <longer explanation: why this patch exists, what it works around,
 who benefits, whether it is vendor-specific>
Origin: vendor, https://<commit-url>
Author: First Last <email@example.org>
Forwarded: not-needed   # OR: <URL of upstream submission>; OR: no
Last-Update: YYYY-MM-DD
Bug: <upstream bug URL, if any>
Applied-Upstream: <commit/version, if it landed>
SPDX-FileCopyrightText: YEAR First Last <email@example.org>
SPDX-License-Identifier: <upstream-matching SPDX ID>
---
diff --git a/...
```

Field reference (DEP-3):
- `Description` (required) — short summary on first line, longer
  explanation indented on following lines.
- `Origin` (required unless `Author`) — `upstream`, `backport`,
  `vendor`, or `other`, optionally with a URL.
- `Author` / `From` — patch author(s).
- `Forwarded` — `yes`/URL, `no`, or `not-needed`.
- `Last-Update` — ISO date the metadata was last revised.
- `Bug`, `Bug-<Vendor>`, `Reviewed-by`, `Applied-Upstream` — optional.

### Verify patch tooling tolerates the preamble

Before committing, sanity-check the project's actual patch-application
path (not just `git apply`). For example:
```bash
git apply --check patches/<file>.patch
git apply -R --check patches/<file>.patch  # if reverse-check is used
```
If the project uses `quilt`, `patch -p1`, or a custom script, run that
too. Most tools ignore the preamble, but confirm before assuming.

### Document it in the README

Add a brief Licensing section pointing at `REUSE.toml` and `LICENSES/`,
and extend any "Submitting Patches" / contributing guidance with the
DEP-3 + SPDX template so new patches are compliant out of the gate.

## Decision Points

### License Selection

> **Default behaviour: do NOT pick a license here.** Use whatever the
> project already declares (per Step 1 / Guiding principles). The list
> below is reference material *only* for two cases: (a) the user is
> bootstrapping a brand-new project that has no `LICENSE` yet and asks
> you for guidance, or (b) the user explicitly asks to relicense or to
> add a separate license for a sub-area. In every other case, skip
> this section.

**For code:**
- Apache-2.0: Permissive, patent grant
- MIT: Simple, permissive
- GPL-3.0-or-later: Copyleft

**For data:**
- CC0-1.0: Public domain dedication
- CC-BY-4.0: Attribution required
- PDDL-1.0: Open Data Commons Public Domain

**For documentation:**
- CC-BY-4.0: Standard for documentation
- CC-BY-SA-4.0: Share-alike for wikis

### DUO Code Selection (BIDS)

Ask user about data use restrictions:
1. Is this general research use? → DUO:0000042
2. Can data be used for re-identification? → If no, add DUO:0000028
3. Is ethics approval required? → DUO:0000021
4. Disease-specific restrictions? → DUO:0000007 + specific disease
5. Collaboration required? → DUO:0000020
6. Time limit? → DUO:0000024 + duration

### Build System Priority

If multiple systems exist, suggest:
1. **Primary**: tox (Python standard)
2. **Developer workflow**: pre-commit (catches issues early)
3. **CI/CD**: GitHub Actions (automated checks)
4. **Make**: For projects already using it

## Output

Provide:
1. **Status report**: Current compliance level
2. **Action items**: What needs to be done
3. **File changes**: Specific files to create/modify
4. **Integration steps**: How to add to build systems
5. **Validation command**: How to check compliance

For BIDS datasets, additionally provide:
- Suggested dataset_description.json updates
- DUO code recommendations based on data type
- Explanation of REUSE + DUO synergy

## References

- REUSE Specification: https://reuse.software/spec/
- REUSE Tutorial: https://reuse.software/tutorial/
- DEP-3 (Patch Tagging Guidelines): https://dep-team.pages.debian.net/deps/dep3/
- BIDS REUSE Issue: https://github.com/bids-standard/bids-specification/issues/2015
- BIDS DUO Issue: https://github.com/bids-standard/bids-specification/issues/2078
- DUO Ontology: https://github.com/EBISPOT/DUO
- GA4GH DUO Standard: https://www.ga4gh.org/product/data-use-ontology-duo/

## Notes

- **Never invent a license the project does not already use.** Adding
  REUSE compliance is a *cleanup* operation, not a relicensing
  operation. If you find yourself wanting to declare CC-BY-4.0 for
  docs or CC0-1.0 for configs in a project that has only ever shipped
  one license, stop and ask the maintainer first.
- Default scope is git-tracked files. Anything else gets gitignored,
  not annotated.
- Prefer one `[[annotations]]` block with `path = "**"` over many.
  Add more blocks only when the project itself already distinguishes
  per-area licensing.
- For BIDS: `License` field in `dataset_description.json` should match
  the REUSE.toml data annotations.
- DUO codes are complementary to licenses, not replacements.
- REUSE handles "can you legally use this?", DUO handles "under what
  conditions?".
- When in doubt about DUO codes, consult the institutional review
  board or data governance team.
