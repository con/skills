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

**Check for existing REUSE infrastructure:**
- Look for LICENSES/ directory
- Check if REUSE.toml or .reuse/dep5 exists
- Check `.gitignore` for build-artifact exclusions (REUSE 3.x honors it;
  if a legacy `.reuseignore` exists, plan to migrate its entries to
  `.gitignore` and remove it)
- Scan for SPDX headers in files

**Check for BIDS dataset:**
- Look for dataset_description.json
- Check if it contains License field
- Identify data files vs. code files (scripts/, code/)

**Check for build system integration:**
- Check if tox.ini exists → suggest adding [testenv:reuse]
- Check if .pre-commit-config.yaml exists → suggest adding reuse hook
- Check if Makefile exists → suggest adding reuse target
- Check if .github/workflows/ exists → suggest adding reuse check

### 2. Propose REUSE Structure

**For general projects:**
```
LICENSES/
├── Apache-2.0.txt     # Main code license
├── CC-BY-4.0.txt      # Documentation license
└── CC0-1.0.txt        # Public domain data

REUSE.toml              # License annotations
```

**For BIDS datasets:**
```
LICENSES/
├── CC0-1.0.txt        # Data license (if public domain)
├── CC-BY-4.0.txt      # Data license (if attribution required)
└── MIT.txt            # Code/scripts license

REUSE.toml              # Separate annotations for data vs code
dataset_description.json  # License field + optional DUO codes
```

### 3. Create REUSE.toml

Generate appropriate annotations:

**Standard Project Template:**
```toml
version = 1

[[annotations]]
path = [
    "src/**",
    "tests/**",
    "*.py",
    "*.md",
    ".github/**",
]
precedence = "aggregate"
SPDX-FileCopyrightText = "YEAR AUTHOR <email>"
SPDX-License-Identifier = "LICENSE-ID"

[[annotations]]
path = ["data/**"]
precedence = "aggregate"
SPDX-FileCopyrightText = "YEAR DATA-PROVIDER"
SPDX-License-Identifier = "CC0-1.0"
```

**BIDS Dataset Template:**
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

### 5. Exclude build artifacts via `.gitignore`

REUSE 3.x honors `.gitignore` — anything matched there is automatically
skipped by `reuse lint`. **Do not create a `.reuseignore` file** (it is
deprecated). Add build artifacts and caches to `.gitignore` if not
already there:

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

- Always preserve existing licensing information when adding REUSE compliance
- For BIDS: License field in dataset_description.json should match REUSE.toml data annotations
- DUO codes are complementary to licenses, not replacements
- REUSE handles "can you legally use this?", DUO handles "under what conditions?"
- When in doubt about DUO codes, consult institutional review board or data governance team
