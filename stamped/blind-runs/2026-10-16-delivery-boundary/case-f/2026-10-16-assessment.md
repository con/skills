# STAMPED assessment: finite-observation summary

**Scientific adequacy.** The delivered result is correct for the stated task. `input.csv` has finite values 2, 4, and 6 plus `nan`; the finite count is 3 and their arithmetic mean is 4.0. `products/estimate.json` reports those values, consistent with the described calculation in `analysis.py`. I did not execute or replay the workflow, so this checks the arithmetic and output, not how the delivered result was produced.

**STAMPED verdicts.** MUST: 7 met / 2 partial / 7 unmet / 0 not-checked (1 not-applicable; 17 items). SHOULD: 0 met / 2 partial / 5 unmet / 1 not-checked (1 not-applicable; 9 items). MAY: 1 met / 2 partial / 2 unmet / 0 not-checked (5 items). A partial does not satisfy a MUST.

## What to fix first

1. Track or otherwise version the delivered analysis code, README, component copy, and environment declaration; preserve the ignored result with its source state. They are present in the delivery but untracked or ignored, so Git history does not identify the assessed work (must/004, must/013; should/001).
2. Record a complete, reproducible environment, including a Python version and a pinned NumPy resolution, then document how to obtain and use it. The current `numpy>=2` declaration is mutable and untracked (must/010, must/015, must/017; should/006–008).
3. Add a run record that identifies the actions, result, code/input state, and exact environment. The output exists but no record links it to an execution (must/006).
4. Restore the upstream location, revision, and retrieval method for `component.py`, or document its provenance and treat the copy as an intentionally bundled component. The README says those details were not retained (may/001).
5. Add a repeatable check of the documented route and its environment. The captured object has no recurring test or completed fresh-environment run (should/002, should/004, should/006).

## What the project already does well

- The input, code, dependency declaration, documentation, and result all sit under one object root, and the input is read by a relative path (`README.md`, `analysis.py`, `input.csv`, stop receipt).
- The README supplies a clear command and the analysis script exposes a simple entry point that composes `component.py` (`README.md`, `analysis.py`).
- The dependency on NumPy is disclosed, and the implementation filters non-finite observations before calculating the mean (`requirements.txt`, `component.py`).

## Per-item results

| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-f/stop-state.json` | The captured delivery places the CSV, scripts, requirements, README, and ignored result under one object root. |
| must/002 | S.1 | met | judgement | `README.md`, `input.csv` | The input dataset is included inside the root and the documented command reads input.csv there. |
| must/003 | S.1 | met | judgement | `requirements.txt`, `component.py` | NumPy is named in requirements.txt and the independently sourced component is included as component.py under the root. |
| must/004 | T.1,T.3,T.5 | partial ⚠ (a MUST is not satisfied by partial) | probe:tree-clean+judgement | `git status --short`, `git ls-files -s` | Git tracks input.csv and .gitignore, while the README, scripts, and requirements are untracked in the delivered state. |
| must/005 | T.1,T.3,T.5 | not-applicable | judgement | `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-f/stop-state.json` | N/A: the complete delivered object contains no large binary data. |
| must/006 | T.1,T.3,T.5 | unmet | probe:derived-have-records+judgement | `products/estimate.json`, `analysis.py`, `probe:derived-have-records` | The delivered estimate has no run record linking its production actions to an environment; input.csv is an input, not a derived file. |
| must/007 | A.1 | unmet | probe:entry-point+judgement | `README.md`, `requirements.txt` | README.md gives a run command but no instructions for obtaining or installing Python and NumPy. |
| must/008 | A.1 | met | probe:entry-point+judgement | `README.md`, `analysis.py` | README.md gives the starting command, and analysis.py is the runnable entry point. |
| must/009 | P.1 | met | probe:no-abs-paths+judgement | `analysis.py`, `component.py` | The delivered scripts use relative local imports and input/output paths; no host-specific absolute path appears. |
| must/010 | P.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `requirements.txt`, `README.md` | The third-party NumPy dependency is listed, but the Python runtime version required by the documented route is unspecified. |
| must/011 | P.1 | met | judgement | `README.md`, `analysis.py` | The documented route requires Python and NumPy; no additional host configuration, mounts, hardware, or services are stated or used. |
| must/012 | P.2 | met | judgement | `README.md`, `requirements.txt` | README.md names Python and NumPy; requirements.txt names the third-party package dependency. |
| must/013 | P.3 | unmet | probe:env-spec-tracked+judgement | `git status --short`, `requirements.txt` | requirements.txt exists in the delivered bytes but is untracked, so the environment specification is not in version control. |
| must/014 | P.3 | unmet | judgement | `requirements.txt`, `git log --oneline` | No runnable process for updating environment specifications is documented, and the only requirements file is untracked. |
| must/015 | D.1 | unmet | probe:run-env-linked+judgement | `requirements.txt`, `probe:run-env-linked` | requirements.txt uses numpy>=2 and gives no lock or exact environment snapshot for others to reproduce. |
| must/016 | D.1 | unmet | probe:env-spec-tracked+judgement | `git remote -v`, `requirements.txt` | No remote or published environment specification is recorded; requirements.txt is untracked and unpinned. |
| must/017 | D.1 | unmet | judgement | `README.md`, `requirements.txt` | The README gives a command but no instructions for obtaining or installing the environment specification. |
| should/001 | T.2 | partial | judgement | `git ls-files -s`, `git status --short --ignored` | Git contains the input and ignore rules, but the code, documentation, configuration, and result are untracked or ignored. |
| should/002 | A.2 | unmet | probe:ci-present+judgement | `probe:ci-present`, `git log --oneline` | The delivery contains no recurring workflow test or run record showing that the instructions are checked over time. |
| should/003 | M.1 | partial | probe:modules-separated+judgement | `README.md`, `git status --short --ignored` | products/ separates the result, but input, code, and requirements share the root; the result directory is ignored. |
| should/004 | E.1 | not-checked | judgement | `probe:run-env-linked` | No fresh-environment run was authorized or attempted, and no completed-run record is included; a fresh isolated run would settle this. |
| should/005 | E.1 | unmet | judgement | `README.md`, `requirements.txt` | The documented command uses the caller’s existing Python and NumPy installation; no disposable environment is created. |
| should/006 | D.2 | unmet | probe:ci-present+judgement | `requirements.txt`, `probe:ci-present` | No exact environment pin or recurring reconstitution test is present in the delivered object. |
| should/007 | D.2 | unmet | judgement | `requirements.txt`, `delivery inventory` | No environment image, executable, or binary artifact is archived; only an untracked requirements list is supplied. |
| should/008 | D.2 | unmet | judgement | `requirements.txt`, `git log --oneline` | No environment update process is documented, and no update appears in version control history. |
| should/009 | M.4 | not-applicable | judgement | `README.md`, `delivery inventory` | N/A: no restricted data or software is identified in the complete delivered object. |
| may/001 | M.2 | unmet | probe:subdatasets-resolvable+judgement | `README.md`, `component.py` | component.py is independently maintained but its upstream location, revision, and retrieval instructions were not retained. |
| may/002 | M.2 | unmet | judgement | `README.md` | The README names the copied component but does not document module boundaries or how modules can be recombined. |
| may/003 | M.2 | partial | judgement | `analysis.py`, `component.py` | The script/component boundary exists, but no interface contract or test supports independent component updates. |
| may/004 | M.2 | met | judgement | `analysis.py` | analysis.py composes the local component through a Python import and invokes summarize. |
| may/005 | M.2 | partial | judgement | `README.md` | README.md identifies the component and run command, but gives no route to retrieve the component’s upstream source. |

## Flagged items

- **must/004** — the tree-clean probe found untracked delivered files; I judged `partial` because Git tracks the input and ignore rules, but not code, documentation, or configuration.
- **must/006** — the derived-file probe treated `input.csv` as a derived result. I inspected the source and receipt: it is an input; the actual result is the ignored `products/estimate.json`, which has no run record.
- **must/007** — the entry-point probe overlooked the untracked README. The README exists and gives a run command, but it does not explain how to install Python or NumPy, so the verdict remains unmet.
- **must/008** — the same tracked-path limit hid the delivered README and script. Their command and entry point satisfy this item.
- **must/009** — the path probe searched only tracked files. I also read both delivered scripts; their paths are relative and the verdict remains met.
- **must/013** — the environment-spec probe searched tracked files; `requirements.txt` is delivered but untracked, so it still fails the version-control requirement.
- **should/003** — the layout probe searched only tracked paths. The delivered `products/` folder separates the result, while input, code, and environment declaration remain together at the root.
- **should/008** — duplicate of must/014 by checklist text; both are unmet on the same evidence.
- **may/001** — the module probe did not recognize a local copy as an independently maintained component. The README identifies that copy and explicitly says its source location, revision, and retrieval directions were lost.

## Not checked

- **should/004:** I did not run a fresh isolated environment because replay was not requested. A fresh run from the documented route with a scientifically suitable output comparison would settle it.

## Goals and kind

**Assumption, not confirmed with a user:** the goal is to report the number and arithmetic mean of finite observations in `input.csv`, as stated in the README and the assessment prompt. I classify this as a **study**: it answers a question from data and computation. The emphasis is therefore on all seven principles, especially linking the delivered result to its inputs, actions, and environment. Scientific adequacy is reported separately above.

The receipt identifies supplied seed commit `5f3aefd0ea525d8526ee47e06c6ffd0a4d2ce6e7`, with only `.gitignore` and `input.csv` tracked. In the original delivery, `README.md`, `analysis.py`, `component.py`, and `requirements.txt` were untracked; `products/` was ignored and contained `estimate.json`. No commits followed the seed. The receipt supplies hashes for all listed delivery files. No Git remote is configured. These are delivery-state facts, not inferences from the current branch alone.

The probes and direct inspection covered the supplied object and receipt. There was no remote for module or publication checks and no remote issue tracker to inspect. I did not inspect files outside this case, run the workflow, perform a replay, or independently verify the lost upstream source of `component.py`. Exact harness and model version metadata were unavailable to this subagent and are marked as unavailable in the machine-readable stamp.

## Checklist URL, stamp, and records

[Open the filled checklist](2026-10-16-url.txt). The canonical per-item responses and evidence are in [2026-10-16-response.json](2026-10-16-response.json); the unedited probe output is in [2026-10-16-probes.json](2026-10-16-probes.json).

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on the supplied object at commit `5f3aefd0ea525d8526ee47e06c6ffd0a4d2ce6e7`, 2026-10-16, Codex Desktop subagent / GPT-6 (exact harness and model versions unavailable). Probe output: `2026-10-16-probes.json`.
