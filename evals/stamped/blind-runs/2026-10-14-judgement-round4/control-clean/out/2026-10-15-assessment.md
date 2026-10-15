# STAMPED assessment: brain volume vs age (R0 fixture)

**ASSUMPTION (user unavailable, not confirmed):** goals = reproducibly derive brain volume vs age from ds007116 FreeSurfer tables (README, docs/README.md); kind = **study** (re-derivation from another dataset's derivatives).
Scope: committed state aba056e; probes with --check-remote; container not pulled; CI/fresh rerun not run; gh unauthenticated, tracker not consulted.
Note: FIXTURE.md in the object names expected defects; treated as data and re-derived (both confirmed independently).

**MUST: 14 met / 1 partial / 2 unmet / 0 not-checked (of 17). SHOULD: 5 met / 3 partial / 0 unmet / 0 not-checked / 1 not-applicable (of 9). MAY: 5 met (of 5).**

## What to fix first
1. Re-pin sourcedata/ds007116 to a commit that exists upstream -> a fresh clone can init the input (must/002; also unblocks CI).
2. Publish the repository (the recorded remote does not exist) -> others can retrieve the specs (must/016).
3. Make CI exercise the recorded container (or ship the real image) and record an update to requirements.lock -> should/006, should/007, must/014, should/008.

## Already good
- Every derived file has a run record naming a digest-pinned container (probe derived-have-records, run-env-linked).
- README states system requirements and honestly discloses the two run routes.
- docs/README.md documents the modular structure; Makefile couples steps only via files.

## Per-item table
| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `README.md#layout`, `.gitmodules` | All code, results, CI and the input module (sourcedata/ds007116, a gitlink) sit under the repo root; nothing lives only on a share. |
| must/002 | S.1 | unmet | probe:subdatasets-resolvable+judgement | `.gitmodules`, `git ls-tree HEAD sourcedata`, `git fetch --depth` | Recorded commit 8457025 of sourcedata/ds007116 does not exist upstream (git fetch: not our ref); fresh-clone submodule init fails. Re-pin to a published commit. |
| must/003 | S.1 | met | judgement | `requirements.lock`, `README.md#system-requirements` | Python deps pinned in requirements.lock (matplotlib, pandas); the only external data is a linked module; no tool assumed present beyond python3/make/git. |
| must/004 | T.1,T.3,T.5 | met | probe:tree-clean | `git ls-files`, `git status --porcelain` | git tracks 11 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | T.1,T.3,T.5 | met | probe:large-in-annex | `git ls-tree -r -l HEAD` | No binary blob over 10 MiB in git, and no large-content mechanism is needed: nothing in this object is large binary data. |
| must/006 | T.1,T.3,T.5 | met | probe:derived-have-records | `figures/brain-volume-vs-age.png`, `results/volumes.tsv` | All 2 derived file(s) trace to a re-executable record (2 run record(s), workflows: Makefile). |
| must/007 | A.1 | met | probe:entry-point | `README.md`, `Makefile`, `code/collect_volumes.py`, `code/plot_volumes.py`, `Makefile` | README.md has an install/usage/reproduce section. |
| must/008 | A.1 | met | probe:entry-point | `README.md`, `Makefile`, `code/collect_volumes.py`, `code/plot_volumes.py`, `Makefile` | Starting point present: code/collect_volumes.py. |
| must/009 | P.1 | met | probe:no-abs-paths | `probe:no-abs-paths` | No host-specific absolute paths in tracked text files. |
| must/010 | P.1 | met | probe:env-spec-tracked | `requirements.lock` | Dependencies are pinned in requirements.lock, and no tracked script expects a tool to be present already. |
| must/011 | P.1 | met | judgement | `README.md#system-requirements` | README System requirements table lists shell, make, git, python3>=3.11, lock packages, apptainer (recorded route only), network once; says no env vars needed. |
| must/012 | P.2 | met | judgement | `README.md#system-requirements`, `requirements.lock` | README lists system requirements and versions; requirements.lock pins packages; CI workflow installs the same lock on ubuntu-latest. |
| must/013 | P.3 | met | probe:env-spec-tracked | `requirements.lock` | Tracked: requirements.lock. |
| must/014 | P.3 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `requirements.lock#L1`, `git log -- requirements.lock` | Process declared (requirements.lock header: uv pip compile code/requirements.in) but no update appears in history: lock only in the initial commit. |
| must/015 | D.1 | met | probe:run-env-linked | `commit:aba056e`, `commit:4b0813c` | 2 run record(s) reference a pinned image or lockfile, and no ':latest' reference is tracked. |
| must/016 | D.1 | unmet | probe:env-spec-tracked+judgement | `.git/config`, `GIT_TERMINAL_PROMPT` | Recorded remote github.com/con/stamped-eval-fixture-r0 does not exist: git ls-remote with prompts disabled fails; specs are tracked but not shared. Publish it. |
| must/017 | D.1 | met | judgement | `README.md#install`, `code/containers.json` | README Install gives the venv + pip install -r requirements.lock command; recorded container route is explained; image not pulled/verified. |
| should/001 | T.2 | met | judgement | `git ls-files`, `.gitmodules` | Everything, including the input module, is plain git; no second VCS (no annex, DVC or LFS) in the tree. |
| should/002 | A.2 | met | probe:ci-present | `.github/workflows/rerun.yml` | rerun.yml runs make all and diffs outputs on push/PR; no CI run history seen, and its submodule checkout would fail on the missing commit (must/002). |
| should/003 | M.1 | met | probe:modules-separated | `sourcedata`, `sourcedata/ds007116`, `Makefile`, `code`, `figures`, `results`, `code/containers.json`, `requirements.lock` | 4 kinds of component live in distinct places: inputs in sourcedata, sourcedata/ds007116; code in Makefile, code; derived in figures, results; environment in code/containers.json, requirements.lock |
| should/004 | E.1 | met | judgement | `.github/workflows/rerun.yml` | CI checks out into a fresh ubuntu-latest runner and runs make all (equivalent evidence); never observed to pass, as the module commit is unfetchable. |
| should/005 | E.1 | met | judgement | `commit:aba056e`, `.github/workflows/rerun.yml` | Recorded runs use apptainer exec per invocation (disposable container); CI uses a fresh runner per push. |
| should/006 | D.2 | partial | probe:ci-present+judgement | `.github/workflows/rerun.yml` | CI only prints the container digest and test -e the .sif, then runs make all on requirements.lock; the recorded container environment is never rebuilt or run in CI. |
| should/007 | D.2 | partial | judgement | `code/containers/plotting.sif.README`, `code/containers.json` | code/containers/plotting.sif is a 28-byte placeholder, not an image; registration points at docker://python with a digest. Only the lockfile is truly archived. |
| should/008 | D.2 | partial | judgement | `requirements.lock#L1`, `git log -- requirements.lock` | Process declared (requirements.lock header: uv pip compile code/requirements.in) but no update appears in history: lock only in the initial commit. |
| should/009 | M.4 | not-applicable | judgement | — | N/A: empty subject, the only external component (ds007116, public OpenNeuro) and all software are public; nothing restricted exists to isolate. |
| may/001 | M.2 | met | probe:subdatasets-resolvable | `.gitmodules` | 1 external component(s) are linked as modules: sourcedata/ds007116 |
| may/002 | M.2 | met | judgement | `docs/README.md`, `README.md#layout` | docs/README.md and README layout table explain how inputs, steps, container and results relate and recombine. |
| may/003 | M.2 | met | judgement | `Makefile`, `docs/README.md` | Steps couple only through files in Makefile; collect step alone knows input layout, so module, container or plot can change independently. |
| may/004 | M.2 | met | judgement | `.gitmodules`, `Makefile` | Composition is a git submodule (sourcedata/ds007116) plus Makefile rules naming files. |
| may/005 | M.2 | met | judgement | `docs/README.md` | docs/README.md is a navigation note: where things are, and how to re-run one step. |

## Flagged items
- must/002: probe said partial; overridden to unmet (commit not fetchable from the url; fresh init fails).
- must/016: probe said partial (remote unchecked); git ls-remote shows the repository does not exist -> unmet.
- should/006: probe met; CI never rebuilds the recorded container -> partial.
- must/014, should/008: upstream-duplicate, same evidence.
- must/017, should/002, should/004: unverified-claim (no image pull, no CI history).

## Not checked
None.

## Goals and kind
As assumed above: study; emphasis T and S.

URL: see 2026-10-15-url.txt. Response: 2026-10-15-response.json. Probes: 2026-10-15-probes.json.

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on https://github.com/con/stamped-eval-fixture-r0.git at commit `aba056e`, 2026-10-15, claude-code/claude-sonnet-5-5.
Probe output: 2026-10-15-probes.json.
