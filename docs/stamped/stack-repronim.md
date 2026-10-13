# ReproNim stack reference (draft)

Draft of `create-repronim-stamped-project/references/stack-repronim.md`, to be moved there in phase 4 of [PLAN.md](PLAN.md#7-roadmap).
`create-repronim-stamped-project` reads it and turns the user's PROMPT into PROMPT-WITH-REPRONIM-SPECIFICS for the generic `create-stamped-project`.
It describes properties first and ReproNim tools as the way this stack satisfies them; the generic skills stay tool-agnostic.

## Dataset

- A DataLad dataset, created with `-c text2git` when its text files can be shared publicly.
- Nothing YODA-specific: STAMPED is the generalization of YODA.

## Layout

A BIDS 1.11 ["study" dataset](https://bids-specification.readthedocs.io/en/stable/common-principles.html#study-dataset), starting from [brain-bbqs/study-template](https://github.com/brain-bbqs/study-template):

- raw BIDS goes under `rawbids/`;
- multiple sources, or sources that are not raw BIDS, go under `sourcedata/`;
- processing results go under `derivatives/`, alongside `code/`, `docs/` and `logs/`.

If the whole project *is* the creation of one derivative (for example, brain masks for ds007116), the dataset itself becomes a BIDS derivative dataset (`DatasetType: derivative`).
Results then go at its root, with no `derivatives/` folder, and the input datasets are subdatasets under `sourcedata/`.

## Inputs

OpenNeuro datasets (`///openneuro/dsXXXXXX`, or OpenNeuroStudies `study-dsXXXXXX`) are installed as subdatasets in the place the layout above gives them.
Use per-session ages (`sub-*/sub-*_sessions.tsv`) where a dataset has them, not the baseline age in `participants.tsv`.

## Containers

- `///repronim/containers` installed as `code/containers`, with `freeze_versions` pinning the images used.
- Every containerized step runs through `datalad containers-run`.
- `REPRONIM_USE_DUCT=1`, so every run also records a duct resource trace.

## The project's own tooling

`datalad`, `datalad-container`, `git-annex` and `con-duct` are declared, with pinned versions, in a tracked spec: `code/requirements.txt`, `code/pyproject.toml` or a `pixi.toml`.
git-annex comes from its PyPI wheel.
That spec is what must/010 and must/013 check for the tooling itself, not only for the containers.

## Conversion to BIDS

- **DICOMs:** [HeuDiConv](https://heudiconv.readthedocs.io/en/latest/) with the ReproIn heuristic.
  That may first need a mapping of the acquisition names into the ReproIn convention, or a custom heuristic; follow the HeuDiConv docs and their tutorials.
- **Other data types:** pick from the [BIDS converters](https://bids.neuroimaging.io/tools/converters.html) after a fair comparison for the data and environment at hand.
  For example, prefer a MATLAB-based converter where MATLAB is already in use.
- **Video collections:** [ReproStim](https://github.com/ReproNim/reprostim) can slice them into BIDS.

## Metadata

`GeneratedBy` (and `SourceDatasets`) in `dataset_description.json`.

## Optional, at scale

- NIDM via `segstats_jsonld` ([OpenNeuroDerivatives-NIDM](https://github.com/ReproNim/OpenNeuroDerivatives-NIDM));
- BEP028 PROV via `metalad runprov`;
- [con/mechababs](https://github.com/con/mechababs) / BABS for many subjects on a cluster.
