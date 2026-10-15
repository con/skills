# STAMPED assessment: dandi-t261-compression-study (blind run)

**Verdict line.** MUST: 4 met / 8 partial / 5 unmet / 0 not-checked (of 17). SHOULD: 1 met / 2 partial / 4 unmet / 2 not-checked (of 9). MAY: 5 met / 0 partial / 0 unmet / 0 not-checked (of 5). Judgement items: 19 of 31 (plus two probe verdicts overridden or mapping-questioned, see flagged items).

**Assumptions (no user available, not confirmed).** Kind: study (primary), with the tool module `code/compression-comparisons-tools` judged as a component. Goals: taken from `dataset_description.json` Purpose (reproduce Buccino et al. 2023 lossless results; compare ITU-T T.261 against the codec set). Date: 2026-10-15 from the UTC system clock, not 2026-10-14 as the session header says.

## What to fix first

1. **Repair the tool module url** (`.gitmodules`, `url = ../..`). A fresh clone of origin fails `submodule update`. Set a real published url. Closes must/002 and helps must/016, may/001 and must/003.
2. **Remove host paths** from `code/run_sorting_sweep.sh` (WavPack at `/data/yoh`, `/tmp/sorting-gen`), `code/run_sweep.sh` (fallback at line 84) and `code/partial_report.sh` (reference CSV). Closes must/009, must/001, must/011.
3. **Track an environment spec** (lock or pinned requirements for `envs/compbench`, plus the pinned datalad) and have run records name it. Closes must/010, must/013, must/015, must/006, and, once it exists, the update-process item must/014 and should/008.
4. **Add a CI job** that runs the README reproduction route on a fresh runner, or at least one unit. Closes should/002 and should/006, and gives should/004 evidence.
5. **Commit the referenced reference data or stop referencing it** (`.specify-ref/`, `.specify/specs/` are named but absent), and add a LICENSE file to match `dataset_description.json`.

## What the project already does well

- Committed state is whole: `git status` is empty, 4422 text files tracked (`must/004`).
- Large binaries are in git-annex, 13407 pointers, no binary blob over 10 MiB in git (`must/005`).
- A clear starting point: `README.md` reproduction section and `code/run_sweep.sh` (`must/007`, `must/008`).
- Pinned tool commit with a refuse-on-drift guard in `code/run_sweep.sh`; pin 915cb4c is fetchable upstream (`may/003`).
- Per-cell `[DATALAD RUNCMD]` records with inputs, outputs and dsid on 1216 runs.

## Per-item table

