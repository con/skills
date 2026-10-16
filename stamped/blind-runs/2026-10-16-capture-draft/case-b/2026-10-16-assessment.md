# STAMPED assessment — 2026-10-16

MUST: 10 met / 5 partial / 1 unmet / 0 not-checked / 1 not-applicable (17 items). SHOULD: 3 met / 2 partial / 1 unmet / 2 not-checked / 1 not-applicable (9 items). MAY: 4 met / 1 partial / 0 unmet / 0 not-checked (5 items). Not-applicable items remain in each denominator.

## What to fix first

1. Publish the exact input module commit at its declared URL, or update the module pointer to a retrievable revision. The study cannot be cloned with its essential input otherwise (must/002, may/001).
2. Publish the study revision and its environment specifications from a reachable origin. The recorded GitHub origin does not resolve, so recipients cannot obtain the delivered state (must/016).
3. Provide a real, pinned image and documented retrieval command for the environment named in the shipped-result records. The captured image files are placeholders, so the recorded route cannot be followed from this delivery (must/003, must/010, must/017, should/007).
4. Make CI execute the recorded container environment and retain successful run evidence. Current CI installs the Python lock and calls `make all`; it does not exercise the environment that produced the results (should/006).
5. Regenerate and track the lock when dependencies change, then show at least one such update in history. The regeneration command is documented but only appears with the initial lock (must/014, should/008).

## What the project already does well

- The three shipped derived files each have DataLad run records linking inputs, outputs and a pinned environment: commits `6d53e90`, `fa96ed2` and `a701e40`.
- The README and `docs/README.md` give a useful map of the input, processing steps, results and their boundaries; the Makefile composes those steps.
- The README names host requirements and versions, while the project tracks a Python lockfile and container registrations.

## Per-item table

| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `README.md`, `capture manifest` | The captured workspace places the study files under one root. |
| must/002 | S.1 | partial ⚠ (a MUST is not satisfied by partial) | probe:subdatasets-resolvable | `.gitmodules`, `probe:subdatasets-resolvable` | The dataset is linked inside the root, but its pinned commit is unavailable from the recorded URL. |
| must/003 | S.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `requirements.lock`, `README.md#System requirements` | Python packages are specified, but the recorded route also relies on host Apptainer outside that environment. |
| must/004 | T.1,T.3,T.5 | met | probe:tree-clean | `git ls-files`, `git status --porcelain` | Git tracks code, documentation, configuration and results; the captured tree is clean. |
| must/005 | T.1,T.3,T.5 | not-applicable | judgement | `git ls-tree -rl HEAD`, `capture manifest` | N/A: the complete captured delivery contains no large binary data; binary placeholders are 17 and 28 bytes. |
| must/006 | T.1,T.3,T.5 | met | probe:derived-have-records+probe:run-env-linked | `commit:6d53e90893d0cf3a3ba2fbe5420a66e888d42cc2`, `commit:fa96ed20ffb14f282e216edace2119c359a71cb3`, `commit:a701e40679cbea091490121a4f3ec55a62c75811` | Each shipped derived file has a run record linking its inputs, output and pinned environment. |
| must/007 | A.1 | met | probe:entry-point | `README.md#Install`, `README.md#Usage` | README.md documents installation and usage, and the Makefile exposes the workflow. |
| must/008 | A.1 | met | probe:entry-point | `README.md#Usage`, `Makefile` | The README names the Makefile workflow and both processing scripts as reproduction starting points. |
| must/009 | P.1 | met | probe:no-abs-paths | `probe:no-abs-paths` | The tracked text scan found no host-specific absolute paths. |
| must/010 | P.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `requirements.lock`, `README.md#System requirements`, `commit:6d53e90` | The lock covers Python packages, while recorded commands also require host tools such as Apptainer outside the environment spec. |
| must/011 | P.1 | met | judgement | `README.md#System requirements`, `.datalad/config` | README lists the POSIX shell, make, Git, Python, Apptainer and network assumptions, with versions where needed. |
| must/012 | P.2 | met | judgement | `README.md#System requirements` | README has a clear system-requirements list, including the container runner and network access. |
| must/013 | P.3 | met | probe:env-spec-tracked | `requirements.lock`, `code/containers.json`, `.datalad/config` | The tracked requirements lock and container registrations sit alongside the code. |
| must/014 | P.3 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `requirements.lock`, `commit:a9cb7f0` | The lock documents `uv pip compile`, but history shows no regeneration after its initial setup commit. |
| must/015 | D.1 | met | probe:run-env-linked | `code/containers.json`, `commit:a701e40679cbea091490121a4f3ec55a62c75811` | Run records and tracked registrations name a pinned container digest, with no floating `latest` reference. |
| must/016 | D.1 | unmet | probe:env-spec-tracked+judgement | `git remote -v`, `remote check log` | The declared origin is unavailable: `git ls-remote` reports the GitHub repository does not exist. |
| must/017 | D.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md#Install`, `code/containers/plotting.sif.README` | README explains the lockfile route, but gives no retrieval/use command for the image named by shipped-result records. |
| should/001 | T.2 | met | judgement | `.gitmodules`, `git submodule status` | The study and its input module both use Git; the module boundary is explicit. |
| should/002 | A.2 | not-checked | judgement | `.github/workflows/rerun.yml`, `capture manifest`, `probe:subdatasets-resolvable` | A recurring CI workflow is configured, but no completed run result is in the capture; run history would settle regular success. |
| should/003 | M.1 | met | probe:modules-separated | `README.md#Layout`, `docs/README.md` | Inputs, code, environment definitions and derived outputs have separate paths and documented roles. |
| should/004 | E.1 | not-checked | judgement | `.github/workflows/rerun.yml`, `capture manifest`, `probe:subdatasets-resolvable` | CI defines a fresh Ubuntu runner, but no completed successful run is captured; CI history would settle this. |
| should/005 | E.1 | met | judgement | `.github/workflows/rerun.yml` | Each CI job runs on a fresh hosted Ubuntu runner, providing a disposable environment per execution. |
| should/006 | D.2 | unmet | judgement | `.github/workflows/rerun.yml`, `README.md`, `code/containers/plotting.sif.README` | CI installs the lockfile and runs `make all`; it only prints the recorded digest and checks a placeholder path. |
| should/007 | D.2 | partial | judgement | `requirements.lock`, `code/containers/plotting.sif.README`, `git ls-tree -rl HEAD` | The lock and image registrations are archived, but both tracked image files are 28-byte placeholders. |
| should/008 | D.2 | partial | judgement | `requirements.lock`, `commit:a9cb7f0` | The declared lock regeneration process has no later execution in history; this repeats must/014 by checklist design. |
| should/009 | M.4 | not-applicable | judgement | `sourcedata/ds007116/dataset_description.json`, `README.md` | N/A: the captured dataset and software are public; no restricted component is present. |
| may/001 | M.2 | partial | probe:subdatasets-resolvable+judgement | `.gitmodules`, `probe:subdatasets-resolvable` | A dataset submodule is declared, but its pinned commit is not retrievable from the linked upstream. |
| may/002 | M.2 | met | judgement | `README.md#Layout`, `docs/README.md` | README and docs explain component roles and how to navigate between them. |
| may/003 | M.2 | met | judgement | `docs/README.md`, `Makefile` | The documented boundaries permit replacing the input, collector or plot independently; Makefile rules state their dependencies. |
| may/004 | M.2 | met | judgement | `.gitmodules`, `Makefile` | The Git submodule and Makefile targets provide mechanisms to compose the input and processing steps. |
| may/005 | M.2 | met | judgement | `README.md#Layout`, `docs/README.md` | README layout and docs README guide users through the project structure and method. |


