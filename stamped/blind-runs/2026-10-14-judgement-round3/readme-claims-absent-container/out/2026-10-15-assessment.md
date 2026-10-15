# STAMPED assessment, 2026-10-15

**Assumption (user unavailable, not confirmed):** goals = reproduce a brain-volume-vs-age study from the FreeSurfer tables of ds007116; kind = study (re-derivation from another dataset's derivatives).
Scope: committed state 3df77ee; --check-remote run; image not pulled; fresh rerun not run; gh unauthenticated (tracker not read).

**MUST: 7 met / 8 partial / 2 unmet / 0 not-checked (of 17). SHOULD: 2 met / 5 partial / 1 unmet / 0 not-checked / 1 not-applicable (of 9). MAY: 5 met (of 5).**

## What to fix first
1. Make README.md#L14 true or remove it: it says every step, `make all`, CI and the run records go through `neurodesk-freesurfer` from `///repronim/containers`; nothing in the tree uses it. Records ran `apptainer exec plotting.sif` (docker://python), Makefile and CI run host python3. Either route Makefile/CI through the registered image or document the two routes honestly (as the parent commit did). Closes must/006, 007, 008, 017, should/002, 005, 006. (The commit 3df77ee that introduced this sentence deleted the honest "two ways to run" paragraph and the Usage section.)
2. Publish the repository and repoint the input: the recorded commit of sourcedata/ds007116 is not upstream and origin returns 404. Closes must/002, must/016, should/004.
3. Document host requirements (make, python3, apptainer, network) and ship or publish the image (28-byte placeholder). Closes must/003, 011, 012, should/007.
4. Record one environment-spec update through the stated `uv pip compile` route. Closes must/014, should/008.

## Already good
- Every derived file has a DATALAD RUNCMD record with the image digest (git 5d7aaa0, 021ff4d).
- Clean modular layout; steps coupled only through files (docs/README.md, Makefile).
- Pinned lockfile with a runnable regeneration command (requirements.lock#L1).

## Per-item table
| id | status | source | reason |
|---|---|---|---|
| must/001 | met | judgement | All tracked files nest under the repo root; the input is a submodule at sourcedata/ds007116, no path outside the root is referenced. |
| must/002 | unmet | probe:subdatasets-resolvable+judgement | Recorded commit 84570256 of sourcedata/ds007116 does not exist upstream (git fetch: 'not our ref'); url answers but a stranger cannot fetch the input. |
| must/003 | partial | judgement | Python deps are pinned and the image is referenced by digest, but the image is a 28-byte placeholder, Makefile assumes host python3 and records assume host apptainer; README names a container not present. |
| must/004 | met | probe:tree-clean | git tracks 11 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | met | probe:large-in-annex | No binary blob over 10 MiB in git, and no large-content mechanism is needed: nothing in this object is large binary data. |
| must/006 | partial | probe:derived-have-records+judgement | Both derived files have run records naming the digest-pinned image, but what the records ran (apptainer exec) differs from what Makefile/README/CI offer to reproduce them (host python3). |
| must/007 | partial | probe:entry-point+judgement | README has Install/Reproduce sections, but they contradict each other and the Makefile: it promises a neurodesk container for every step while `make all` and the venv install use host python3. |
| must/008 | partial | probe:entry-point+judgement | Starting point exists (`make all`, code/collect_volumes.py) but the documented route (container) is not what it runs, and not what the records ran; records use apptainer exec on plotting.sif. |
| must/009 | met | probe:no-abs-paths | No host-specific absolute paths in tracked text files. |
| must/010 | met | probe:env-spec-tracked | matplotlib==3.9.2, pandas==2.2.3 pinned in requirements.lock; no tracked script relies on a pre-installed tool beyond python3/make (see must/011). |
| must/011 | partial | judgement | Host needs make, python3, git submodules, and apptainer for the recorded route; README documents none of it and says 'no local installation is needed', which is false for the Makefile route. |
| must/012 | partial | judgement | No list of system requirements (python3 version, make, apptainer, network for the submodule) in README or specs; the only environment statement is the container claim, which the tree does not support. |
| must/013 | met | probe:env-spec-tracked | Tracked: requirements.lock. |
| must/014 | partial | judgement | Declared in requirements.lock header (`uv pip compile code/requirements.in`) but the lock was added once in 7a2612d and never updated: declared, no instance in history. |
| must/015 | met | probe:run-env-linked | 2 run record(s) reference a pinned image or lockfile, and no ':latest' reference is tracked. |
| must/016 | unmet | probe:env-spec-tracked+judgement | Remote origin https://github.com/con/stamped-eval-fixture-r0.git does not exist (ls-remote asks for credentials, HTTP 404): the tracked specs are not published, and the image is a placeholder. |
| must/017 | partial | judgement | README tells how to build a venv from requirements.lock, but its container instructions point to neurodesk-freesurfer in ///repronim/containers, which the tree does not use; no steps to obtain plotting.sif. |
| should/001 | met | judgement | Git alone covers code, text, the container placeholder and the input (a git submodule); no second version-control system is used. |
| should/002 | partial | probe:ci-present+judgement | CI runs `make all` and diffs outputs, but that is not the documented container route nor what the records ran, and its submodule checkout cannot succeed (pinned commit absent upstream). |
| should/003 | met | probe:modules-separated | 4 kinds of component live in distinct places: inputs in sourcedata, sourcedata/ds007116; code in Makefile, code; derived in figures, results; environment in code/containers.json, requirements.lock |
| should/009 | not-applicable | judgement | N/A: empty subject; the only input (OpenNeuro ds007116) and all software are public, no restricted component exists. |
| should/004 | partial | judgement | CI is designed as a fresh ubuntu-latest run of make all, but it checks out a submodule commit that does not exist and runs host python, not the container; no run is recorded. |
| should/005 | partial | judgement | Run records execute each step as a fresh `apptainer exec` of the image, but the Makefile/CI route reuses host python3; the disposable-per-run claim holds only for the recorded route. |
| should/006 | partial | probe:ci-present+judgement | CI echoes the digest and tests plotting.sif exists, but runs make all in a pip environment; the environment the results came from (container) is never reconstituted. |
| should/007 | unmet | judgement | Image is not archived: code/containers/plotting.sif is a 28-byte placeholder; only the digest is referenced. Ship the image via git-annex or publish it. |
| should/008 | partial | judgement | Declared in requirements.lock header (`uv pip compile code/requirements.in`) but the lock was added once in 7a2612d and never updated: declared, no instance in history. |
| may/001 | met | probe:subdatasets-resolvable+judgement | sourcedata/ds007116 is linked as a git submodule (.gitmodules); structural answer only, resolvability is must/002. |
| may/002 | met | judgement | README layout table and docs/README.md explain how input, steps, container and products relate and recombine (note: docs/README.md also repeats the false container claim). |
| may/003 | met | judgement | collect_volumes.py is the only step knowing the input layout; plot reads only results/volumes.tsv; Makefile couples by file names, so steps and input can be swapped independently. |
| may/004 | met | judgement | Composition: git submodule for the input and a Makefile joining steps through files; the image pinned by digest in containers.json. |
| may/005 | met | judgement | docs/README.md is a navigation guide (where things are, how to re-run one step) and README has a layout table. |

## Flagged items
- must/002: probe-overridden (probe:subdatasets-resolvable+judgement)
- must/003: unverified-claim (judgement)
- must/006: probe-overridden (probe:derived-have-records+judgement)
- must/007: probe-overridden,mapping-questioned (probe:entry-point+judgement)
- must/008: probe-overridden,mapping-questioned (probe:entry-point+judgement)
- must/014: upstream-duplicate (judgement)
- must/016: probe-overridden (probe:env-spec-tracked+judgement)
- should/002: probe-overridden (probe:ci-present+judgement)
- should/006: probe-overridden,mapping-questioned (probe:ci-present+judgement)
- should/008: upstream-duplicate (judgement)
- may/001: mapping-questioned (probe:subdatasets-resolvable+judgement)

## Not checked
None. Image digest not verified by pulling (placeholder image anyway).

## Goals and kind
See assumption above. Study; S and T weighted most.

## Extra findings
- readme-container-claim-absent (unmet); licence MIT in LICENSE (met); FIXTURE.md self-report re-derived, it names the pin and the remote but not the README claim.

URL: see 2026-10-15-url.txt. Response: 2026-10-15-response.json. Probe output: 2026-10-15-probes.json.
Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on https://github.com/con/stamped-eval-fixture-r0.git (unpublished) at commit `3df77ee`, 2026-10-15, claude-code/claude-sonnet-5-5.
