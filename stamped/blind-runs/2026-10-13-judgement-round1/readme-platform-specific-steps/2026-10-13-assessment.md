# STAMPED assessment — brain-volume-vs-age study (ds007116, R0)

Object: `https://github.com/con/stamped-eval-fixture-r0.git` at commit `c77ad04f` (checked out locally;
origin returns 404, see Scope note below). Checklist `0.3.1`. Assessed read-only; nothing was changed.

## Verdict

- **MUST: 13 met / 2 partial / 2 unmet / 0 not-checked** (of 17)
- **SHOULD: 2 met / 4 partial / 1 unmet / 1 not-checked / 1 not-applicable** (of 9)
- **MAY: 3 met / 2 partial** (of 5)

(`partial` never counts as satisfying a MUST; 4 of 17 MUST items fail outright.)

## What to fix first

1. **State the OS this project needs, or stop assuming it (must/011, unmet).**
   `README.md`'s Install block (added in commit `c77ad04`, "spell out the install steps") runs
   `brew install python@3.12 freesurfer`, `sed -i '' ...` (BSD `sed` syntax) and
   `make all -j $(sysctl -n hw.ncpu)` — all three macOS-only — with no statement anywhere that macOS is
   required. A Linux reader hits `sysctl: command not found` and a no-op `sed` with no explanation, while
   `.github/workflows/rerun.yml` (`runs-on: ubuntu-latest`) proves the pipeline itself needs none of this.
   Closes: must/011.

2. **Make the README's container claim true, or remove it (must/017, unmet).**
   The README says "the analysis step runs inside the container pinned in `code/containers.json`," but
   `Makefile`'s recipe for `figures/brain-volume-vs-age.png` calls bare `python3 code/plot_volumes.py ...`
   — no `apptainer`/`docker` invocation anywhere, and no command is given to obtain the container either.
   Following the documented Reproduce steps never touches the pinned environment. Closes: must/017.

3. **Drop the spurious FreeSurfer dependency (must/012, partial).**
   `README.md` line 11 tells installers to `brew install ... freesurfer`, but neither
   `code/collect_volumes.py` nor `code/plot_volumes.py` calls FreeSurfer — they only parse the
   `*_qc.tsv` tables `ds007116` already ships under `derivatives/freesurfer-post/`. CI proves this by
   running the full pipeline with no FreeSurfer install. Closes: must/012; also removes the strongest
   false lead for item 1 above.

4. **Archive (or at least point CI at) the environment that actually produced the results (should/007, unmet; should/006, partial).**
   The two `[DATALAD RUNCMD]` commits (`ebe8aa1`, `b230d4f`) record
   `apptainer exec code/containers/plotting.sif ...` as the command that generated `results/volumes.tsv`
   and the figure, but `code/containers/plotting.sif` is not a tracked path at all (`git ls-files code`
   lists only `collect_volumes.py`, `containers.json`, `plot_volumes.py`, `requirements.in`). CI
   reconstitutes a different, container-free environment (`pip install -r requirements.lock; make all`)
   that happens to reproduce the same output shape, but never exercises the one the provenance record
   names. Closes: should/007; improves should/006.

5. **Give `docs/README.md` actual content, or point may/002's reader elsewhere (may/002, may/005, partial).**
   `docs/README.md` is the single line "Notes on the method live here." with nothing behind it, and the
   main README never lays out the module structure explicitly — a reader has to reverse-engineer it from
   the `Makefile`. Closes may/002, may/005.

## What the project already does well

- **Every derived file traces to a run record.** `results/volumes.tsv` and
  `figures/brain-volume-vs-age.png` both have a `[DATALAD RUNCMD]`-style commit (`ebe8aa1`, `b230d4f`)
  naming the exact command, inputs and outputs — must/006 is cleanly met.
- **The one external input is a properly resolvable module.** `.gitmodules` links
  `sourcedata/ds007116` to `https://github.com/OpenNeuroDatasets/ds007116.git`; I independently confirmed
  it resolves (`git ls-remote` returned `HEAD` without error) rather than trusting the probe alone.
- **The dependency pin is real and tracked.** `requirements.lock` pins `matplotlib==3.9.2` and
  `pandas==2.2.3`, and its header comment even names the regeneration command
  (`uv pip compile code/requirements.in`) — a small thing most projects skip.

## Per-item table

MUST

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| must/001 | S.1 | met | `git ls-files` (14 paths, all under root) | All tracked paths incl. the 1 submodule sit under the object root |
| must/002 | S.1 | met | `.gitmodules`; `git ls-remote` (confirmed) | sourcedata/ds007116 url resolves from elsewhere |
| must/003 | S.1 | met | `requirements.lock`; `code/containers.json` | Real dependencies pinned/contained; README's freesurfer mention is spurious (see must/012) |
| must/004 | T.1/T.3/T.5 | met | `git status --porcelain` (empty) | Committed state is the whole state |
| must/005 | T.1/T.3/T.5 | met | `git ls-tree -r -l HEAD` | No binary blob > 10 MiB; nothing large here |
| must/006 | T.1/T.3/T.5 | met | commits `b230d4f`, `ebe8aa1` | Both derived files trace to a run record |
| must/007 | A.1 | met | `README.md` Install/Usage/Reproduce sections | Instructions for install and usage exist (accuracy issues are must/011/012/017, not this item) |
| must/008 | A.1 | met | `code/collect_volumes.py`, `Makefile` targets | Clear starting point named and present |
| must/009 | P.1 | met | probe scan, 0 hits | No host-specific absolute paths in tracked text |
| must/010 | P.1 | met | `requirements.lock` | Dependencies pinned; no script expects a preinstalled tool |
| **must/011** | P.1 | **unmet** | `README.md#L11,13,14`; `.github/workflows/rerun.yml#L5` | macOS-only commands added, OS requirement never stated, contradicted by CI |
| must/012 | P.2 | partial | `README.md#L11` vs `code/collect_volumes.py` | FreeSurfer listed as required but never invoked |
| must/013 | P.3 | met | `requirements.lock` | Spec is tracked |
| must/014 | P.3 | partial | `requirements.lock#L1`; `git log` (1 commit) | Regeneration command named, no described process, never exercised |
| must/015 | D.1 | met | commits `b230d4f`, `ebe8aa1` | Pinned image/lockfile named, no `:latest` |
| must/016 | D.1 | met | `requirements.lock`; remote url | Spec tracked in a repo with a (nominally) published remote |
| **must/017** | D.1 | **unmet** | `README.md` vs `Makefile#L5-6` | Container claimed but never invoked by the documented reproduce path |

