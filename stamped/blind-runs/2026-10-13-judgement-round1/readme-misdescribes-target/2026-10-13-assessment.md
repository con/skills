# STAMPED assessment — stamped-eval-fixture-r0, commit `fc0b262`

## Verdict

- **MUST** (17): 16 met / 1 partial (counts as a MUST failure, per convention) / 0 unmet / 0 not-checked
- **SHOULD** (9): 5 met / 2 partial / 1 unmet / 1 not-applicable / 0 not-checked
- **MAY** (5): 3 met / 2 unmet / 0 partial / 0 not-applicable / 0 not-checked

No single overall score (per convention).

## What to fix first

1. **Make the README's "Reproduce" section true, or change the Makefile to match it.**
   README.md L33-34 says "`make all` also installs the environment and fetches the inputs, so the clone
   above is the only manual step" — but `Makefile` has no rule that installs dependencies or fetches the
   submodule, and the README's own Install section (L8-12) already requires a separate manual venv+pip
   step. Following the Reproduce recipe exactly, as written, does not work. Closes: must/017, should/002.
2. **Document how to obtain and use the container the README says the analysis runs in.**
   README.md L14 claims "The analysis step runs inside the container pinned in `code/containers.json`,"
   but no instructions anywhere say how to pull or build that image (digest `sha256:3e0f1b6c…` for
   `docker://python`), and `code/containers/plotting.sif.README` discloses the tracked file is a
   placeholder. Closes: must/017.
3. **Either run the Makefile inside the recorded container, or stop implying it does.**
   The two `[DATALAD RUNCMD]` records (`9c80df0`, `312a526`) show the shipped results were produced via
   `apptainer exec code/containers/plotting.sif python3 …`, but `Makefile` calls bare `python3 …` with no
   container at all, and CI (`.github/workflows/rerun.yml`) never invokes apptainer either. The
   re-executable path and the provenance record describe two different mechanisms. Closes: should/005,
   should/006.
4. **Add a short note on the modular layout.**
   `docs/README.md`'s entire content is "Notes on the method live here." — there is no documentation of how
   `sourcedata/`, `code/`, `results/`, `figures/` and the environment specs relate or recombine, even though
   the separation itself (should/003) is real. Closes: may/002, may/005.
