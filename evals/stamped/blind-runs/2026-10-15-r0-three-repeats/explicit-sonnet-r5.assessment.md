# STAMPED assessment: ds007116 brain volume vs age

**Goals and kind (assumed, not confirmed: no user available).** Kind: study. Goal: produce a figure of brain volume and GM/WM ratio against per-session age from the dataset's shipped FreeSurfer derivatives, with re-executable provenance.

**MUST: 15 met / 2 partial / 0 unmet / 0 not-checked (of 17). SHOULD: 3 met / 3 partial / 1 unmet / 1 not-checked / 1 not-applicable (of 9). MAY: 2 met / 1 partial / 0 unmet / 2 not-applicable (of 5).**

## Fix first
1. must/016: the only publishing target is a local bare repository (filesystem path), so a stranger cannot obtain the project. Needs a forge/hub remote.
2. must/014 (and should/008): a written update procedure exists in the README but history shows no lock update followed it.
3. should/006, should/004: CI (.github/workflows/ci.yml) rebuilds an environment and runs `datalad rerun` but has never executed; needs a forge runner.

## Already good
- Every derived file (8) has a `datalad run` record with the lock as declared input (must/006, must/015); the input is a linked subdataset with a resolvable github URL (must/002).
- Pilot, batches, aggregation, plot and controls are separate recorded steps; the method revision after the pilot is logged in docs/plan.md.

