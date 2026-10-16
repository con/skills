# STAMPED assessment — 2026-10-16

**Verdicts:** MUST: 5 met / 1 partial / 11 unmet / 0 not-checked; SHOULD: 0 met / 2 partial / 5 unmet / 2 not-checked; MAY: 0 met / 0 partial / 5 unmet / 0 not-checked. A partial does not satisfy a MUST.

**Scientific adequacy (separate from STAMPED):** The supplied task is to calculate the arithmetic mean of x. The input values are 1, 2, and 3, so the mean is 2.0. products/estimate.json reports 2.0, and analysis.py computes sum(x) / len(x). The delivered result is correct for this task. I checked the values and implementation directly; I did not replay the pipeline.

## What to fix first

1. Track the delivered analysis code and result in the original version-control workflow. The receipt shows that both were outside Git at delivery, so the answer is not preserved with the tracked input: **must/004, should/001**.
2. Add a small, reproducible environment specification and instructions for obtaining it, running the script, and updating the specification. The current script needs an available Python runtime but does not identify one: **must/003, must/007, must/010–017, should/008**.
3. Record each run’s command, input and code identity, exact environment, and result. This would connect the correct estimate to the computation that produced it: **must/006, should/006**.
4. Keep a test or repeated-run record and test the documented route in a fresh environment. These records would show that instructions and environment remain usable: **should/002, should/004**.
5. Describe the component boundaries and any composition mechanism if the input, code, output, or runtime are intended to be independently maintained: **should/003, may/002–005**.

## What the project already does well

- The supplied input and result are small text files; no large-binary storage mechanism is needed (input.csv, products/estimate.json).
- The script has one clear entry point and uses relative input and output paths (analysis.py).
- The data input, script, and result are all inside the delivered root (input.csv, analysis.py, products/estimate.json).

## Per-item results

| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f`, `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -type l` | All delivered files are under the object root; the inventory contains no external paths or symlinks. |
| must/002 | S.1 | met | probe:subdatasets-resolvable+judgement | `input.csv`, `analysis.py` | The only dataset input, input.csv, is inside the root and analysis.py reads it by relative path. |
| must/003 | S.1 | unmet | judgement | `analysis.py`, `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | Python is needed to run analysis.py, but no environment or linked module provides that runtime. |
| must/004 | T.1,T.3,T.5 | partial ⚠ (a MUST is not satisfied by partial) | probe:tree-clean+judgement | `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/stop-state.json`, `analysis.py` | Git tracked input.csv, while original delivery left analysis.py untracked and estimate.json ignored. |
| must/005 | T.1,T.3,T.5 | met | probe:large-in-annex | `input.csv`, `products/estimate.json` | The delivered CSV and JSON are small text files; no large binary content needs a separate store. |
| must/006 | T.1,T.3,T.5 | unmet | probe:derived-have-records+judgement | `products/estimate.json`, `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/stop-state.json` | The delivered estimate has no run record linking its actions and exact environment; the probe misidentified input.csv as derived. |
| must/007 | A.1 | unmet | probe:entry-point+judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f`, `analysis.py` | No README, Makefile, or other installation and usage instructions explain how to obtain and run the environment. |
| must/008 | A.1 | met | probe:entry-point+judgement | `analysis.py` | analysis.py is a single runnable script that reads input.csv and writes products/estimate.json. |
| must/009 | P.1 | met | probe:no-abs-paths+judgement | `analysis.py`, `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/stop-state.json` | The delivered script reads and writes with relative paths; the probe scanned tracked files only, while analysis.py was untracked at delivery. |
| must/010 | P.1 | unmet | probe:env-spec-tracked+judgement | `analysis.py`, `git ls-files` | The workflow requires a Python runtime, but no environment specification declares Python or any dependencies. |
| must/011 | P.1 | unmet | probe:platform-assumptions+judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | The script assumes Python and an object-root working directory; no documentation records these host requirements. |
| must/012 | P.2 | unmet | probe:platform-assumptions+judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No README or environment specification lists system requirements or dependencies. |
| must/013 | P.3 | unmet | probe:env-spec-tracked | `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/stop-state.json` | No environment specification is present in the original version-controlled delivery. |
| must/014 | P.3 | unmet | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No dependency-update process or environment specification is declared. |
| must/015 | D.1 | unmet | probe:run-env-linked+judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No exact environment specification or frozen package manifest is delivered. |
| must/016 | D.1 | unmet | probe:env-spec-tracked+judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No environment specification is published or otherwise made available for retrieval. |
| must/017 | D.1 | unmet | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | There are no instructions for obtaining or using an environment specification. |
| should/001 | T.2 | partial | judgement | `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/stop-state.json` | Git versions input.csv, but original delivery leaves the analysis script untracked and the result ignored. |
| should/002 | A.2 | unmet | probe:ci-present+judgement | `probe:ci-present`, `git log` | No test definitions, repeated test records, or CI configuration are present in the delivered object or its history. |
| should/003 | M.1 | partial | probe:modules-separated+judgement | `input.csv`, `analysis.py`, `products/estimate.json` | input and result occupy separate paths, but code is at the root and there is no environment module. |
| should/004 | E.1 | not-checked | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No fresh-environment run evidence exists; replay was outside this assessment. A clean replay with a suitable comparison would settle it. |
| should/005 | E.1 | unmet | judgement | `analysis.py` | analysis.py runs in the caller's Python process and does not create a disposable environment. |
| should/006 | D.2 | unmet | probe:ci-present+judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No environment specification or reconstitution test record exists in the delivered object. |
| should/007 | D.2 | unmet | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No environment artifacts or specification are archived with the object. |
| should/008 | D.2 | unmet | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No dependency-update process or environment specification is declared. |
| should/009 | M.4 | not-checked | judgement | `input.csv` | Access terms are absent, so I cannot determine whether input.csv is restricted; confirm its owner and access terms. |
| may/001 | M.2 | unmet | probe:subdatasets-resolvable+judgement | `analysis.py`, `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | Python is an external software dependency, but no linked module provides it. |
| may/002 | M.2 | unmet | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No documentation describes modules or how components relate and can be recombined. |
| may/003 | M.2 | unmet | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No modular boundaries or independent-update mechanism are defined. |
| may/004 | M.2 | unmet | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No mechanism composes modules; the object has no linked or otherwise composed modules. |
| may/005 | M.2 | unmet | judgement | `find /Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-c/object -maxdepth 3 -type f` | No documentation or tooling explains a modular structure or navigation. |

