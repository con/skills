# STAMPED assessment — stamped-eval-fixture-r0 (`clean`, commit `55e35e5`)

## Verdict

- **MUST: 11 met / 5 partial / 1 unmet / 0 not-checked** (of 17)
- **SHOULD: 5 met / 3 partial / 0 unmet / 0 not-checked / 1 not-applicable** (of 9)
- **MAY: 5 met / 0 partial / 0 unmet / 0 not-checked** (of 5)

No single overall score, per convention. All 31 items answered; validated against checklist 0.3.1 (`encode_response.py validate` — `ok: 31 answers`).

## What to fix first

1. **Make the documented route actually use the pinned environment.**
   README.md says the analysis "runs inside the container pinned in `code/containers.json`," but `Makefile`'s two targets call `python3 code/collect_volumes.py` / `python3 code/plot_volumes.py` directly, and `.github/workflows/rerun.yml` runs `make all` the same way after a bare `pip install -r requirements.lock` — neither ever execs `code/containers/plotting.sif`. The only place the container is actually used is in the two `[DATALAD RUNCMD]` run records that already produced `results/volumes.tsv` and `figures/brain-volume-vs-age.png` (e.g. commit `0edcc7e`: `apptainer exec code/containers/plotting.sif python3 code/collect_volumes.py ...`). A reader who follows the README/Makefile today reproduces with *some* Python environment, not the recorded one. Fix: have the Makefile (and CI) call through `apptainer exec`, or record future runs the same way the Makefile actually executes them, so the three accounts (docs, Makefile/CI, run records) agree. **Closes:** must/007, must/008, must/017, should/005, should/006.
2. **Make what is already linked actually retrievable.** The submodule `sourcedata/ds007116` points at `https://github.com/OpenNeuroDatasets/ds007116.git`, a real and reachable repository (HTTP 200), but the pinned commit `84570256a...` does not exist there (`git fetch --depth=1` → `not our ref`). Separately, `remote.origin.url` names `https://github.com/con/stamped-eval-fixture-r0.git`, which returns HTTP 404 — nobody but this checkout can obtain the tracked environment spec from it. Fix: pin the submodule to a commit that is actually on `ds007116`'s `main`, and either publish the object at the recorded remote or update `remote.origin.url` to wherever it will actually live. **Closes:** must/002, must/016.
3. **Exercise the declared environment-update process once.** `requirements.lock` already documents its own regeneration command (`# pinned with uv pip compile code/requirements.in`), but the object is one commit deep and that file (and `code/containers.json`) has never been touched since. The process is declared, not yet demonstrated. Fix: the next time a dependency changes, run the documented command and commit the result — one real instance is what turns this from "declared" into "met." **Closes:** must/014, should/008.

## What this object already does well

- **Every derived file traces to a re-executable, environment-naming run record.** `results/volumes.tsv` and `figures/brain-volume-vs-age.png` are each the sole output of a `[DATALAD RUNCMD]` commit (`0edcc7e`, `55e35e5`) whose `run_info` names the exact `apptainer exec code/containers/plotting.sif ...` command, its inputs and its digest-pinned image — not just "the project uses DataLad," an actual citable record per run (must/006, must/015).
- **Modules are cleanly separated and the separation is documented twice.** `sourcedata/` (input, never written to), `code/` (steps + env registration), `results/`/`figures/` (products), and `requirements.lock`/`code/containers.json` (environment) sit in distinct places (should/003), and both `README.md`'s Layout table and `docs/README.md`'s four-point walkthrough explain how they relate and can be swapped (may/002–005).
- **No undocumented host lock-in anywhere in the tracked tree.** A scan of all 17 tracked paths found no absolute host-specific paths, no unnamed platform-specific command (`brew`, BSD `sed -i ''`, `sbatch`, …), and the dependency set is fully pinned by version in `requirements.lock` (must/009, must/010, must/011, must/012).

## Per-item table

### MUST

