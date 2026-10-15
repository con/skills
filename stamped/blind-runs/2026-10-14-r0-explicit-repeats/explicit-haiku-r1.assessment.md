# STAMPED assessment: r0-freesurfer-plot (study), 2026-10-15

Assumptions, labelled: kind `study` (the project derives a figure and table from a published dataset's derivatives); goals taken from README.md. No user was available to confirm either.

**Verdict.** MUST items: 12 met, 4 partial, 1 unmet, 0 not-checked, of 17. All 31 items answered (17 met, 8 partial, 5 unmet, 1 not-applicable).

## What to fix first
1. must/006 and must/015: five of seven run records name only the host `.venv`; the two container records name the image, but the probe did not recognise it (its regex wants `.sif`). Fix: re-run the remaining host records in the container, or accept partial with this reason.
2. must/016 and should/002: no published remote and no CI. Publish the dataset and add a workflow that re-runs the batch on a small subset.
3. must/014 and should/008: no stated process for updating `code/requirements.lock`.

## Already good
Raw data is a linked subdataset pinned to a commit; the tree is clean; the environment is locked and the container is registered and stored in the annex; the batch was re-derived in the container with identical output.

## Flagged items
- 006: partial, flags ['probe-overridden']. Container-run records name the image (cmd and extra_inputs); 5 of 7 records (pilot, host batch, host figure, host summary) name only .venv, not a lockfile or image.
- 014: unmet, flags ['upstream-duplicate']. No stated process for updating code/requirements.lock; history shows one creation and no update.
- 008: unmet, flags ['upstream-duplicate']. Same as must/014: no stated update process for the environment specification.
- must/006: the probe reported unmet; judgement overrides to partial because the container records do name the image. Probe regex gap noted.

## Not checked

## Per-item table
| item | status | reason |
|---|---|---|
| 001 | met | Everything in the root is tracked; raw data is a linked subdataset (sourcedata/ds007116), not copies. |
| 002 | met | All 1 linked module(s) carry urls that resolve from elsewhere: sourcedata/ds007116 |
| 003 | met | Python packages are in code/requirements.lock; the run container py313 is registered in .datalad/config. |
| 004 | met | git tracks 17 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| 005 | met | git-annex carries the binary content (4 pointer(s) tracked) and no binary blob over 10 MiB is in git. |
| 006 | partial | Container-run records name the image (cmd and extra_inputs); 5 of 7 records (pilot, host batch, host figure, host summary) name only .venv, not a lockfile or image. |
| 007 | met | README.md has an install/usage/reproduce section. |
| 008 | met | Starting point present: code/collect_volumes.py. |
| 009 | met | No host-specific absolute paths in tracked text files. |
| 010 | met | Dependencies are pinned in .datalad/config, code/requirements.lock, and no tracked script expects a tool to be present already. |
| 011 | partial | Host tools (datalad, git-annex, apptainer, uv) are named in README Requirements, but the Linux and /bin/sh assumptions are only partly stated. |
| 012 | met | README 'Requirements' lists host tools, versions used, container image and Python lock. |
| 013 | met | Tracked: .datalad/config, code/requirements.lock. |
| 014 | unmet | No stated process for updating code/requirements.lock; history shows one creation and no update. |
| 015 | partial | Packages are pinned by lock; the image is registered by file (sha256 prefix in README) but its python:3.13-slim source tag is floating, not a digest. |
| 016 | partial | Specification is tracked, but this checkout has no published remote, so no one else can retrieve it yet. |
| 017 | met | README 'Entry point and reproduce' and code/setup-env.sh explain obtaining and using the environment. |
| 001 | met | Both the superdataset and the subdataset are DataLad/git-annex repositories; one toolchain. |
| 002 | unmet | No CI; the workflow is not re-executed automatically. |
| 003 | met | 4 kinds of component live in distinct places: inputs in sourcedata, sourcedata/ds007116; code in code; derived in figures, results; environment in code/requirements.lock |
| 009 | not-applicable | No restricted data or software in the project; the input is a public OpenNeuro dataset (CC0). |
| 004 | unmet | The pipeline was not tested in a fresh container, batch job or clean VM; one batch was re-derived in the container and matched byte for byte. |
| 005 | partial | Batch and summary ran each in a fresh apptainer exec; the pilot and first figure ran on a host venv. |
| 006 | unmet | Reconstitution of results was checked once (batch re-derivation, identical output) and is not a regular test. |
| 007 | met | The container image is annexed inside the dataset at .datalad/environments/py313/image. |
| 008 | unmet | Same as must/014: no stated update process for the environment specification. |
| 001 | met | 1 external component(s) are linked as modules: sourcedata/ds007116 |
| 002 | partial | README describes inputs, code and results, but not the module structure as a whole. |
| 003 | partial | The raw-data subdataset can be updated independently; the code is not tested against other input versions. |
| 004 | met | Composition is by DataLad subdataset and by run wrappers (code/run-recorded.sh). |
| 005 | partial | README gives a file-by-file entry point, but no module diagram. |

## Stamp
checklist 0.3.1; assessor assess-alignment-with-stamped-principles 0.1.0; harness Claude Code; model claude-haiku-5-5; date 2026-10-15; object commit 4dd6015e.

The response JSON is `2026-10-15-response.json` and the probes are `2026-10-15-probes.json` in this directory; the app URL is in `2026-10-15-url.txt`.
