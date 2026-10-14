# STAMPED assessment — `stamped-eval-fixture-r0` object at `776596a`

## Verdict line

- **MUST:** 13 met / 2 partial / 2 unmet / 0 not-checked (17)
- **SHOULD:** 5 met / 3 partial / 0 unmet / 0 not-checked / 1 not-applicable (9)
- **MAY:** 5 met / 0 partial / 0 unmet / 0 not-checked (5)

No single overall score.

## What to fix first

1. **The root `dataset_description.json` contradicts every other account of what this object is.**
   It names `SourceDatasets: ///openneuro/ds000003`, `GeneratedBy: fMRIPrep 23.2.0` and
   `DatasetType: raw`. `.gitmodules`, `README.md`, `docs/README.md`, the `Makefile` and both
   `[DATALAD RUNCMD]` records agree instead that the input is `ds007116`, the pipeline is two
   custom Python steps joining FreeSurfer tables the input already ships (no fMRIPrep step exists
   anywhere in this object), and the product is a derived study, not raw data. A reader or tool
   that trusts the BIDS metadata file first — which is exactly what it is for — draws a false
   picture of provenance and lineage. No checklist item names this property directly, so it is
   reported as the extra item `dataset-description-accuracy` (`unmet`); it is also why `object.kind`
   is recorded as `study` here rather than taken from the file's own `DatasetType`. **Fix:** make
   `dataset_description.json` agree with `.gitmodules`/`README.md`, or remove the fields it gets
   wrong.
2. **The environment the results were actually produced in is not the one a fresh run would use.**
   Both run records show `apptainer exec code/containers/plotting.sif python3 ...`, and `README.md`
   / `docs/README.md` both say the steps "run inside" that container — but the tracked `Makefile`
   (and the CI job that exercises it) call `python3` directly, with no container at all. Closes
   `must/017` (partial), `should/005` (partial), `should/006` (partial).
   **Fix:** wrap the `Makefile` targets in the same `apptainer exec` the run records name, or stop
   claiming in the docs that they are.
3. **The two environment-sharing MUSTs don't hold for a stranger.** `sourcedata/ds007116` is pinned
   to a commit (`8457025`) that `git fetch` against the real upstream rejects as "not our ref", and
   `remote.origin.url` (`.../con/stamped-eval-fixture-r0.git`) does not answer `git ls-remote` at
   all. Both probes reported these as `met` from url shape alone; verifying against the network
   flips them. Closes `must/002`, `must/016` (both `unmet`).
4. **CI checks that the container spec is readable, not that it reconstitutes.** `rerun.yml` prints
   the digest and does `test -e code/containers/plotting.sif`, then runs `make all` with a plain
   `pip install` — never an `apptainer exec`. Closes `should/006` (partial), and is the same gap as
   item 2.