| id | principles | status | source | reason (first words) |
|---|---|---|---|---|
| must/001 | S.1 | partial | judgement | Essential inputs outside root: reference CSV from /data/yoh fallback |
| must/002 | S.1 | unmet | probe+judgement | Url ../.. : fresh clone fails, "dandi/.. not found" |
| must/003 | S.1 | partial | judgement | WavPack vendored for sweep; sorting hardcodes host path |
| must/004 | T.1,T.3,T.5 | met | probe:tree-clean | Committed state is the whole state, 4422 files |
| must/005 | T.1,T.3,T.5 | met | probe:large-in-annex | git-annex carries binaries, 13407 pointers |
| must/006 | T.1,T.3,T.5 | unmet | probe+probe+judgement | No record names an environment; duct counted as capture |
| must/007 | A.1 | met | probe:entry-point | README install/usage/reproduce section |
| must/008 | A.1 | met | probe:entry-point | Starting point: code/run_sorting_sweep.sh, run_sweep.sh |
| must/009 | P.1 | unmet | probe:no-abs-paths | Host paths under /data/yoh in four scripts |
| must/010 | P.1 | unmet | probe:env-spec-tracked | Host tools (patched datalad, cmake) not in any spec |
| must/011 | P.1 | partial | judgement | Some host assumptions named; /data/yoh, OS, toolchain not |
| must/012 | P.2 | partial | judgement | No requirements list; cmake, GPU, datalad inline only |
| must/013 | P.3 | partial | probe+judgement | No env spec here; tool pyproject in uninitialised module |
| must/014 | P.3 | partial | judgement | Declared in README, 17 re-pins; no spec here to update |
| must/015 | D.1 | unmet | probe:run-env-linked | Records pin nothing: no digest or frozen manifest |
| must/016 | D.1 | partial | judgement | Tool repo public and pin fetchable; object url broken |
| must/017 | D.1 | partial | judgement | Build steps given; clone step is placeholder <this-repo-url> |
| should/001 | T.2 | met | judgement | One stack: git plus git-annex, .datalad/config |
| should/002 | A.2 | unmet | probe:ci-present | No CI config; nothing re-runs the route |
| should/003 | M.1 | partial | probe+judgement | Inputs, code, derived apart; env definition not separate here |
| should/004 | E.1 | not-checked | judgement | No CI, no fresh-environment record; rerun not attempted |
| should/005 | E.1 | unmet | judgement | One long-lived venv serves all 912 cells |
| should/006 | D.2 | unmet | probe:ci-present | No CI; environment never rebuilt or tested |
| should/007 | D.2 | unmet | judgement | No image or binary archived; rebuilt from prose |
| should/008 | D.2 | partial | judgement | Same as must/014 (upstream-duplicate) |
| should/009 | M.4 | not-checked | judgement | Upstream BWC terms (src/bwc, uninitialised) not read |
| may/001 | M.2 | met | probe:subdatasets-resolvable | Two external components linked as modules |
| may/002 | M.2 | met | judgement | Layout documented in dataset_description and README |
| may/003 | M.2 | met | judgement | Pin guard; sourcedata never modified; re-pins show independence |
| may/004 | M.2 | met | judgement | git submodules and datalad subdatasets in .gitmodules |
| may/005 | M.2 | met | judgement | README Layout section and dataset_description Layout |

Extra items (no checklist id): clone-weight partial (22 text blobs over 10 MiB, 239 MiB in git); inputs-untouched not-checked (modules uninitialised); license-declared partial (MIT in dataset_description.json, no LICENSE file tracked).

## Flagged items

- **must/006**: `mapping-questioned`, `probe-overridden`. The probe counted `duct` profiles as environment capture (1095 of 1216 records). Duct measures resources and does not capture an environment. The verdict is unmet.
- **should/003**: `probe-overridden`, `mapping-questioned`. The probe found no environment component at all and still returned met. Overridden to partial.
- **must/014 and should/008**: `upstream-duplicate`. Same sentence in the checklist; same evidence, same verdict.
- **should/001** and **should/009**: `unverified-claim`. Submodule internals were not read.
- **must/002**: probe verdict confirmed by a fresh clone of origin and a failing `git submodule update --init` (no override).
- **must/006 probe overlap**: `derived-have-records` answers a T-property (record coverage of derived files, 1218 uncovered) that the must/006 text does not ask about.

## Not checked

- Module contents: `code/compression-comparisons-tools` and `sourcedata/aind-ephys-compression` are uninitialised. Settling them needs `git submodule update --init` in a throwaway clone.
- should/004: needs a fresh-container rerun (`fresh_rerun.py`), not run because the user did not consent and it is expensive.
- should/009: needs the upstream terms of the BWC reference code.
- Issue tracker (Step 5): `gh` unauthenticated; not consulted. The object's own README discloses two gaps (no sweep-level run record; 20 cells lost), not checked against the history.

## Goals and kind

Goals from `dataset_description.json` Purpose and README "Status" (assumption, not confirmed by a user). Kind: study (primary), tool module as a component. Emphasis: T, S and A items weigh most.

## URL, stamp, files

Checklist URL: `2026-10-15-url.txt` (one line, validated against the 0.3.1 pin, 31 answers).
Response: `2026-10-15-response.json`. Probes: `2026-10-15-probes.json`. No fresh-rerun file (probe not run).

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on https://github.com/dandi/compression-comparisons-t261-study at commit `f2f0802`, 2026-10-15, claude-code/claude-haiku-5-5.
