# STAMPED assessment: brain-volume-vs-age (R0 fixture), 2026-10-15

**Blind run, no user available.** Goals and kind are labelled assumptions, not confirmed: kind = `study` (README: a question answered from `sourcedata/ds007116` derivatives, with run records). Stated goal per README: does brain volume grow with age over 8-20 years, and does the GM/WM ratio fall.

**Verdict line.** MUST: 9 met / 7 partial / 1 unmet / 0 not-checked (of 17). SHOULD: 4 met / 4 partial / 0 unmet / 0 not-checked / 1 not-applicable (of 9). MAY: 5 met / 0 partial / 0 unmet / 0 not-checked (of 5). Total 31 of 31 answered.

## What to fix first

1. **Publish the environment spec and make the input fetchable (must/016, must/002).** The recorded remote refuses anonymous access, and the pinned submodule commit `84570256` is not on the upstream `ds007116` remote, so a stranger cannot obtain either as recorded. Fix: publish the object's remote, and re-pin the module to a commit upstream has.
2. **Make the documented route match what it says (must/011, must/012, must/009).** README line 36 says no environment variable is required and nothing is read from outside; lines 67-68 export a lab-mount path and `/opt/local` FreeSurfer, and no tracked file reads either. Fix: delete the two exports and the "lab filer" sentence, or make a step read them.
3. **Make the lockfile a real lock (must/010).** `requirements.lock` has two package lines and no transitive pins, although its header says `uv pip compile` wrote it. Fix: regenerate it with that command and commit the output.
4. **Make CI exercise what the records name (should/006, should/002).** The CI comment says it must exercise the recorded environment; its steps do not, and its recursive checkout cannot fetch the pinned module commit. Fix: run the container in CI, and make the checkout succeed.
5. **Record an update to the environment spec and archive or document the image (must/014 = should/008, must/017, should/007).** The update command is declared but has never been run; the image is a 28-byte placeholder. Fix: run the update command once and commit it; document how to obtain the image digest, or ship it.

## What the project already does well

- One root, one VCS: git governs the code, the docs and the submodule (`git ls-files`, `.gitmodules`); the tree is clean (`git status` empty).
- Every derived file has a run record (`git log --grep='[DATALAD RUNCMD]'`, commits `4b0813c`, `aba056e`), each naming the container.
- Entry point and layout are documented (`README.md` Install, Layout, Usage; `docs/README.md`; `Makefile` targets).

## Per-item table

| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `.gitmodules`, `git ls-files` | every tracked file sits under the one root; the only external input is the linked submodule inside it |
| must/002 | S.1 | partial ⚠ (a MUST is not satisfied by partial) | probe:subdatasets-resolvable | `.gitmodules`, `git ls-tree HEAD sourcedata/ds007116`, `git fetch --depth`, `git ls-remote https://github.com/OpenNeuroDatasets/ds007116.git` | module url answers, but pinned commit 84570256 is not on the upstream remote (fetch: not our ref); the input cannot be obtained as recorded |
| must/003 | S.1 | met | judgement | `requirements.lock`, `README.md#L22`, `code/collect_volumes.py` | python deps pinned in requirements.lock; no step calls FreeSurfer; apptainer is a documented host requirement (must/012), not analysis software |
| must/004 | T.1,T.3,T.5 | met | probe:tree-clean | `git ls-files`, `git status --porcelain` | git tracks 11 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | T.1,T.3,T.5 | met | probe:large-in-annex | `git ls-tree -r -l HEAD` | No binary blob over 10 MiB in git, and no large-content mechanism is needed: nothing in this object is large binary data. |
| must/006 | T.1,T.3,T.5 | met | probe:derived-have-records | `figures/brain-volume-vs-age.png`, `results/volumes.tsv` | All 2 derived file(s) trace to a re-executable record (2 run record(s), workflows: Makefile). |
| must/007 | A.1 | met | probe:entry-point | `README.md`, `Makefile`, `code/collect_volumes.py`, `code/plot_volumes.py`, `Makefile` | README.md has an install/usage/reproduce section. |
| must/008 | A.1 | met | probe:entry-point | `README.md`, `Makefile`, `code/collect_volumes.py`, `code/plot_volumes.py`, `Makefile` | Starting point present: code/collect_volumes.py. |
| must/009 | P.1 | partial ⚠ (a MUST is not satisfied by partial) | probe:no-abs-paths+judgement | `README.md#L67`, `README.md#L68`, `code/collect_volumes.py` | scripts take paths as arguments and are clean; the documented route exports lab-mount and /opt host paths (README lines 67-68) |
| must/010 | P.1 | partial ⚠ (a MUST is not satisfied by partial) | probe:env-spec-tracked+judgement | `requirements.lock#L1`, `requirements.lock`, `code/requirements.in` | requirements.lock pins only matplotlib and pandas; no transitive pins, though its header says uv pip compile wrote it |
| must/011 | P.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md#L36`, `README.md#L67-L68`, `git grep DS007116|FREESURFER` | README says no env var is needed and nothing is read outside; Reproduce exports DS007116 and FREESURFER_HOME, and no tracked file reads either |
| must/012 | P.2 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md#L22`, `README.md#L64-L68` | system-requirements table omits the lab-filer input and the FREESURFER_HOME=/opt/local/freesurfer-7.4.1 that Reproduce exports |
| must/013 | P.3 | met | probe:env-spec-tracked | `requirements.lock` | Tracked: requirements.lock. |
| must/014 | P.3 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `requirements.lock#L1`, `git log -- requirements.lock` | update process declared (uv pip compile in requirements.lock header); no update in history: declared, no instance in the history yet |
| must/015 | D.1 | met | probe:run-env-linked+judgement | `code/containers.json`, `code/containers/plotting.sif` | image digest pinned in code/containers.json and named by run records; image not shipped, so the digest is not checked against an image |
| must/016 | D.1 | unmet | probe:env-spec-tracked+judgement | `git ls-remote https://github.com/con/stamped-eval-fixture-r0.git (GIT_TERMINAL_PROMPT`, `.git/config remote.origin.url` | recorded remote github.com/con/stamped-eval-fixture-r0 refuses anonymous access, so a stranger cannot fetch the environment spec |
| must/017 | D.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md#L8`, `code/containers/plotting.sif.README`, `code/containers.json` | lockfile route is documented (venv install); the recorded container is not obtainable from the docs: plotting.sif is a placeholder and no step fetches the digest |
| should/001 | T.2 | met | judgement | `.gitmodules`, `git ls-files` | git governs code, docs, configuration and the submodule; no DVC or annex pointers in the tree |
| should/002 | A.2 | partial | probe:ci-present+judgement | `.github/workflows/rerun.yml#L7`, `git ls-tree HEAD sourcedata/ds007116` | CI checks out the module recursively, and the pinned commit is not upstream, so that checkout cannot succeed as published; no CI run inspected |
| should/003 | M.1 | met | probe:modules-separated | `sourcedata`, `sourcedata/ds007116`, `Makefile`, `code`, `figures`, `results`, `code/containers.json`, `requirements.lock` | 4 kinds of component live in distinct places: inputs in sourcedata, sourcedata/ds007116; code in Makefile, code; derived in figures, results; environment in code/containers.json, requirements.lock |
| should/004 | E.1 | met | judgement | `.github/workflows/rerun.yml#L5` | CI runs on ubuntu-latest from a fresh checkout for each push: a clean runner per execution; CI run history not inspected |
| should/005 | E.1 | met | judgement | `commit:aba056e`, `commit:4b0813c` | each recorded execution is one apptainer exec, a fresh container per run; CI starts a fresh runner per job |
| should/006 | D.2 | partial | probe:ci-present+judgement | `.github/workflows/rerun.yml#L10-L15`, `code/containers.json` | CI checks the digest string and tests that plotting.sif exists, then runs make all in a pip venv: the recorded environment is never run |
| should/007 | D.2 | partial | judgement | `requirements.lock`, `code/containers/plotting.sif`, `code/containers/plotting.sif.README` | lockfile archived; the container the run records name is referenced by digest but not archived (placeholder file) |
| should/008 | D.2 | partial | judgement | `requirements.lock#L1`, `git log -- requirements.lock` | same sentence as must/014: update process declared in requirements.lock header, no update in history yet |
| should/009 | M.4 | not-applicable | judgement | `.gitmodules` | N/A: every component is a public module (OpenNeuro ds007116) or project code; no restricted data or software present to isolate |
| may/001 | M.2 | met | probe:subdatasets-resolvable | `.gitmodules` | 1 external component(s) are linked as modules: sourcedata/ds007116 |
| may/002 | M.2 | met | judgement | `README.md#L44`, `docs/README.md` | modular structure documented in README layout table and docs/README.md |
| may/003 | M.2 | met | judgement | `docs/README.md`, `Makefile` | docs/README.md says each part swaps independently; Makefile rules name files, not steps |
| may/004 | M.2 | met | judgement | `Makefile`, `.gitmodules` | composition by Makefile rules over named files and the git submodule for the input |
| may/005 | M.2 | met | judgement | `docs/README.md` | docs/README.md explains how the pieces relate and how to re-run one step |