SHOULD

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| should/001 | T.2 | met | `.gitmodules`; `git submodule status` | Git is the only VCS, used for both components |
| should/002 | A.2 | partial (overridden) | `.github/workflows/rerun.yml` vs `README.md#L11-15` | CI tests `make all`, never the Install/container steps |
| should/003 | M.1 | met | `sourcedata/`, `code/`, `results/`+`figures/`, `requirements.lock`+`code/containers.json` | 4 distinct module kinds |
| should/004 | E.1 | not-checked | — | Fresh rerun not attempted (cost/consent; see Not checked) |
| should/005 | E.1 | partial | run records vs `.github/workflows/rerun.yml` | Local runs apptainer-isolated per step; CI shares one VM, no per-step container |
| should/006 | D.2 | partial (overridden) | `.github/workflows/rerun.yml` vs run records | CI never invokes the container the records say produced the results |
| should/007 | D.2 | unmet | `git ls-files code` (no `containers/` dir) | The named `.sif` artifact isn't archived anywhere in the object |
| should/008 | D.2 | partial | same as must/014 | Duplicate item, same evidence |
| should/009 | M.4 | not-applicable | `sourcedata/ds007116/dataset_description.json` (`License: CC0`) | N/A: no restricted component exists |

MAY

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| may/001 | M.2 | met | `.gitmodules` | External component linked as a module |
| may/002 | M.2 | partial | `README.md`; `docs/README.md` | Paths named in prose only; no structure section; docs stub |
| may/003 | M.2 | met | `.gitmodules`; `Makefile#L5` | Submodule boundary updatable independently of code |
| may/004 | M.2 | met | `.gitmodules`; `Makefile` | Git submodules + Makefile compose the modules |
| may/005 | M.2 | partial | `docs/README.md` | Stub file, no real navigation aid |

## Flagged items

- **should/002** — `probe-overridden`. `ci-present` reported `met` because `.github/workflows/rerun.yml`
  matches on `make`; a reading shows CI never exercises the README's Install section (brew/sed/sysctl) or
  its claimed containerized execution, only the `make all` step. Downgraded to `partial`.
- **should/006** — `probe-overridden`. Same probe, same `met`; a reading shows the "exact environment
  specification used to generate" the shipped results (per the run records) is the apptainer container,
  which CI never touches — CI tests a different, simpler environment that happens to agree on output.
  Downgraded to `partial`.
- All other items: none.

## Not checked

- **should/004** — fresh rerun not attempted. `scripts/fresh_rerun.py` needs another host, real compute
  time, and the user's consent to that cost; the user was not available in this run to give it, per this
  run's operating constraints. Settling it: re-run with `fresh_rerun.py --url <published-url> --entry
  'make all'` on a throwaway host once that's acceptable.

## Goals and kind

**Goals** (from `README.md`): "a tiny, fully recorded study" that joins `ds007116`'s shipped FreeSurfer
tables with per-session ages and plots brain volume (and GM/WM ratio) against age — a small, self-described
reproducibility demonstration, not a scientific claim of its own.

**Kind: `study`** (primary), with a secondary **dataset-consumer** flavor (it only reads another dataset's
derivatives, producing none of its own raw/intermediate data). **Assumption, stated explicitly because the
user was not available to confirm it in this run:** I treated this as a `study` per
`project-kinds.md` ("a question answered with data and compute... T and S carry the most weight"), since
that is what the README claims for itself and the DATALAD-RUNCMD-style provenance trail supports. Under
this kind, T (every derived file has a re-executable record) and S (inputs under the boundary) are
emphasized, which is why must/006, must/001 and must/002 were checked most carefully — and is also why the
must/011/must/017 gaps matter more here than they might for a one-off exploratory script.

## Checklist URL and stamp

URL: written to `out/2026-10-13-url.txt` (9128 chars; omitted from this report's body since it embeds the
entire response as base64 and would dwarf the table above — open the file or decode
`out/2026-10-13-response.json` directly).

Produced by `assess-alignment-with-stamped-principles` 0.2.0 with `stamped-conventions` 0.2.0, checklist
0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on `https://github.com/con/stamped-eval-fixture-r0.git`
at commit `c77ad04f`, 2026-10-13, claude-code (agent SDK)/claude-sonnet-5.
Probe output: `out/2026-10-13-probes.json`. Response JSON: `out/2026-10-13-response.json`.

**Scope note:** the object's own `origin` remote (`https://github.com/con/stamped-eval-fixture-r0.git`)
returns HTTP 404 — it does not resolve publicly (confirmed via `curl`). This looks like fixture packaging
rather than a defect of the object itself, so it was not counted against must/016 (which only checks the
URL's shape, as the probe does), but a reader should not take "published at …" in must/016's evidence
literally for this particular object.
