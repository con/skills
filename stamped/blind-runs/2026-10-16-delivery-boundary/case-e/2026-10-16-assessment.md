# STAMPED assessment — finite-observation study

**Assumption (not confirmed):** The goal is to report the number and arithmetic mean of finite observations in `input.csv`, as stated in the assessment prompt. The object is a **study**: it delivers data, computation, and a numerical answer. No human was available to confirm this.

MUST: 4 met / 2 partial / 10 unmet / 0 not-checked / 1 not-applicable (17 total).  
SHOULD: 0 met / 2 partial / 3 unmet / 3 not-checked / 1 not-applicable (9 total).  
MAY: 0 met / 0 partial / 4 unmet / 0 not-checked / 1 not-applicable (5 total).

**Scientific adequacy, separate from STAMPED:** The result is correct for the stated task. The finite values in `input.csv` are 2, 4, and 6, so n = 3 and mean = 4.0, matching `products/estimate.json`. I checked the input and output directly; I did not execute `analysis.py`.

## What to fix first

1. Track `analysis.py`, `requirements.txt`, and the result with Git → the delivered revision currently omits the method and its output from tracked history → must/004, should/001, should/003.
2. Specify and pin Python and NumPy, then record the producing command and exact environment with the result → another reader cannot reconstruct which environment produced the correct number → must/003, must/006, must/010, must/013, must/014, must/015, must/016, must/017, should/006, should/008.
3. Add short install and run instructions naming the working directory and output → a reader can identify the script but cannot follow a documented reproduction route → must/007, must/011, must/012.
4. Add a repeatable test or run check in a clean environment → the checked result has no recorded fresh run or regular testing evidence → should/002, should/004.
5. State the simple input/code/output layout and provide a retrievable publication route → collaborators currently have no navigation or environment retrieval path → may/002–005.

## What the project already does well

- All delivered files, including the ignored estimate, are inside the same root; the script refers to the input and output with relative paths (`analysis.py`, `input.csv`, `products/estimate.json`).
- The delivered answer is numerically adequate for the stated descriptive task, as checked directly against the CSV values and JSON result.
- The calculation is short and visible in one script, and the result has an output directory created by the script (`analysis.py`).

## Per-item table

| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `input.csv`, `products/estimate.json` | All delivered files, including the ignored result, are inside the object root. |
| must/002 | S.1 | met | judgement | `input.csv`, `analysis.py` | input.csv is included at the root and analysis.py reads it by relative name. |
| must/003 | S.1 | unmet | judgement | `requirements.txt`, `probe:subdatasets-resolvable` | NumPy is named in requirements.txt but is neither supplied in an environment nor linked as a project module. |
| must/004 | T.1,T.3,T.5 | partial ⚠ (a MUST is not satisfied by partial) | probe:tree-clean+judgement | `git status --porcelain`, `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-e/stop-state.json#original_delivery` | Git tracks the input and .gitignore, but analysis.py and requirements.txt are untracked and the result is ignored. |
| must/005 | T.1,T.3,T.5 | not-applicable | judgement | `input.csv`, `products/estimate.json` | N/A: the complete delivery contains only small text/CSV/JSON files and no large binary data. |
| must/006 | T.1,T.3,T.5 | unmet | probe:derived-have-records+judgement | `products/estimate.json`, `analysis.py`, `probe:derived-have-records` | The delivered estimate has no run record linking its producing action and exact environment; the probe misidentified input.csv as derived. |
| must/007 | A.1 | unmet | probe:entry-point | `probe:entry-point`, `analysis.py` | No README or Makefile gives installation and usage instructions. |
| must/008 | A.1 | met | probe:entry-point+judgement | `analysis.py`, `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-e/out/2026-10-16-probes.json#entry-point` | analysis.py is the single main script and reads the included input; it is an identifiable starting point, though usage instructions are absent. |
| must/009 | P.1 | met | probe:no-abs-paths | `analysis.py` | The script uses relative input and output paths; no host-specific absolute path appears. |
| must/010 | P.1 | partial ⚠ (a MUST is not satisfied by partial) | probe:env-spec-tracked+judgement | `requirements.txt`, `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-e/out/2026-10-16-probes.json#env-spec-tracked` | requirements.txt declares NumPy, but the Python interpreter/version and exact dependency versions are not specified. |
| must/011 | P.1 | unmet | judgement | `analysis.py`, `requirements.txt` | The script assumes a Python runtime, NumPy, and execution from the directory containing input.csv; these host and launch assumptions are undocumented. |
| must/012 | P.2 | unmet | judgement | `requirements.txt`, `probe:entry-point` | No README or complete environment specification lists system requirements; requirements.txt names only NumPy. |
| must/013 | P.3 | unmet | probe:env-spec-tracked | `git status --porcelain`, `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-e/stop-state.json#original_delivery` | requirements.txt is present in the delivery but untracked; no environment specification is in Git. |
| must/014 | P.3 | unmet | judgement | `git log`, `requirements.txt` | No runnable process for updating environment specifications is declared; the sole commit does not show one. |
| must/015 | D.1 | unmet | probe:run-env-linked+judgement | `requirements.txt`, `probe:run-env-linked` | numpy>=2 is a floating lower bound and Python is unpinned, so the environment cannot be exactly reconstructed. |
| must/016 | D.1 | unmet | probe:env-spec-tracked+judgement | `git remote -v`, `requirements.txt`, `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-e/out/2026-10-16-probes.json#env-spec-tracked` | No remote or publication route makes an environment specification retrievable; requirements.txt is only local and untracked. |
| must/017 | D.1 | unmet | judgement | `probe:entry-point`, `requirements.txt` | The delivery has no instructions for obtaining or using a reproducible environment. |
| should/001 | T.2 | partial | probe:tree-clean+judgement | `git status --porcelain`, `/Users/johnlee/.local/state/stamped-in-practice/assessment-neutrality-trial-01/case-e/stop-state.json#original_delivery` | The input is tracked in Git, but code and environment files in the same delivery are untracked; component tracking is incomplete. |
| should/002 | A.2 | not-checked | probe:ci-present+judgement | `probe:ci-present`, `git log` | No repeated-test record or CI is present in this delivery; an external run archive or test history would settle regular testing. |
| should/003 | M.1 | partial | probe:modules-separated+judgement | `object inventory`, `requirements.txt` | products/ is separate, but input, code, and environment are not organized as independently maintained modules. |
| should/004 | E.1 | not-checked | probe:run-env-linked+judgement | `probe:run-env-linked`, `products/estimate.json` | No fresh-environment run is recorded; an authorized clean-environment execution with its result would settle this. |
| should/005 | E.1 | unmet | judgement | `analysis.py`, `requirements.txt` | analysis.py runs directly in the caller's existing Python environment and defines no disposable-environment creation. |
| should/006 | D.2 | not-checked | probe:run-env-linked+judgement | `probe:run-env-linked`, `requirements.txt` | No environment pin or reconstitution run is recorded; a repeated clean rebuild using the result-producing specification would settle this. |
| should/007 | D.2 | unmet | judgement | `object inventory`, `requirements.txt` | The delivery has a requirements file but no archived environment artifact such as a wheel bundle or image. |
| should/008 | D.2 | unmet | judgement | `requirements.txt`, `git log` | No runnable dependency-update process is declared, and history contains no tracked updates to such a process. |
| should/009 | M.4 | not-applicable | judgement | `input.csv`, `object inventory` | N/A: the delivered object contains no restricted data or software component. |
| may/001 | M.2 | not-applicable | probe:subdatasets-resolvable+judgement | `probe:subdatasets-resolvable`, `requirements.txt` | N/A: there are no independently maintained project components; NumPy is a runtime package dependency, not a project module. |
| may/002 | M.2 | unmet | judgement | `probe:modules-separated`, `probe:entry-point` | No documentation describes a modular structure or how components relate. |
| may/003 | M.2 | unmet | judgement | `analysis.py`, `requirements.txt` | The input, script, and environment declaration have no defined module boundaries or independent update mechanism. |
| may/004 | M.2 | unmet | judgement | `analysis.py` | No module composition mechanism is defined; the script directly reads one file from its working directory. |
| may/005 | M.2 | unmet | judgement | `probe:entry-point`, `object inventory` | No navigation documentation or tooling explains the object's structure to users. |