## Flagged items

- **must/002, must/015, should/002, should/006, may/001 — probe-overridden:** the probes left these unchecked after finding no linked modules, CI, or environment pin. Reading the delivered files established that input.csv is included locally and that Python is needed but not supplied as a linked module. The missing run and environment evidence leaves the remaining properties unmet.
- **must/004 — probe-overridden:** tree-clean saw the coordinator-preserved commit. The original stop receipt records analysis.py as untracked and products/estimate.json as ignored.
- **must/006 — probe-overridden:** derived-have-records called input.csv derived; the delivered result is products/estimate.json, and the original receipt records it as ignored with no run record.
- **must/008 — probe-overridden:** entry-point looked at tracked paths and missed the delivered but untracked analysis.py, which is the clear script starting point.
- **must/009 — mapping-questioned:** the probe scanned tracked paths, while the checklist asks about scripts. Direct inspection of the untracked script confirmed relative paths.
- **must/011, must/012 — probe-overridden:** the command scan cannot settle documented host assumptions or requirements. The object has no documentation or environment specification, and the script assumes Python and the object-root working directory.
- **should/003 — probe-overridden:** the probe considers recognized tracked layouts; direct inspection found input and output paths separated but code at the root and no environment module, so partial.
- **must/014 and should/008 — upstream-duplicate:** the checklist repeats the same environment-update question; both answers use the same evidence.

Extra probe findings outside the checklist: no reuse license is declared (license-declared: unmet); no oversized text blob exists (clone-weight: met); inputs-untouched is not applicable because there are no linked modules to compare.

## Not checked

- **should/004:** no fresh-environment replay or equivalent completed-run evidence was available. A clean replay with a suitable scientific comparison would settle it; replay was not requested.
- **should/009:** the object supplies no access terms, so I cannot tell whether input.csv is restricted. The data owner or access terms would settle it.

## Goals and kind

**Assumption, not confirmed:** the goal is to answer the supplied scientific task by calculating the arithmetic mean of x in input.csv. I propose **study**, because the product is a computed answer from data and code. The task is standalone, so the goal and kind could not be confirmed with a user. This kind emphasizes the included input, run provenance, and the environment that produced the result.

## Checklist URL and assessment stamp

[Open the STAMPED checklist](2026-10-16-url.txt). The canonical item responses are in [2026-10-16-response.json](2026-10-16-response.json); the unedited probe output is in [2026-10-16-probes.json](2026-10-16-probes.json).

Produced by assess-alignment-with-stamped-principles 0.1.0 with stamped-conventions 0.1.0, checklist 0.3.1 (stamped-checklist-schema@v0.3.1, af259ba), on the local case object at coordinator-preservation commit fa2a403a5940d9c7425278720d404856ab680874, 2026-10-16, Codex Desktop subagent / model metadata unavailable through an approved resolver. No fresh-rerun report was produced.

**Scope and capture boundary:** the supplied original stop receipt records seed commit 296e306732358822e82b548b8d73e55255ef536a, with .gitignore and input.csv tracked; analysis.py untracked; and products/estimate.json ignored. SHA-256 values checked against the receipt: input.csv 4bf0e63035dd1fafdbe5915d64110833dacd4754cfbb5e70330440fd3bb5f53b; analysis.py e0b9f58f2216ff75136cf681d961fe171c48361c1335ffce03f137c73488cacf; products/estimate.json e6ed0002cabe15a3394c892c60df5e6ff91dac274066f0fd145ecf2eb7ea95c5. Coordinator preservation added the code and result to the current commit; that does not earn worker-practice credit. The object has no remote, TODO, or AGENTS.md, so no project issue tracker could be checked. I inspected the full file inventory, Git history and status, the delivered script, input and estimate; ran the supplied probes with remote checking; checked the original receipt and hash agreement; and validated all 31 responses. I did not inspect other case materials or replay the pipeline.

Probe output: [2026-10-16-probes.json](2026-10-16-probes.json). Response: [2026-10-16-response.json](2026-10-16-response.json).