5. **The declared lockfile-update process has never run.** `requirements.lock` documents
   `uv pip compile code/requirements.in` in its header, but the object's five-commit history shows
   no instance of that command having been re-run since the initial pin. Closes `must/014` and
   `should/008` (both `partial` — the checklist's own duplicate question).

## What the project already does well

- **The layout is genuinely modular and it is documented as such.** `README.md`'s Layout table and
  `docs/README.md`'s per-component walkthrough both describe inputs, code, environment and products
  as separable, and the `Makefile` rules back that claim by keying on file paths rather than step
  names (`modules-separated`: met on `should/003`; `may/002`–`may/005`: met).
- **Every derived file traces to a re-executable record.** Both `results/volumes.tsv` and
  `figures/brain-volume-vs-age.png` are named as outputs in a `[DATALAD RUNCMD]`-style commit
  message that also names their inputs and the pinned container (`must/006`: met).
- **No host lock-in.** Nothing in the tracked text depends on a host-specific absolute path or a
  platform-only command (Homebrew, BSD flags, a scheduler); `requirements.lock` pins exact versions
  with no floating tag (`must/009`, `must/010`, `must/011`, `must/012`, `must/015`: all met).

## Per-item table

### MUST

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| must/001 | S.1 | met | `.gitmodules`; `README.md#Layout` | All essential parts reachable under the root; input linked, not copied. |
| must/002 | S.1 | **unmet** | verified: `git fetch --depth=1 ...ds007116.git 8457025` → "not our ref" | Pinned commit does not exist upstream; a fresh clone's `submodule update --init` fails. |
| must/003 | S.1 | met | `code/containers.json`; `code/containers/plotting.sif.README` | External software linked within the boundary, not assumed present. |
| must/004 | T | met | `git status --porcelain` empty, incl. submodules | Committed state is the whole state. |
| must/005 | T | met | `git ls-tree -r -l HEAD` | No binary blob > 10 MiB; nothing large-binary in this object. |
| must/006 | T | met | 2 run records name `inputs`/`outputs`/`extra_inputs` (container+digest) | All derived files trace to a re-executable, environment-naming record. |
| must/007 | A.1 | met | `README.md` install/usage/reproduce section | Instructions exist and the named entry point is present. |
| must/008 | A.1 | met | `code/collect_volumes.py` | Clear starting point present. |
| must/009 | P.1 | met | scan of all tracked text, 0 hits | No host-specific absolute paths. |
| must/010 | P.1 | met | `requirements.lock` | Dependencies pinned; no script expects a pre-installed tool. |
| must/011 | P.1 | met | scan of all tracked text, 0 hits | No undocumented platform-specific command. |
| must/012 | P.2 | met | (same scan) | No undocumented system requirement. |
| must/013 | P.3 | met | `requirements.lock` tracked | Environment spec is in version control. |
| must/014 | P.3 | **partial** | `requirements.lock#L1`; `git log --oneline` (5 commits, lock touched once) | Regeneration command declared; no instance of it running since. `[upstream-duplicate]` |
| must/015 | D.1 | met | `code/containers.json` digest; no `:latest` tag anywhere | Pinned image/lockfile, no floating reference. |
| must/016 | D.1 | **unmet** | verified: `git ls-remote https://github.com/con/stamped-eval-fixture-r0.git` → fails, no refs | Recorded remote does not resolve; a stranger cannot retrieve the spec there. `[probe-overridden]` |
| must/017 | D.1 | **partial** | `README.md#L14`; `Makefile` (no apptainer wrapper) | Docs assert container execution; the only runnable instruction bypasses it. |

### SHOULD

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| should/001 | T.2 | met | `.gitmodules`; `sourcedata/ds007116/.git` | Superproject and linked input both use git. |
| should/002 | A.2 | met | `.github/workflows/rerun.yml` | CI re-executes `make all` on every push. |
| should/003 | M.1 | met | `sourcedata`, `code`, `results`/`figures`, `code/containers.json` | Four kinds of component in distinct places. |
| should/004 | E.1 | met | `.github/workflows/rerun.yml` (`runs-on: ubuntu-latest`) | Fresh-runner CI job is equivalent evidence; no `fresh_rerun.py` run. |
| should/005 | E.1 | **partial** | run records (`apptainer exec ...` per step) vs. `Makefile`/CI (bare `python3`) | The two accounts of how each step executes disagree. |
| should/006 | D.2 | **partial** | `.github/workflows/rerun.yml` (digest print + `test -e`, no exec) | CI checks the spec is readable, not that it reconstitutes. `[probe-overridden]` |
| should/007 | D.2 | met | `code/containers/plotting.sif` tracked at the recorded path | Artifact archived in-tree, not only referenced (fixture discloses it is a placeholder). |
| should/008 | D.2 | **partial** | same as must/014 | Same sentence as must/014; same evidence. `[upstream-duplicate]` |
| should/009 | M.4 | N/A | `LICENSE` (MIT); `dataset_description.json#License` (CC0) | No restricted component exists in this object to isolate. |

### MAY

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| may/001 | M.2 | met | `.gitmodules` | External input linked as a module. |
| may/002 | M.2 | met | `README.md#Layout`; `docs/README.md` | Modular structure documented. |
| may/003 | M.2 | met | `Makefile` (file-keyed rules) | Boundaries independent, matching the README's claim. |
| may/004 | M.2 | met | `.gitmodules`; `Makefile` | Two explicit composition mechanisms. |
| may/005 | M.2 | met | `README.md#Layout`; `docs/README.md` | Documentation/tooling for navigating the modular structure. |

## Flagged items

- **must/002** `[probe-overridden]` — `subdatasets-resolvable` reported `met` from url shape; a network check shows the pinned commit does not exist upstream. Verdict changed to `unmet`.
- **must/016** `[probe-overridden]` — `env-spec-tracked` reported `met` because a non-local remote url was recorded; `git ls-remote` shows it does not resolve. Verdict changed to `unmet`.
- **should/006** `[probe-overridden]` — `ci-present` matched the filename `plotting.sif` appearing in a `test -e` line as "reconstitutes the same environment"; the job never execs the container. Verdict changed from `met` to `partial`.
- **must/014** and **should/008** `[upstream-duplicate]` — the checklist asks the same sentence twice (P.3 MUST and D.2 SHOULD); both answered from the same evidence.

## Not checked

None. Every item above was answered from committed evidence, a cheap network verification, or an equivalent-evidence citation in place of the expensive rerun probe (`should/004`).

## Goals and kind

**Stated goal** (from `README.md`/`docs/README.md`): join the FreeSurfer tables `ds007116` already
ships with per-session ages, and plot brain volume and the GM/WM ratio against age over 8–20 years.

**Kind — labelled assumption, user unavailable to confirm:** `study`. This is a re-derivation from
another dataset's already-computed derivatives (`sourcedata/ds007116/derivatives/freesurfer-post`),
adding a join and a plot and producing no raw or intermediate data of its own — the shape
`project-kinds.md` names explicitly. This **overrides** the root `dataset_description.json`'s own
`"DatasetType": "raw"`, which is itself the headline finding above (`dataset-description-accuracy`).
Under `study`, T (every derived file has a re-executable record) and S (inputs linked, not copied)
carry the most weight, which is reflected in the fix-first ordering; `should/009` is `not-applicable`
because nothing in the object is access-restricted.

## The checklist URL and stamp

Filled checklist: see `2026-10-13-url.txt` (a single-line link; not inlined here per
`response-format.md` — it is ~8.6 kB of base64).

> Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0,
> checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on
> `https://github.com/con/stamped-eval-fixture-r0.git` at commit `776596a15a64c42a52af89ea2d41d0fb0e26864e`,
> 2026-10-13, claude-code (agent SDK)/claude-sonnet-5.
> Probe output: `2026-10-13-probes.json`.
> Machine-readable answers: `2026-10-13-response.json`.

**Scope:** Assessed the committed state at `776596a` (working tree clean). The expensive
`fresh_rerun.py` probe was not run; `should/004` is answered instead from the fresh-runner CI job,
which is equivalent evidence per the conventions. `gh` is unauthenticated and the recorded remote
does not resolve (confirmed above), so Step 5 ("check what the project already knows") found no
reachable issue tracker. No user was available to confirm the goals or kind stated above; both are
recorded as explicit, labelled assumptions.