| id | principle | status | evidence (first) | reason |
|---|---|---|---|---|
| must/001 | S.1 | met | git ls-files | All 17 tracked paths (code, docs, results, figures, env specs, and the sourcedata submodule) sit under this one repository root; nothing essential is referenced only on a share, cluster path or in prose. |
| must/002 | S.1 | partial | .gitmodules | `subdatasets-resolvable --check-remote`: the url resolves, but commit 84570256a is not fetchable from it (`git fetch --depth=1` fails 'not our ref'); confirmed independently, matches FIXTURE.md's own disclosure. |
| must/003 | S.1 | met | code/containers.json | code/containers/plotting.sif (digest-pinned in code/containers.json) and requirements.lock carry the external software — the base Python image and matplotlib/pandas — inside the project boundary, not merely assumed present. |
| must/004 | T.1,T.3,T.5 | met | git ls-files | git tracks 11 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | T.1,T.3,T.5 | met | git ls-tree -r -l HEAD | No binary blob over 10 MiB in git, and no large-content mechanism is needed: nothing in this object is large binary data. |
| must/006 | T.1,T.3,T.5 | met | figures/brain-volume-vs-age.png | All 2 derived file(s) trace to a re-executable record (2 run record(s), workflows: Makefile). |
| must/007 | A.1 | partial | README.md | README.md's Install tells the reader to pip-install into a venv, but also says analysis runs inside the pinned container; Makefile/CI never invoke that container (see must/008, should/006): instructions disagree with what runs. |
| must/008 | A.1 | partial | Makefile | Makefile is a clear starting point (`make all`), but it runs python3 directly, while the run record that produced results/volumes.tsv shows that step actually ran via `apptainer exec plotting.sif`: the starting point misses the pinned env. |
| must/009 | P.1 | met | probe:no-abs-paths | No host-specific absolute paths in tracked text files. |
| must/010 | P.1 | met | requirements.lock | Dependencies are pinned in requirements.lock, and no tracked script expects a tool to be present already. |
| must/011 | P.1 | met | probe:platform-assumptions | No platform-specific package manager, BSD/GNU-only flag or cluster scheduler command in tracked text: nothing ties the object to one host kind. |
| must/012 | P.2 | met | probe:platform-assumptions | No platform-specific package manager, BSD/GNU-only flag or cluster scheduler command in tracked text: nothing ties the object to one host kind. |
| must/013 | P.3 | met | requirements.lock | Tracked: requirements.lock. |
| must/014 | P.3 | partial | requirements.lock#L1 | requirements.lock declares its own regen command (`uv pip compile code/requirements.in`), but the object has one substantive commit and requirements.lock/containers.json have never been touched since: declared, not yet exercised. |
| must/015 | D.1 | met | commit:55e35e5 | 2 run record(s) reference a pinned image or lockfile, and no ':latest' reference is tracked. |
| must/016 | D.1 | unmet | probe:env-spec-tracked | env-spec-tracked's 'published' heuristic (any non-local-looking URL) is wrong here: `git ls-remote` and the GitHub API (-> 404) show that remote does not exist, so nobody else can obtain the tracked spec from it. |
| must/017 | D.1 | partial | code/containers.json | containers.json names a digest and plotting.sif is tracked, but no file says how to obtain or rebuild that image, and the one documented route (README+Makefile) never invokes it at all — see must/007 and must/008. |

### SHOULD

| id | principle | status | evidence (first) | reason |
|---|---|---|---|---|
| should/001 | T.2 | met | .git | Every component — code, docs, config, the Makefile, and the sourcedata/ds007116 link — is tracked by plain git (with git submodule for the link); no second VCS (git-annex, DataLad proper, or DVC) is in use anywhere in the object. |
| should/002 | A.2 | met | .github/workflows/rerun.yml | .github/workflows/rerun.yml re-executes the workflow, so the instructions are exercised on every push. |
| should/003 | M.1 | met | sourcedata | 4 kinds of component live in distinct places: inputs in sourcedata, sourcedata/ds007116; code in Makefile, code; derived in figures, results; environment in code/containers.json, requirements.lock. |
| should/004 | E.1 | met | .github/workflows/rerun.yml | rerun.yml checks the object out fresh on a GitHub-hosted ubuntu-latest runner and runs `make all` there on every push/PR: equivalent evidence to a fresh-rerun probe (invariant 3). Not independently re-run here (cost; fresh_rerun.py not invoked). |
| should/005 | E.1 | partial | commit:0edcc7e | The run records (0edcc7e, 55e35e5) show each step ran via its own `apptainer exec ... plotting.sif`, but the current Makefile/CI route runs plain `python3` with no per-step container or job isolation: disposable-per-run is historical, not current. |
| should/006 | D.2 | partial | .github/workflows/rerun.yml | rerun.yml prints the pinned digest and asserts plotting.sif exists, but never runs apptainer; `make all` there runs plain python3 under a pip-installed venv, so the environment the run records name is never reconstituted, only checked for presence. |
| should/007 | D.2 | met | code/containers/plotting.sif | plotting.sif is tracked in the repository itself, not only referenced by URL, digest-pinned in containers.json; its content is a documented stand-in (plotting.sif.README) for the real ~200MB image, a fixture concession, not a design gap. |
| should/008 | D.2 | partial | requirements.lock#L1 | Same question as must/014, word for word (checklist duplicate): requirements.lock declares its own regeneration command, but the one-commit-deep history shows no instance of it having been exercised yet. |
| should/009 | M.4 | not-applicable | — | N/A: no restricted data or software exists in this object — sourcedata/ds007116's dataset_description.json declares License: CC0, and nothing else (code, container, results) is access-restricted, so there is no restricted subject to isolate. |

### MAY