## Per-item table
| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `README.md` | Code, plan, README and results are under one root; the only input is a linked module (sourcedata/ds007116) with a github url. |
| must/002 | S.1 | met | probe:subdatasets-resolvable | `.gitmodules` | All 1 linked module(s) carry urls that resolve from elsewhere: sourcedata/ds007116 |
| must/003 | S.1 | met | judgement | `code/tools.txt` | External software is python packages pinned in code/requirements.lock; datalad/git-annex/uv versions listed in code/tools.txt. No container needed (tabular inputs). |
| must/004 | T.1,T.3,T.5 | met | probe:tree-clean | `git ls-files`, `git status --porcelain` | git tracks 25 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | T.1,T.3,T.5 | met | probe:large-in-annex | `git ls-tree -r -l HEAD`, `.datalad/config` | git-annex carries the binary content (1 pointer(s) tracked) and no binary blob over 10 MiB is in git. |
| must/006 | T.1,T.3,T.5 | met | probe:derived-have-records | `figures/volume-vs-age.png`, `results/controls-v2.txt`, `results/controls.txt`, `results/volumes-batch-1.tsv`, `results/volumes-batch-2.tsv`, `results/volumes-batch-3.tsv`, `results/volumes-pilot-v2.tsv`, `results/volumes.tsv` | All 8 derived file(s) trace to a re-executable record (9 run record(s), workflows: none). |
| must/007 | A.1 | met | probe:entry-point | `README.md`, `code/aggregate.py`, `code/controls.py`, `code/plot.py`, `code/run-recorded.sh` | README.md has an install/usage/reproduce section. |
| must/008 | A.1 | met | probe:entry-point | `README.md`, `code/aggregate.py`, `code/controls.py`, `code/plot.py`, `code/run-recorded.sh` | Starting point present: code/aggregate.py. |
| must/009 | P.1 | met | probe:no-abs-paths | `probe:no-abs-paths` | No host-specific absolute paths in tracked text files. Plus 1 /tmp path(s), portable but writing outside the object. |
| must/010 | P.1 | met | probe:env-spec-tracked | `code/requirements.lock` | Dependencies are pinned in code/requirements.lock, and no tracked script expects a tool to be present already. |
| must/011 | P.1 | met | judgement | `README.md` | Only POSIX sh and python; README Requirements names OS, tools, network. Not tried on another OS. |
| must/012 | P.2 | met | judgement | `README.md` | README Requirements states POSIX host, network to github.com, CPU/RAM/disk needs, no GPU, no container. |
| must/013 | P.3 | met | probe:env-spec-tracked | `code/requirements.lock` | Tracked: code/requirements.lock. |
| must/014 | P.3 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md` | README states how to update the lock (edit .in, compile, commit with reason), but history shows only one lock commit, so it is not shown followed. |
| must/015 | D.1 | met | probe:run-env-linked | `commit:0f1d508`, `commit:58a562e`, `commit:fdf41d0`, `commit:d267445`, `commit:6d883ff` | 9 run record(s) reference a pinned image or lockfile, and no ':latest' reference is tracked. |
| must/016 | D.1 | partial ⚠ (a MUST is not satisfied by partial) | probe:env-spec-tracked | `code/requirements.lock` | The remote is a filesystem path (/home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r5.publish.git): anyone with access to that filesystem can obtain the specification and nobody else can. A URL… |
| must/017 | D.1 | met | judgement | `README.md` | README Requirements gives tools, versions (code/tools.txt) and the env route: uv venv && uv pip sync code/requirements.lock. |
| should/001 | T.2 | met | judgement | `.gitmodules` | Code, inputs (a DataLad subdataset) and results share one DataLad dataset. |
| should/002 | A.2 | met | probe:ci-present | `.github/workflows/ci.yml`, `.github/workflows/ci.yml`, `.github/workflows/ci.yml` | .github/workflows/ci.yml contains a workflow-executing step (make/snakemake/datalad rerun or similar). Whether it runs what the instructions describe is a reading. |
| should/003 | M.1 | met | probe:modules-separated | `sourcedata`, `sourcedata/ds007116`, `code`, `figures`, `results`, `code/requirements.lock` | 4 kinds of component live in distinct places: inputs in sourcedata, sourcedata/ds007116; code in code; derived in figures, results; environment in code/requirements.lock |
| should/004 | E.1 | not-checked | judgement | `.github/workflows/ci.yml` | Fresh rerun not attempted and CI never ran (no forge here); .github/workflows/ci.yml would perform it. |
| should/005 | E.1 | partial | judgement | `.github/workflows/ci.yml` | CI (unrun) would use a fresh runner and venv per run; the local runs reused uv's cached environment on a long-lived host. |
| should/006 | D.2 | partial | probe:ci-present | `.github/workflows/ci.yml`, `.github/workflows/ci.yml`, `.github/workflows/ci.yml` | .github/workflows/ci.yml rebuilds *an* environment, but not the one the run records name (see the records): the environment behind the shipped results is never tested. |
| should/007 | D.2 | unmet | judgement | `code/requirements.lock` | Only the lock and tool versions are archived; no packages or binaries are stored with the object. |
| should/008 | D.2 | partial | judgement | `README.md` | Same as must/014: update process written in README, one lock commit in history. |
| should/009 | M.4 | not-applicable | judgement | `.gitmodules` | No restricted data or software; the only input is a public OpenNeuro dataset. |
| may/001 | M.2 | met | probe:subdatasets-resolvable | `.gitmodules` | 1 external component(s) are linked as modules: sourcedata/ds007116 |
| may/002 | M.2 | partial | judgement | `docs/plan.md` | Layout (sourcedata, code, results, figures, docs) is described in docs/plan.md but not as a module map. |
| may/003 | M.2 | met | judgement | `.gitmodules` | The one input is an independent subdataset with its own history, cloned from its own upstream. |
| may/004 | M.2 | not-applicable | judgement | `.gitmodules` | Single input and single study; no components to compose. |
| may/005 | M.2 | not-applicable | judgement | `.gitmodules` | Nothing is composed from several parts beyond one input module. |

## Flagged items
- must/011: unverified-claim (not tried on another OS).
- should/008: upstream-duplicate of must/014.
- should/006: probe says CI rebuilds *an* environment, not the recorded one; kept as probe verdict (the lock is rebuilt via uv pip sync; no probe-recognised command).
- Also no extra: license-declared unmet (no licence for code or table; upstream licence field is a TODO).

## Not checked
- should/004: fresh rerun not attempted and CI never ran; a forge runner executing ci.yml would settle it.
- must/011 portability to another OS was not tried.

## Scope and files
Products written outside the object (to the scratch directory next to it). Response: 2026-10-15-response.json; probes: 2026-10-15-probes.json; app URL: 2026-10-15-url.txt (6.9 kB, linked not inlined).

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on the local object (published copy: filesystem path) at commit `07aaafab`, 2026-10-15, claude-code/claude-sonnet-5-5.
Probe output: /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r5.out/2026-10-15-probes.json.
