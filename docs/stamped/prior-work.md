# Prior work, and what this collection takes from it

Companion to [PLAN.md](PLAN.md).

### STAMPED itself

**[stamped-agent-skills](https://github.com/stamped-principles/stamped-agent-skills): `stamped-skill-draft.md`, `stamped-skill-next-steps.md`** (@asmacdo)
- *What it is:* one draft STAMPED skill (facts → make it stick → 7 rules → moments → audit) plus a next-steps document.
- *What we take:* its settled decisions.
  - an agent-agnostic core;
  - "intervene, don't summarize";
  - establish facts before applying rules;
  - the "make it stick" pointer in `AGENTS.md`;
  - audit items generated from the checklist;
  - its development method, the **audit loop**: diff what the agent improvised against what the skill said, then promote or prune.

  Its content becomes the seed of `stamped-conventions` and *assess*.
  One fix: it cites "checklist v1.0.1", which is the web app's `package.json` version, not `checklist_version` (0.3.1).

**[stamped-checklist-schema](https://github.com/stamped-principles/stamped-checklist-schema) 0.3.1**
- *What it is:* LinkML schema and JSON for the checklist items: 31 items (17 MUST, 9 SHOULD, 5 MAY), with ids such as `stamped-checklist:must/009`.
- *What we take:* the only item source we use, vendored and pinned.
  There is **no response schema** ([§5](PLAN.md#5-checklist-response-format)).

**[stamped-checklist](https://github.com/stamped-principles/stamped-checklist) (web app)**
- *What it is:* pulls the items at a pinned tag and persists answers in the URL as `format=3`.
  The payload is base64 of `{"checklist_version", "responses": {id: {"value", "reason"}}}`, where `value` is `"yes"`, `"no"` or `null`.
  Reasons are capped at 250 characters, and an unknown id fails the whole load.
- *What we take:* the URL is how a report hands its result to people.
  The app is also a ready-made labeling UI: you fill the checklist for a test project and we decode the link into a reference answer ([evals.md §7](evals.md#7-calibrating-the-assessor)).

**[stamped-skills-assessment](https://github.com/stamped-principles/stamped-skills-assessment)**
- *What it is:* LinkML records for `use_case`, `object`, `rubric`, `assessment` and `review`, with a validator, a pinned "reference lock", and `docs/automation-evidence.md`.
- *What we take:* the durable record format for eval runs.
  Use case → `use_case` + `rubric`; produced project → `object`; grading → `assessment`; your feedback → `review`.
  Its evidence rules carry over:
  - an agent's success report is an assertion, not evidence;
  - a skill path being present does not show the skill was used;
  - unknown is not zero;
  - collector failures are kept apart from object defects;
  - numerators are reported with their denominators.

**[stamped-paper](https://github.com/stamped-principles/stamped-paper) `main.tex`**
- *What it is:* the normative definitions.
  Its AI section covers pinning models, `datalad run` around agent calls, `Co-Authored-By`, and AGENTS.md.
- *What we take:* linked, never pasted.
  Note the drift to raise upstream: the paper's S.2, M.3 and D.3 (licenses) are missing from principles-schema 0.2.0, and T.4 has no checklist item.

### Earlier attempts to learn from

**[STAMPED-dl_morphometrics_biases](https://github.com/STAMPED-dl-morphometrics-biases/STAMPED-dl_morphometrics_biases) `skills/`** (@leej3, Codex)
- *What it is:* a heavy STAMPED neuroimaging skill with a roughly 3,000-row assessment TSV.
  Its own phase-3 reviews document the failures.
- *What we take:* the negative lessons.
  - Execution ran ahead of committed state.
  - The preflight was "three documents about the gate and zero lines of gate".
  - An absolute `$HOME` path sat in "portable" YAML.
  - The guidance outgrew the context window.
  - A slimmed skill grew back within two days.

  What follows: **commit before execute**; one-screen operating cards; **a lesson requires a regression artifact**; a size and duplication lint; a factorial evaluation design.

**[dandi/compression-comparisons](https://github.com/dandi/compression-comparisons) → [compression-comparisons-t261-study](https://github.com/dandi/compression-comparisons-t261-study)**
- *What it is:* 1,265 commits, about 1,215 `[DATALAD RUNCMD]` records, and duct logs, built with Claude.
- *What we take:*
  - never commit while a `datalad run` is in flight (cells were lost; the fix became a pre-commit hook);
  - pin the tool subdataset and refuse a dirty or drifted checkout;
  - measurements are immutable while narrative can be corrected;
  - trace each parameter to its consumer, and run no-op controls;
  - adversarial reviews and `CORRECTION:` commits.

  Its known gaps make it a **real-world calibration object**: the subdataset `url = ../..` (fails D), and containers that were written but never built (P/E).

**[K-Dense scientific-agent-skills#227](https://github.com/K-Dense-AI/scientific-agent-skills/pull/227) (DataLad skill) and [#265](https://github.com/K-Dense-AI/scientific-agent-skills/pull/265) (STAMPED probes, changes requested)**
- *What it is:* the STAMPED section in `references/provenance.md`, and review feedback on #265.
  The feedback asks for tool-agnostic evidence, and says "not checked with the tooling available" is not "unmet".
- *What we take:*
  - probes are *examples* of evidence, and equivalent evidence counts (a tracked Makefile or Snakefile satisfies A.2);
  - `not-checked` is a separate verdict;
  - adopt the "Validation scope" section, `metadata.version`, and tests kept outside the skill directory.

**[bcmcpher/my-skills](https://github.com/bcmcpher/my-skills/tree/main/plugins/datalad-cli) `datalad-stamped-assess`**
- *What it is:* a read-only ✓/◐/✗ assessment that cites evidence, with `--plan` mapping fixes to other skills.
- *What we take:* prior art for *assess*.
  Avoid its `Stop`-hook autosave: it is exactly what destroys a long `datalad run`.

**[con/cierge#52](https://github.com/con/cierge/issues/52)** (@leej3)
- *What it is:* a demo design for US-RSE.
  A vanilla run is compared with a `/repronim-stamped-analysis` run.
  Each is started via `datalad run claude "…"` in a fresh `datalad create -c text2git` dataset and recorded with Entire.
- *What we take:* the runner design for the outer loop ([evals.md §5](evals.md#5-runners-inner-and-outer-loop)), and a name to reconcile with `create-repronim-stamped-project` ([§10](PLAN.md#10-open-questions)).

### Infrastructure and data

**[ReproNim/containers](https://github.com/ReproNim/containers)**
- *What it is:* 341 registered Apptainer images.
  They include `bids-mriqc` 24.0.2, `repronim-simple-workflow`, and about 345 `neurodesk-*` images (afni, fsl, synthstrip, synthseg, fastsurfer).
  It uses `freeze_versions` and `REPRONIM_USE_DUCT=1`.
- *What we take:* the environment layer for the ReproNim rungs.

**[brain-bbqs/study-template](https://github.com/brain-bbqs/study-template)**
- *What it is:* a BIDS 1.11.2 ["study" dataset](https://bids-specification.readthedocs.io/en/stable/common-principles.html#study-dataset) skeleton.
  It has `rawbids/`, `sourcedata/`, `derivatives/`, `code/`, `docs/`, `logs/` and `scratch/`, each with a README.
  Its `sourcedata/` README already points at STAMPED self-containment.
- *What we take:* the starting layout for ReproNim/BIDS projects ([§4.2](#create-repronim-stamped-project)).

**[ReproNim/skills](https://github.com/ReproNim/skills)**
- *What it is:* an empty scaffold in Agent Skills format.
- *What we take:* where the ReproNim layer could eventually be vendored.

**con/skills itself**
- *What it is:*
  - `AGENTS.md` rules;
  - `ci/validate_skills.py`;
  - the shared-conventions pattern and `version:` frontmatter (#16/#22);
  - APM distribution with a `skills/` tree (#13, merged 2026-10-15 into the `ci-security-llm-review` branch of #9; adopted here already);
  - Claude-neutral wording (#14);
  - `introduce-*` → `setup-*` (#21).
- *What we take:* follow all of these.
  The STAMPED skills use the same "sibling conventions skill, read it or stop" contract as `code-quality-report-conventions`.

**[anthropics/skills `skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator)**
- *What it is:* an eval loop.
  It runs with-skill and baseline runs, grades into `grading.json` (`text`/`passed`/`evidence`), aggregates a benchmark, and has an HTML viewer for human feedback and a description-trigger optimizer.
- *What we take:* its workspace layout and viewer for the inner loop, rather than building our own.

**[ds007116](https://github.com/OpenNeuroDatasets/ds007116)** (Penn LEAD, CC0)
- *What it is:* 132 subjects and 225 sessions.
  - Ages run 8.7–20 y per session.
  - `sessions.tsv` keeps the time of day at hour resolution (09:00–19:00), with dates shifted to the 1800s.
  - Modalities: T1w/T2w, rest and n-back BOLD, DWI, ASL.
  - It already ships `derivatives/freesurfer-post/*_qc.tsv` in plain git.
  - Linked fMRIPrep derivatives are in ds007088.
- *What we take:* an ideal ladder.
  Rung 0 needs no compute at all, and the shipped derivatives double as an **oracle** for later rungs.

---