## Flagged items

- **must/004 — probe-overridden, mapping-questioned:** `tree-clean` measured whether paths were committed; that alone does not answer whether Git is used. Git tracks the input and ignore rule, while the delivered code, requirements, and ignored result are outside tracked history; verdict partial.
- **must/006 — mapping-questioned:** `derived-have-records` called the input `input.csv` a derived file. The actual derived file is `products/estimate.json`; it has no delivery run record, so the unmet verdict rests on the result and lack of provenance.
- **must/008 — probe-overridden:** the entry-point probe considered tracked paths only and missed the delivered `analysis.py`. It is the clear main script, though usage instructions are absent.
- **must/010 — probe-overridden, mapping-questioned:** `env-spec-tracked` measured whether a specification is tracked, while this item asks whether dependencies are specified. The untracked `requirements.txt` specifies NumPy but omits Python and exact versions; partial.
- **must/014 and should/008 — upstream-duplicate:** the checklist repeats the environment-update question word for word; both use the same evidence and verdict.
- **must/016 — mapping-questioned:** absence of a tracked environment file alone does not prove publication failure. The object has no configured remote and no environment publication instructions; unmet.
- **should/001 — mapping-questioned:** the clean-tree probe does not itself establish a common version-control system across components. The input is Git tracked; the delivered code and environment specification are not.
- **should/003 — probe-overridden:** the probe counted only tracked paths. The delivered output is in `products/`, while input, code, and environment specification are at the root; partial.

## Not checked

- **should/002:** no CI or repeated-test record appears in this delivery. A reachable test/run archive or repeat history would settle whether the workflow is tested regularly.
- **should/004:** no fresh-environment run is recorded. A run in a clean environment with its result and matching specification would settle this.
- **should/006:** no reconstitution check is recorded. Repeated clean rebuild records using the result-producing specification would settle this.

## Goals and kind

The assessment prompt states the scientific goal: report the count and arithmetic mean of finite observations in `input.csv`. With no user available, this is an explicit assumption, not a confirmed project goal. The primary kind is **study** because the product is a computed answer from supplied observations. That emphasizes traceable results and a self-contained boundary while retaining all checklist requirements.

The original stop receipt says the supplied seed was commit `5f3aefd0ea525d8526ee47e06c6ffd0a4d2ce6e7`, tracking only `.gitignore` and `input.csv`. At original delivery the same commit remained HEAD, `analysis.py` and `requirements.txt` were untracked, and `products/` was ignored; no commits followed the seed. I assessed these original delivered bytes, not just Git history. The receipt records hashes for all five paths. The object has no configured Git remote, so no external tracker or publication claim could be checked. No replay was attempted. No instruction-like content was found in the object.

Checklist URL: [open the filled STAMPED checklist](2026-10-16-url.txt)  
Machine-readable record: [2026-10-16-response.json](2026-10-16-response.json)  
Probe output: [2026-10-16-probes.json](2026-10-16-probes.json)

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on object commit `5f3aefd0ea525d8526ee47e06c6ffd0a4d2ce6e7`, 2026-10-16, Codex Desktop (subagent; exact version unavailable) / GPT-6 (exact model build unavailable). Exact harness/model build metadata was unavailable and is recorded without guessing. Probe output: [2026-10-16-probes.json](2026-10-16-probes.json).
