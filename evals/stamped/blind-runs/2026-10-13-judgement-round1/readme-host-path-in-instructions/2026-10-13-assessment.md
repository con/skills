# STAMPED Assessment: Brain volume versus age in ds007116 (R0)

**Verdict line:** MUST: 12 met / 3 partial / 2 unmet (17 items); SHOULD: 6 met / 1 partial / 1 unmet / 1 not-applicable (9 items); MAY: 5 met (5 items).

## What to fix first

1. **Verify or replace the linked input dataset's commit.**
   The submodule `sourcedata/ds007116` is pinned to commit `84570256`, which does not exist in the upstream repository. A stranger cannot clone and initialize this submodule. Either verify that the commit exists upstream (repin to a published commit), or explain why this object is offline-only.
   *Closes: must/002.*

2. **Publish the repository or document offline use.**
   The remote origin URL names a repository marked as "not published." If reproducibility requires publication, either publish the remote or document that this object is intended for offline use within a lab network.
   *Closes: must/016.*

3. **Remove or document the lab-filer paths in the README.**
   The README contains hardcoded paths to a lab share (`/mnt/labshare/openneuro/ds007116`) that a reader cannot access. Either remove these paths (reference the linked submodule instead), or move them to a separate "advanced setup" section that makes clear they are optional.
   *Closes: must/009.*

4. **Document how to obtain the container image.**
   The README instructs readers to install Python and then run `make all`, but does not say how to obtain the container image (digest `sha256:3e0f1b6c...`). State whether to rebuild from a Dockerfile, pull from Docker Hub, or use the placeholder if running on the published CI system.
   *Closes: must/017.*

5. **Track environment updates in history (if dependencies change).**
   The environment specifications (requirements.lock and code/containers.json) carry a declared update process but no execution history—both files are from the initial commit and unchanged. This is not a failure yet, but document the process and apply it the next time dependencies change (e.g., add a comment to requirements.lock explaining the update procedure).
   *Closes: must/014, should/008.*

## What the project already does well

- **Run records are complete and precise.** Every derived file (`results/volumes.tsv`, `figures/brain-volume-vs-age.png`) has a git commit with `[DATALAD RUNCMD]` and names the container digest used, linking environment and computation.

- **Modular structure is documented and reusable.** The docs/README.md explains each module's role (input, code, output, environment), how they can be replaced independently (e.g., "swap input module for another BIDS dataset with FreeSurfer derivatives"), and the Makefile makes the composition explicit.

- **CI validates the entry point on every push.** The .github/workflows/rerun.yml workflow runs on a fresh ubuntu-latest VM, installs dependencies, and re-executes `make all`, confirming that the documented instructions work.

## Per-item checklist