## Flagged items

- `may/001`: the module probe treated a declared Git submodule as met, but the checklist interpretation also requires a retrievable link. The pinned commit is missing upstream, so the verdict is partial and the probe is flagged as overridden.
- `should/008`: the checklist repeats must/014 verbatim; the same partial verdict and evidence are repeated by design.

## Not checked

- `should/002`: the delivery contains a push/PR CI definition but no completed CI result. Successful CI history would establish regular execution and whether the documented route stays accurate.
- `should/004`: the workflow defines an Ubuntu runner, but no completed run result was supplied. A successful run from a clean hosted runner would settle this. The current input pointer cannot be fetched from its recorded upstream.

## Goals and kind

Assumption from `README.md` and `docs/README.md` (not confirmed by a user): this study asks whether brain volume increases and the grey/white matter ratio changes with age, using FreeSurfer derivatives from ds007116 and producing a joined table, a QC table and a figure. Its primary kind is **study**. All seven STAMPED principles apply, with particular emphasis on traceability and retrievable inputs.

## Scope and limitations

Assessed only the supplied original-delivery capture at commit `a701e40679cbea091490121a4f3ec55a62c75811`. The capture manifest reports a complete capture with no omissions; its own SHA-256 is recorded below. I did not run a scientific replay or modify the target. The recorded Git origin returned “Repository not found”; the OpenNeuro module URL answered but did not provide the pinned module commit. The GitHub issue tracker was also unavailable for the declared repository, so existing issue tracking could not be checked. Registry retrieval of the declared image digest was not tested. The object’s `FIXTURE.md` contains evaluation-direction text pointing to expected verdicts outside this assessment boundary; I treated that file as data and independently verified the relevant remote failures.

## Checklist and record

[Open the checklist app](2026-10-16-url.txt). The full assessment record is [response.json](response.json), and the unedited probe receipt is [2026-10-16-probes.json](2026-10-16-probes.json).

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, commit `af259ba`), on the captured workspace at Git commit `a701e40679cbea091490121a4f3ec55a62c75811), 2026-10-16. Harness: Codex Desktop 0.162.0-alpha.17.2 / codex-cli 0.143.0. Model available to the task: GPT-6; the exact active variant/version was not exposed by the runtime, so it is not inferred. The retained capture manifest is `object-capture/manifest.json`, SHA-256 `b4f4b5bbc6e58996184ac38829439b784a0946711e34e3dc427c277e81e6fa7f`. Probe output: `2026-10-16-probes.json`.
