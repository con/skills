# STAMPED skills: sources

Companion to [PLAN.md](PLAN.md).
Each source, and the one thing the plan takes from it.

## STAMPED

- [stamped-paper](https://github.com/stamped-principles/stamped-paper) `main.tex` (preprint doi:10.31222/osf.io/f3h82_v1)
  - The normative definitions, linked and never pasted.
  - Its license principles S.2, M.3 and D.3 are missing from principles-schema 0.2.0, and T.4 has no checklist item.
- [stamped-checklist-schema](https://github.com/stamped-principles/stamped-checklist-schema) 0.3.1
  - The checklist items: 31 items (17 MUST, 9 SHOULD, 5 MAY) with stable ids such as `stamped-checklist:must/009`.
  - There is no response schema.
- [stamped-checklist](https://github.com/stamped-principles/stamped-checklist) (web app)
  - The format-3 URL encoding of answers ([PLAN §4](PLAN.md#4-answer-format)).
  - Also a labeling UI for reference answers.
- [stamped-skills-assessment](https://github.com/stamped-principles/stamped-skills-assessment)
  - Record types (`use_case`, `object`, `rubric`, `assessment`, `review`) for eval runs.
  - Evidence rules: claims are not evidence; unknown is not zero; numerators come with denominators.
- [stamped-agent-skills](https://github.com/stamped-principles/stamped-agent-skills) drafts (@asmacdo)
  - Facts before rules; "make it stick"; the audit loop as development method.
  - It cites the app's version (1.0.1), not the checklist's (0.3.1).

## con/skills

- [#23](https://github.com/con/skills/pull/23) (@asmacdo): `assess-stamped`, `align-stamped`, the base of phase 1.
  Its `DESIGN.md` files list the deferred drop-ins this plan schedules.
- [#16](https://github.com/con/skills/pull/16): `code-quality-report-conventions` (location, provenance stamp, evidence rules) and the top-level `version:` rule; not yet merged.
- [#13](https://github.com/con/skills/pull/13) (APM, `skills/` tree), [#14](https://github.com/con/skills/pull/14) (Claude-neutral wording), [#21](https://github.com/con/skills/pull/21) (`introduce-*` → `setup-*`): followed as they land.
- `ci/validate_skills.py`:
  - W003 warns when a `SKILL.md` exceeds 600 lines;
  - E003 scans `SKILL.md` for home-directory paths;
  - Python checks cover only `*.py` placed directly in a skill directory.

## Earlier attempts

- [STAMPED-dl_morphometrics_biases](https://github.com/STAMPED-dl-morphometrics-biases/STAMPED-dl_morphometrics_biases) `skills/` (@leej3)
  - Its own reviews: execution ran ahead of committed state; a preflight was documented but never built; an absolute `$HOME` path sat in "portable" YAML; the guidance outgrew the context window, and a slimmed skill grew back.
  - Hence: commit before execute; one-screen skills; a lesson needs a regression artifact.
- [dandi/compression-comparisons](https://github.com/dandi/compression-comparisons) → [-t261-study](https://github.com/dandi/compression-comparisons-t261-study)
  - About 1,215 `datalad run` records, built with Claude.
  - Its lessons: no commits during a run; pin the tool and refuse a drifted checkout; measurements are immutable.
  - A calibration object with known gaps: a subdataset `url = ../..`, and containers that were never built.
- [K-Dense #227](https://github.com/K-Dense-AI/scientific-agent-skills/pull/227) / [#265](https://github.com/K-Dense-AI/scientific-agent-skills/pull/265): probes are examples of evidence; "not checked" is not "unmet".
- [bcmcpher datalad-stamped-assess](https://github.com/bcmcpher/my-skills/tree/main/plugins/datalad-cli): prior art for a read-only assessor.
  Its `Stop`-hook autosave is what destroys a long `datalad run`.
- [con/cierge#52](https://github.com/con/cierge/issues/52) (@leej3): the vanilla-vs-skill demo, with each run under `datalad run claude …`.

## Tools and data

- [anthropics/skills `skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator): workspace layout, `grading.json`, aggregation, viewer, and trigger tests (`run_eval.py`, `run_loop.py`).
- [ReproNim/containers](https://github.com/ReproNim/containers)
  - 341 registered Apptainer images, among them `bids-mriqc`, `repronim-simple-workflow` and `neurodesk-*` (afni, fsl, synthstrip, synthseg).
  - `freeze_versions`, and `REPRONIM_USE_DUCT=1` for duct traces.
- [brain-bbqs/study-template](https://github.com/brain-bbqs/study-template): a BIDS 1.11.2 study-dataset skeleton (`rawbids/`, `sourcedata/`, `derivatives/`, …).
- [ReproNim/skills](https://github.com/ReproNim/skills): an empty scaffold, a possible vendoring target.
- [ds007116](https://github.com/OpenNeuroDatasets/ds007116) (Penn LEAD, CC0)
  - 132 subjects and 225 sessions, ages 8.7–20 y.
  - `sessions.tsv` keeps the hour of acquisition.
  - It ships `derivatives/freesurfer-post/*_desc-FreeSurfer_qc.tsv` in plain git.
  - fMRIPrep derivatives are in [ds007088](https://github.com/OpenNeuroDatasets/ds007088).
- [Zenodo 19834562](https://zenodo.org/records/19834562): Dichter et al., SfN'25 poster, AI agents reproducing systems-neuroscience findings from DANDI.
- [Entire](https://github.com/entireio/cli): commit-linked agent transcripts; an option for run provenance.