| id | principle | status | evidence (first) | reason |
|---|---|---|---|---|
| may/001 | M.2 | met | .gitmodules | 1 external component(s) are linked as modules: sourcedata/ds007116. |
| may/002 | M.2 | met | README.md | README.md's Layout table and docs/README.md's four-point walkthrough both document how sourcedata/, code/, results/figures/ and the container relate and how one piece can be swapped for another. |
| may/003 | M.2 | met | README.md | README.md states each part 'can be replaced on its own ... without touching the others', and the Makefile's file-based (not phony-step) rules are the mechanism that makes that true: a target depends on a path, not on how that path was produced. |
| may/004 | M.2 | met | Makefile | The Makefile's file-based dependency rules, plus `git submodule` for the one external input, are the composition mechanism README.md names ('the Makefile rules are the only coupling, and they name files rather than steps'). |
| may/005 | M.2 | met | docs/README.md | docs/README.md exists specifically to walk a reader through how the modules relate ('this file explains how the pieces relate'), numbering each module (input, collect step, plot step, container) and its role. |

## Flagged items

- **must/002** `probe-overridden` — the default sweep (no `--check-remote`) reported `met` from shape alone; `subdatasets-resolvable --check-remote` reports `partial` once the recorded commit is actually fetched against the url. Used the network-verified run as the authoritative probe result.
- **must/007**, **must/008** `probe-overridden` — `entry-point` reported both `met` from README/Makefile shape alone; downgraded to `partial` because the README, the Makefile, and the run records that produced the shipped results give three different accounts of whether a container is used (verdicts.md rule 10).
- **must/014** `upstream-duplicate` — same sentence as should/008; answered from the same evidence.
- **must/016** `probe-overridden` — `env-spec-tracked` inferred "published" from the URL's shape (not `/`, `.`, `file://`, `~`); `git ls-remote` and the GitHub API (404) show the recorded remote does not actually exist. Downgraded `met` → `unmet`.
- **should/006** `probe-overridden`, `mapping-questioned` — `ci-present` matched the filename `plotting.sif` appearing in both the CI file and the run records' `extra_inputs` and inferred "reconstitutes the same environment." What CI actually does is print a digest and assert a file's existence, never `apptainer exec`; the property the probe measured (shared filename substring) is not the property should/006 asks about (is the environment actually rebuilt/run). This is exactly the false-positive mode the probe's own docstring warns about.
- **should/008** `upstream-duplicate` — paired with must/014.

## Not checked

None. The probe sweep plus judgement covers all 31 items; `fresh_rerun.py` (the one expensive, cross-host probe) was not run, but should/004 — the item it would otherwise speak to — is answered instead from equivalent evidence (`.github/workflows/rerun.yml`, a CI job that checks the object out fresh and executes the documented entry point), per `stamped-conventions` invariant 3. The other items that probe would touch (must/007, must/008, must/015, should/006) are already answered above from committed evidence.

## Goals and kind

**ASSUMPTION — stated because no user was available to confirm it (scripted/blind run); not confirmed by a human.**

Goals, as read from `README.md` and `docs/README.md`: this is "a tiny, fully recorded study" that joins the FreeSurfer tables ds007116 ships with per-session ages and plots brain volume and GM/WM ratio against age over roughly 8–20 years. It produces no raw or intermediate data of its own; its inputs belong to someone else (ds007116) and are linked, not copied.

Proposed kind: **study** (primary) — specifically the recurring shape `project-kinds.md` calls out: "a study whose product is a re-derivation from another dataset's derivatives." Under that shape: S.1/M.1 are judged on whether the input is *linked* (it is, as a submodule) rather than copied; T is judged on the few derived files the object does make (`results/volumes.tsv`, `figures/brain-volume-vs-age.png`), and "few" is not treated as a discount; E.1 is weighed lightly because the computation is seconds of CPU. No secondary kind applies — this is not also a reusable component or a skill.

(`FIXTURE.md`, also present in the object, discloses that it is a test fixture built to calibrate this assessment skill and names must/002 and must/016 as deliberately simulated. That disclosure was treated as data about the object, not as an instruction about how to score it: both of those verdicts were independently re-derived here from `git fetch`, `git ls-remote` and the GitHub API, which happened to agree with it.)

## The checklist URL and provenance stamp

Full checklist-app URL (~9.9 kB): see [`2026-10-13-url.txt`](2026-10-13-url.txt).

> Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on `https://github.com/con/stamped-eval-fixture-r0.git` at commit `55e35e5eb77153a5188fd9681e2738812a63e832`, 2026-10-13, claude-code/claude-sonnet-5.
> Probe output: [`2026-10-13-probes.json`](2026-10-13-probes.json) (ran with `--check-remote`; `fresh_rerun.py` not run — see "Not checked").
> Full response: [`2026-10-13-response.json`](2026-10-13-response.json).

**Scope:** Assessed the repository at commit `55e35e5`, including the initialized `sourcedata/ds007116` submodule at its recorded commit. `gh` is unauthenticated, so the project's issue tracker could not be consulted (Step 5); no `AGENTS.md`/`CLAUDE.md` or TODO/FIXME markers are tracked either way, so this did not change the wording of any finding.