| ID | Codes | Status | Reason |
|---|---|---|---|
| must/001 | S.1 | met | All components (code, inputs, results, environment) are nested under a single root; input dataset is linked as a submodule. |
| must/002 | S.1 | unmet | The linked module URL resolves, but the recorded commit 84570256 does not exist in the upstream repository. |
| must/003 | S.1 | met | External software (Python packages, container image) are specified in requirements.lock and code/containers.json, tracked in the repository. |
| must/004 | T.1,T.3,T.5 | met | Git is used for code, text, documentation, and configuration files; committed state is clean. |
| must/005 | T.1,T.3,T.5 | met | No binary blob in git exceeds 10 MiB; nothing in this object requires a large-content mechanism. |
| must/006 | T.1,T.3,T.5 | met | All derived files trace to re-executable records (2 run records with [DATALAD RUNCMD]). |
| must/007 | A.1 | met | README.md has install/usage/reproduce sections; Makefile names targets and entry points. |
| must/008 | A.1 | met | Clear starting point: `code/collect_volumes.py` and `code/plot_volumes.py`, with make targets. |
| must/009 | P.1 | partial | No script uses hardcoded paths, but README.md line 44 names a lab-filer path (`/mnt/labshare/openneuro/ds007116`); this is in docs only, not executed. |
| must/010 | P.1 | met | Dependencies pinned in requirements.lock; no tracked script expects a pre-installed tool. |
| must/011 | P.1 | met | No platform-specific commands (brew, BSD sed, sbatch) in tracked text. |
| must/012 | P.2 | met | Requirements.lock and code/containers.json document system and software dependencies. |
| must/013 | P.3 | met | requirements.lock and code/containers.json are in version control with code and config. |
| must/014 | P.3 | partial | Process declared in README ("python3 -m venv...pip install -r requirements.lock") but no updates tracked in version history; both env files from initial commit, never changed. |
| must/015 | D.1 | met | 2 run records reference a pinned image digest; no ':latest' reference is tracked. |
| must/016 | D.1 | unmet | The remote repository is simulated as not published in this fixture; environment specs are tracked but not accessible from a published remote. |
| must/017 | D.1 | partial | Python environment documented ("pip install -r requirements.lock") but container acquisition method not documented (rebuild, download, placeholder). |
| should/001 | T.2 | met | Git is used across all components (code, config, documentation, input submodule). |
| should/002 | A.2 | met | CI workflow (.github/workflows/rerun.yml) re-executes on every push, testing the instructions. |
| should/003 | M.1 | met | Raw data, code, environment, and results are in distinct directories: sourcedata, code, code/containers.json, results, figures. |
| should/004 | E.1 | met | CI runs on ubuntu-latest, a fresh GitHub Actions VM per execution. |
| should/005 | E.1 | met | Each CI run has a disposable GitHub Actions environment; complete isolation between runs. |
| should/006 | D.2 | met | CI workflow (.github/workflows/rerun.yml) reconstitutes the pinned environment (pip from requirements.lock). |
| should/007 | D.2 | unmet | Container image (code/containers/plotting.sif) is pinned by digest but not archived; only a 28-byte placeholder file exists. |
| should/008 | D.2 | partial | Same as must/014 (duplicate checklist item): process declared, no execution history. |
| should/009 | M.4 | not-applicable | No restricted data or software in the object; all inputs are public OpenNeuro data. |
| may/001 | M.2 | met | Input dataset is linked as a git submodule (sourcedata/ds007116). |
| may/002 | M.2 | met | Modular structure documented in docs/README.md, explaining how modules relate and can be recombined. |
| may/003 | M.2 | met | Makefile dependencies define module boundaries; each step depends only on what it reads. |
| may/004 | M.2 | met | Makefile is the composition mechanism; explicit targets define how modules are combined. |
| may/005 | M.2 | met | Documentation guides users through modular structure and how to reuse/replace components. |

## Flagged items

- **must/002**: `probe:subdatasets-resolvable+judgement` — Probe checked URL resolution only; manual verification shows the recorded commit does not exist upstream. `[probe-overridden]`
- **must/016**: `probe:env-spec-tracked+judgement` — Probe affirmed publication; fixture design sets this as not published. `[probe-overridden]`
- **should/008**: Duplicate of must/014 (checklist item text is identical). `[upstream-duplicate]`

## Not checked

None; all 31 items have a verdict.

## Goals and kind

**Goals** (from README.md): Does brain volume grow with age over 8–20 years, and does the grey/white matter ratio fall over the same range?

**Kind**: Study.
- **Emphasis**: All seven principles; **T** (every derived file has a re-executable record) and **S** (inputs under the boundary as a submodule, not a path) carry the most weight.

## Checklist URL and provenance stamp

See `2026-10-13-url.txt` for the checklist-app link.

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on `https://github.com/con/stamped-eval-fixture-r0.git` at commit `91f2e00`, 2026-10-13, claude-haiku-4-5-20251001.
Probe output: `2026-10-13-probes.json`.
Response JSON: `2026-10-13-response.json`.

