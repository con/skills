# Stack: ReproNim and BIDS

What `create-repronim-stamped-project` turns a PROMPT into, and what
`stamped-conventions/references/stacks/repronim.md` will carry once that skill exists.
Companion to [PLAN.md](PLAN.md).

Thin: it reads `stacks/repronim.md` and turns PROMPT into PROMPT-WITH-REPRONIM-SPECIFICS for *create*.
It is also where a future ReproNim assessment skill plugs in.
The ReproNim stack reference covers:

- **Dataset:** a DataLad dataset, `-c text2git` when text files can be shared.
  Nothing YODA-specific; STAMPED is the generalization.
- **Layout:** a BIDS 1.11 study dataset, starting from [brain-bbqs/study-template](https://github.com/brain-bbqs/study-template):
  - raw BIDS goes under `rawbids/`;
  - multiple sources, or sources that are not raw BIDS, go under `sourcedata/`;
  - processing results go under `derivatives/`, alongside `code/`, `docs/` and `logs/`.

  If the whole project *is* the creation of one derivative (for example, brain masks for ds007116), the dataset itself becomes a BIDS derivative dataset (`DatasetType: derivative`).
  Results then go at its root, with no `derivatives/` folder, and the input datasets are subdatasets under `sourcedata/`.
- **Inputs:** OpenNeuro datasets (`///openneuro/dsXXXXXX`, or OpenNeuroStudies `study-dsXXXXXX`) as subdatasets in the place the layout above gives them.
- **Containers:** `///repronim/containers` installed as `code/containers`, with `freeze_versions` and `datalad containers-run`, and `REPRONIM_USE_DUCT=1` so every run gets a duct trace.
- **The project's own tooling:** `datalad`, `datalad-container`, `git-annex` and `con-duct` are declared in a tracked spec with pinned versions.
  That spec is `code/requirements.txt`, `code/pyproject.toml` or a `pixi.toml`; git-annex comes from its PyPI wheel.
  The spec is what P.2/P.3 (must/010, must/013) check for the tooling itself, not only for the containers.
- **Conversion to BIDS:**
  - DICOMs: [HeuDiConv](https://heudiconv.readthedocs.io/en/latest/) with the ReproIn heuristic.
    That may first need a mapping of the acquisition names into the ReproIn convention, or a custom heuristic; follow the HeuDiConv docs and their tutorials.
  - Other data types: pick from the [BIDS converters](https://bids.neuroimaging.io/tools/converters.html) after a fair comparison for the data and environment at hand (for example, a MATLAB-based converter where MATLAB is already in use).
  - Video collections: [ReproStim](https://github.com/ReproNim/reprostim) can slice them into BIDS.
- **Metadata:** `GeneratedBy` in `dataset_description.json`.
- **Optional:** NIDM (`segstats_jsonld`), BEP028 PROV (`metalad runprov`), and mechababs/BABS for scale.