5. *(Lower leverage, same root cause as #1)* Fix the Usage comment's step order: it lists "draws the
   figure, and writes the … volumes" but the Makefile draws the figure only *after* `results/volumes.tsv`
   exists — the comment has the two steps backwards.

## What the project already does well

- **The input dataset is a real, resolvable module**, not a path or a copy: `.gitmodules` names
  `https://github.com/OpenNeuroDatasets/ds007116.git`, which independently resolves (`HTTP 200` and a
  working `git-upload-pack` probe at that URL, checked without cloning).
- **Every derived file in the object traces to a committed, container-naming run record** — `9c80df0` and
  `312a526` both carry `[DATALAD RUNCMD]` JSON naming inputs, outputs and the exact container, and no
  `:latest` reference is tracked anywhere (must/006, must/015).
- **The tree is genuinely the whole state**: `git status --porcelain` is empty, the submodule is clean and
  pinned, and no host-specific absolute path appears in any tracked text file.

## Per-item table

MUST first, then SHOULD, then MAY. `src` = probe name or `judgement`; an item with `source` ending
`+judgement` was a probe verdict overridden by a reading of the object.

| id | principle | status | src | evidence (abridged) |
|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `git ls-files` — all 16 tracked paths under one root |
| must/002 | S.1 | met | probe:subdatasets-resolvable | `.gitmodules` URL resolves (confirmed live) |
| must/003 | S.1 | met | judgement | requirements.lock + code/containers.json, both under boundary |
| must/004 | T.1/T.3/T.5 | met | probe:tree-clean | `git status --porcelain` empty |
| must/005 | T.1/T.3/T.5 | met | probe:large-in-annex | no blob > 10 MiB; nothing needs annex |
| must/006 | T.1/T.3/T.5 | met | probe:derived-have-records+run-env-linked | 2/2 derived files trace to run records naming the container |
| must/007 | A.1 | met | probe:entry-point | README.md has install/usage/reproduce sections (existence only) |
| must/008 | A.1 | met | probe:entry-point | Makefile + named scripts present |
| must/009 | P.1 | met | probe:no-abs-paths | 16 tracked paths scanned, 0 hits |
| must/010 | P.1 | met | probe:env-spec-tracked | requirements.lock pinned |
| must/011 | P.1 | met | judgement | no undocumented host assumption beyond documented python3/venv |
| must/012 | P.2 | met | judgement | README Install + requirements.lock list exact versions |
| must/013 | P.3 | met | probe:env-spec-tracked | requirements.lock tracked |
| must/014 | P.3 | met | judgement [upstream-duplicate] | requirements.lock header names the regen command; no update commit exists yet to show it followed |
| must/015 | D.1 | met | probe:run-env-linked | both run records pin the container by digest, no `:latest` |
| must/016 | D.1 | met | probe:env-spec-tracked | spec tracked in a repo published at the recorded remote |
| **must/017** | D.1 | **partial** | judgement | venv path documented; **container obtain/use path is not**, despite README claiming it's used |
| should/001 | T.2 | met | judgement | one VCS (git + git submodule) across all components; `is_datalad: false` |
| **should/002** | A.2 | **partial** | probe:ci-present+judgement [probe-overridden] | CI tests a sequence the README's Reproduce recipe does not describe |
| should/003 | M.1 | met | probe:modules-separated | inputs/code/derived/environment each in distinct dirs |
| should/004 | E.1 | met | judgement | GH Actions `ubuntu-latest` is a fresh VM per job (equivalent evidence) |
| **should/005** | E.1 | **partial** | judgement | isolation is job-level only; Makefile has no per-execution container, unlike the original run |
| **should/006** | D.2 | **unmet** | probe:ci-present+judgement [probe-overridden, mapping-questioned] | CI never exercises the apptainer container that actually produced the results |
| should/007 | D.2 | met | judgement [unverified-claim] | `plotting.sif` + digest both tracked (placeholder per its own README) |
| should/008 | D.2 | met | judgement [upstream-duplicate] | same evidence as must/014 |
| should/009 | M.4 | not-applicable | judgement | N/A: no restricted data/software exists in the object (ds007116 is CC0) |
| may/001 | M.2 | met | probe:subdatasets-resolvable | sourcedata/ds007116 linked as a module |
| **may/002** | M.2 | **unmet** | judgement | no documentation of the modular structure anywhere |
| may/003 | M.2 | met | judgement | submodule pin + decoupled Makefile rules allow independent updates |
| may/004 | M.2 | met | judgement | git submodules + Makefile are the composition mechanism |
| **may/005** | M.2 | **unmet** | judgement | docs/ exists but carries no real navigational content |

## Flagged items

- **must/014** `upstream-duplicate` — same sentence as should/008; answered once, from requirements.lock's
  header comment.
- **should/002** `probe-overridden` — `ci-present` reported `met` because `rerun.yml` matches `/make\b/`;
  a reading shows CI's actual steps diverge from the README's documented Reproduce recipe, so the verdict
  is downgraded to `partial`.
- **should/006** `probe-overridden`, `mapping-questioned` — `ci-present`'s regex only checks for the
  literal word "make" in CI config text; it never checks *which* environment mechanism CI exercises. The
  item asks specifically about the environment that produced the shipped results (the apptainer container
  per the run records), which CI never touches. Downgraded `met` → `unmet`.
- **should/007** `unverified-claim` — resting on `plotting.sif.README`'s own disclosure that the tracked
  binary is a fixture placeholder; taken at face value rather than independently confirmed, since
  confirming it would mean pulling/verifying a real container image (out of scope here).
- **should/008** `upstream-duplicate` — same sentence as must/014.

## Not checked

None. All 31 items carry a status other than `not-checked` in this run (the probe sweep's own
"no probe covers this item" placeholders were all replaced with judgement answers in Step 4, as the skill
requires).

Deliberately skipped, by the operating constraints of this run (not part of any item's denominator):
- `fresh_rerun.py` (the expensive probe) — not run; `should/004` was answered instead from equivalent
  committed evidence (CI on a fresh GH Actions VM), per the skill's explicit guidance for this case.
- `gh issue list --repo con/stamped-eval-fixture-r0` — the recorded remote returns `404` from
  `api.github.com` (unauthenticated), so there is no reachable issue tracker to check for already-tracked
  gaps; none of the findings above are reported as already known.
- Pulling/verifying the real `docker://python` image behind the digest in `code/containers.json`.

## Goals and kind

**Stated goal** (README.md L1-6): "A tiny, fully recorded study: it reads the FreeSurfer tables that
ds007116 ships, joins them with the per-session ages, and plots brain volume with the GM/WM ratio on a
secondary axis against age."

**Kind: `study`** (primary, no secondary kind). Per `project-kinds.md`, a study is read against all seven
principles with **T** and **S** weighted most heavily — both are met here (clean tree, resolvable module,
both derived files have run records).

**ASSUMPTION (labelled, since no user is present to confirm):** The user was not available in this run.
The kind `study` is adopted because the documentation plainly describes a one-shot analysis of a public
input dataset producing a figure and a table, with no indication it is meant as a reusable library,
component, or skill. If the object is actually intended as a template for other brain-volume-vs-age
studies (a `component`), the emphasis would shift toward **A** (tests, entry point) and **E**
(ephemerality), which would raise the weight of the should/005/006 findings above but would not change
any verdict, since none of them turned on the kind.

## Checklist URL and stamp

URL (persistence format 3, checklist 0.3.1): see `2026-10-13-url.txt` in this directory (9319 characters —
too long to inline safely).

> Produced by `assess-alignment-with-stamped-principles` 0.2.0 with `stamped-conventions` 0.2.0, checklist
> 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on `https://github.com/con/stamped-eval-fixture-r0.git`
> at commit `fc0b262552af3668243c0dc13d9db2063967e116`, 2026-10-13, claude-code (agent run)/claude-sonnet-5.
> Probe output: `2026-10-13-probes.json`.
> Response JSON: `2026-10-13-response.json`.
