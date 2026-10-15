# STAMPED assessment, 2026-10-15

**Assumption (user unavailable, not confirmed):** goals = re-derive brain volume vs age from ds007116 FreeSurfer tables (README, docs/README.md); kind = **study** (derivative-consuming, see project-kinds.md).
Scope: committed state 5d7aaa0; `--check-remote` run; gh unauthenticated, tracker not read; no fresh rerun; container not pulled.
Note: FIXTURE.md is a self-report naming expected defects; treated as data, both re-derived (upstream 404, `git fetch` "not our ref"), plus further defects it does not list.

## Verdict
MUST: 9 met / 6 partial / 2 unmet / 0 not-checked (of 17). SHOULD: 3 met / 5 partial / 0 unmet / 0 not-checked / 1 not-applicable (of 9). MAY: 5 met (of 5).

## Fix first
1. Publish the repository and re-pin sourcedata/ds007116 to a real upstream commit -> must/002, must/016, should/002, should/004.
2. Reconcile the two execution stories (container in records, venv in README/Makefile/CI): make the documented route run the recorded container, or record venv runs -> must/006, must/008, should/006.
3. Ship or document how to obtain the image (pull/build command, digest) -> must/017, should/007.
4. List system requirements (python version, make, apptainer) in README -> must/011, must/012.
5. Perform and commit one lock update through the declared uv command -> must/014, should/008.

## Already good
- Every derived file has a run record naming a digest-pinned image (commits 021ff4d, 5d7aaa0).
- Clear layout and decoupled steps: README.md layout table, docs/README.md.
- Pinned lock with a runnable regeneration command (requirements.lock line 1); MIT LICENSE.