## Flagged items

- must/009 (`probe:no-abs-paths+judgement`, mapping-questioned): the probe scanned all tracked text; the item asks about scripts, which are clean. I kept the probe's partial because the documented route, which a reader pastes, hardcodes lab and `/opt` paths. Arguable: unmet on scripts, met on docs.
- must/010 (probe-overridden): the probe's met is based on the lock existing; the lock lacks transitive pins.
- must/015 (unverified-claim): digest pinned, but the image is a placeholder; the recorded sha256 `3e0f1b6c...` does not match the tracked `plotting.sif` (`716c2a63...`). Expected for a placeholder, not checked against an image.
- must/016 (probe-overridden): the probe asked for `git ls-remote` before believing a claim; I ran it and it failed without credentials.
- must/014 and should/008 (upstream-duplicate): the same sentence; answered identically from the same evidence.
- should/002 (probe-overridden, unverified-claim): the CI job was not run. The reasoning is from the workflow file and the unfetchable pin.
- should/004 (unverified-claim): based on the workflow file only.
- should/006 (probe-overridden): the probe's met treated "names the same image" as "tests it". The CI does not run the container.
- must/002: confirmed by me, not overridden. Fetch from upstream failed with "not our ref". The shape probe's partial is kept.
- Not a flag: the FIXTURE.md states the module and remote are simulated. I did not use it as evidence; I checked both myself.

## Not checked

- Fresh rerun (`fresh_rerun.py`): not attempted (expensive, no user consent). should/004 is answered from the CI workflow file as equivalent evidence, per the skill.
- Container image digest: not pulled (out of scope per skill).
- CI run history: not inspected (`gh` unauthenticated; not required).
- The Makefile `all` in a clone without `git submodule update --init` was not run (not run per never-run-pipeline rule). Reading the code suggests it would succeed with an empty result; unverified.

## Goals and kind

- Source: README.md (documentation), no user confirmation. Kind `study` assumed. Emphasis: all seven, with T and S weighted.

## Stamp

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on https://github.com/con/stamped-eval-fixture-r0.git (remote as recorded) at commit `52cc39d`, 2026-10-15, claude-code/claude-haiku-5-5.
Probe output: `/home/yoh/proj/CON/skills/.git-meta/scratch/stamped/jm4/readme-host-path-in-instructions/out/2026-10-15-probes.json`.
Response JSON: `.../out/2026-10-15-response.json`. URL: `.../out/2026-10-15-url.txt`.