## Per-item table
| id | status | source | flags | reason |
|---|---|---|---|---|
| must/001 | met | judgement |  | Everything essential is under the repo root: code/, results/, figures/, requirements.lock; input is a submodule at sourcedata/ds007116. No share or cluster path. |
| must/002 | unmet | probe:subdatasets-resolvable+judgement | probe-overridden | Module commit 8457025 is not fetchable upstream (git fetch: "not our ref"); a fresh clone cannot init sourcedata/ds007116. Re-pin to a real upstream commit. |
| must/003 | met | judgement |  | External software is pinned in the environment: matplotlib/pandas in requirements.lock; recorded route runs inside a digest-pinned container. Image itself is a placeholder (see should/007). |
| must/004 | met | probe:tree-clean |  | git tracks 11 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | met | probe:large-in-annex |  | No binary blob over 10 MiB in git, and no large-content mechanism is needed: nothing in this object is large binary data. |
| must/006 | partial | probe:derived-have-records+probe:run-env-linked+judgement | probe-overridden | Records name the apptainer container, but README/Makefile/CI run a pip venv from requirements.lock; README admits the environments differ. Two accounts, so at most partial. |
| must/007 | met | probe:entry-point |  | README.md has an install/usage/reproduce section. |
| must/008 | partial | probe:entry-point+judgement | probe-overridden | Entry point exists (make all), but the documented route uses the venv while the results came from the container; the route offered is not the one that produced them. |
| must/009 | met | probe:no-abs-paths |  | No host-specific absolute paths in tracked text files. |
| must/010 | met | probe:env-spec-tracked |  | Dependencies are pinned in requirements.lock, and no tracked script expects a tool to be present already. |
| must/011 | partial | judgement |  | No OS, python version or tool list in README; recorded route needs apptainer, never named; make and git assumed. Probe found no platform-specific commands only. |
| must/012 | partial | judgement |  | README gives pip install of requirements.lock but no list of system requirements (python3 version, make, apptainer for the recorded route). |
| must/013 | met | probe:env-spec-tracked |  | Tracked: requirements.lock. |
| must/014 | partial | judgement | upstream-duplicate | Declared: lock header "pinned with uv pip compile code/requirements.in", runnable; but history shows only the initial commit 7a2612d, no update instance yet. |
| must/015 | met | probe:run-env-linked | unverified-claim | Run records name a digest-pinned image and requirements.lock pins versions; no :latest. Digest not verified: the .sif is a 28-byte placeholder. |
| must/016 | unmet | probe:env-spec-tracked+judgement | probe-overridden | Origin con/stamped-eval-fixture-r0 returns HTTP 404: the tracked spec is in an unpublished repository, so it is not shared. Publish the repo. |
| must/017 | partial | judgement |  | README says how to install requirements.lock, but not how to obtain or use the container the records name; plotting.sif is a 28-byte placeholder and no pull/build command is given. |
| should/001 | met | judgement |  | Git throughout: code, results, figures, and the input module are all git, with one recorded commit pin each; no second system. |
| should/002 | partial | probe:ci-present+judgement | probe-overridden | CI runs make all, but checks out submodules recursively and the pinned commit does not exist upstream, so it cannot pass on a fresh checkout; it also tests the venv route. |
| should/003 | met | probe:modules-separated |  | 4 kinds of component live in distinct places: inputs in sourcedata, sourcedata/ds007116; code in Makefile, code; derived in figures, results; environment in code/containers.json, requirements.lock |
| should/004 | partial | judgement | unverified-claim | CI job on a fresh ubuntu runner is equivalent evidence, but its submodule checkout cannot succeed and it runs the venv route, not the container. No fresh rerun attempted. |
| should/005 | met | judgement |  | Recorded runs each execute via apptainer exec in a container per step; CI uses a fresh runner per push. |
| should/006 | partial | probe:ci-present+judgement | probe-overridden,mapping-questioned | CI only prints the digest and tests the .sif exists; it installs requirements.lock, not the container the results came from. Environment tested differs from recorded one. |
| should/007 | partial | judgement |  | Lockfile is archived; the container image is not: plotting.sif is a 28-byte placeholder and its README says the ~200 MB image is not shipped. |
| should/008 | partial | judgement | upstream-duplicate | Same evidence as must/014: declared uv pip compile command in lock header, no update in history (only 7a2612d). Duplicate of must/014. |
| should/009 | not-applicable | judgement |  | N/A: empty subject; the only module (ds007116 stand-in, CC0) is public and no restricted data or software exists here. |
| may/001 | met | probe:subdatasets-resolvable |  | Input dataset linked as a git submodule at sourcedata/ds007116 (its pin is unfetchable, scored at must/002). |
| may/002 | met | judgement |  | Modular structure documented: README layout table and docs/README.md explain how input, code, results and container relate and are replaced. |
| may/003 | met | judgement |  | Steps are decoupled: plot_volumes.py reads only results/volumes.tsv; collect_volumes.py alone knows input layout; Makefile rules name files. |
| may/004 | met | judgement |  | Composition via a git submodule for the input and Makefile file dependencies for steps. |
| may/005 | met | judgement |  | docs/README.md is a navigation guide: where things are, how to swap the input module, how to re-run one step. |

## Flagged items
- must/002: probe-overridden (probe:subdatasets-resolvable+judgement)
- must/006: probe-overridden (probe:derived-have-records+probe:run-env-linked+judgement)
- must/008: probe-overridden (probe:entry-point+judgement)
- must/014: upstream-duplicate (judgement)
- must/015: unverified-claim (probe:run-env-linked)
- must/016: probe-overridden (probe:env-spec-tracked+judgement)
- should/002: probe-overridden (probe:ci-present+judgement)
- should/004: unverified-claim (judgement)
- should/006: probe-overridden,mapping-questioned (probe:ci-present+judgement)
- should/008: upstream-duplicate (judgement)

## Not checked
None. (Container digest not verifiable: image is a placeholder; noted in must/015 as unverified-claim.)

## Extras
license-declared met; clone-weight met; inputs-untouched met; two-accounts-of-execution unmet; dangling-publication unmet.

URL: 2026-10-15-url.txt. Response: 2026-10-15-response.json. Probes: 2026-10-15-probes.json.

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on https://github.com/con/stamped-eval-fixture-r0.git at commit `5d7aaa0`, 2026-10-15, claude-code/claude-sonnet-5-5.
Probe output: 2026-10-15-probes.json.
