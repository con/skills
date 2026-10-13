# STAMPED assessment — `stamped-eval-fixture-r0` (study: brain volume vs age in ds007116)

Object: `/tmp/.../readme-wrong-make-target/object`, commit `070c2502eba13fd4ee78d9cd8e27c1326834a8d2`, working tree clean.
Recorded remote: `https://github.com/con/stamped-eval-fixture-r0.git`.

## 1. Verdict

- **MUST: 14 met / 3 partial / 0 unmet / 0 not-checked** (17)
- **SHOULD: 4 met / 3 partial / 1 unmet / 0 not-checked / 1 not-applicable** (9)
- **MAY: 3 met / 2 partial / 0 unmet / 0 not-checked** (5)

No single overall score, per convention.

## 2. What to fix first

1. **Fix the README's documented command — it does not exist.**
   README's Usage and Reproduce sections both say `make brain-volumes`; the Makefile only has
   `all`, `clean`, `figures/brain-volume-vs-age.png`, `results/volumes.tsv`. Confirmed directly:
   `make -n brain-volumes` → `make: *** No rule to make target 'brain-volumes'.  Stop.`
   A reader who copy-pastes the README's own instructions cannot reproduce anything.
   Closes: **must/007** (partial), and is the direct cause of **should/002** (unmet).
2. **Make CI exercise the documented command, not a different one.**
   `.github/workflows/rerun.yml` runs `make all`, so the real Makefile target has kept working —
   but nothing checks that the string the README tells a human to type is still valid. Pointing
   CI at the README's own command (or vice versa) would have caught finding (1) automatically.
   Closes: **should/002**.
3. **Point CI at the actual execution path, not a bypass of it.**
   Every shipped result was produced via `apptainer exec code/containers/plotting.sif python3 ...`
   (commits `ebe8aa1`, `b230d4f`), but CI only does `pip install -r requirements.lock && make all`
   on the bare runner — the container is never invoked in CI. Closes: **should/004**.
4. **Write down how to invoke the pinned container.**
   README names `code/containers.json` but never shows the `apptainer exec ...` form; that
   command currently lives only inside two DATALAD RUNCMD commit trailers. Closes: **must/017**.
5. **Name an explicit dependency-update process.**
   `requirements.lock` documents its own regeneration command in a comment, but no README/docs
   text says so, and the object's short history (one commit) can't show the process being
   followed. Closes the duplicate pair **must/014** / **should/008**.

## 3. What the project already does well

- Every derived file traces to a `[DATALAD RUNCMD]` run record that names the exact pinned
  container and command (`results/volumes.tsv` ← `ebe8aa1`, `figures/brain-volume-vs-age.png` ←
  `b230d4f`) — a stranger can see exactly what produced each output and with what.
- The input dataset is a real Git submodule with a resolvable public URL
  (`.gitmodules`: `sourcedata/ds007116` → `https://github.com/OpenNeuroDatasets/ds007116.git`),
  not a bare path or a prose mention, and `git submodule status` shows it clean and pinned.
- The environment is fully pinned and tracked in plain Git (`requirements.lock`,
  `code/containers.json` with a `sha256:` digest, no `:latest`), with nothing large enough to
  need git-annex/DataLad — one version-control system end to end.

## 4. Per-item table

### MUST

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| must/001 | S.1 | met | `git ls-files`, `.gitmodules` | Everything resolves under the one root; the input is a submodule of it, not an outside path. |
| must/002 | S.1 | met | `.gitmodules` | `sourcedata/ds007116` URL resolves from elsewhere (probe `subdatasets-resolvable`). |
| must/003 | S.1 | met | `requirements.lock`, `code/containers.json`, commit `ebe8aa1` | Software pinned in environment specs, invoked via apptainer — not assumed present. |
| must/004 | T.1,T.3,T.5 | met | `git ls-files`, `git status --porcelain` | 10 tracked text/code/config files; tree clean (probe `tree-clean`). |
| must/005 | T.1,T.3,T.5 | met | `git ls-tree -r -l HEAD` | No binary blob > 10 MiB; no large-content mechanism needed (probe `large-in-annex`). |
| must/006 | T.1,T.3,T.5 | met | commits `ebe8aa1`, `b230d4f` | Both derived files trace to a run record naming the container (probes `derived-have-records`, `run-env-linked`). |
| **must/007** | A.1 | **partial** (overridden) | `README.md#L19`, `README.md#L29`, `Makefile`, `make -n brain-volumes` output | README's Usage/Reproduce sections tell the reader to run `make brain-volumes`, which is not a Makefile target; confirmed it fails. Probe `entry-point` said `met` from presence of an install/usage section alone, without checking the command against the target list. |
| must/008 | A.1 | met | `Makefile`, `code/collect_volumes.py`, `code/plot_volumes.py` | The Makefile itself (`all` target, per-file rules) is a clear, working starting point independent of the README's wrong prose (probe `entry-point`). |
| must/009 | P.1 | met | probe `no-abs-paths` | 0 hits scanning 14 tracked paths for host-specific absolute paths. |
| must/010 | P.1 | met | `requirements.lock` | All deps pinned; no script expects a pre-installed tool (probe `env-spec-tracked`). |
| must/011 | P.1 | met | `code/collect_volumes.py`, `code/plot_volumes.py`, `README.md#L10-12` | Scripts use only stdlib; the one real host assumption (python3) is named in README. |
| must/012 | P.2 | met | `README.md#L8-12` | Install section names python3 + the exact lockfile to install from. |
| must/013 | P.3 | met | `requirements.lock` | Tracked in version control (probe `env-spec-tracked`). |
| **must/014** | P.3 | **partial** | `requirements.lock#L1`, `git log -- requirements.lock requirements.in` | A regen command is documented in a lockfile comment, but no README/docs text states a process, and only one commit ever touched the spec — can't show it being followed. **Duplicate of should/008** (same sentence, principles-card.md). |
| must/015 | D.1 | met | commits `ebe8aa1`, `b230d4f` | Run records reference a pinned digest, never `:latest` (probe `run-env-linked`). |
| must/016 | D.1 | met | `requirements.lock`, published remote | Spec travels with the published object (probe `env-spec-tracked`). |
| **must/017** | D.1 | **partial** | `README.md#L14`, commit `ebe8aa1`, `docs/README.md` | README says the container exists and is pinned, but never shows how to invoke it; the real command is only in commit trailers. |

### SHOULD

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| should/001 | T.2 | met | `git ls-files`, `.gitmodules` | One VCS (plain Git) across every component; nothing needed git-annex/DataLad. |
| **should/002** | A.2 | **unmet** (overridden) | `.github/workflows/rerun.yml#L10`, `README.md#L19` | CI runs `make all`, never the README's documented `make brain-volumes`; nothing tests that the published instructions remain accurate, and they don't. Probe `ci-present` said `met` from "CI re-executes the workflow", a different property than "the documented instructions are tested". |
| should/003 | M.1 | met | sourcedata/, code/, results+figures/, requirements.lock+containers.json | 4 kinds of component in 4 distinct places (probe `modules-separated`). |
| should/004 | E.1 | partial | `.github/workflows/rerun.yml`, commit `ebe8aa1` | CI's VM is fresh, but it never runs the apptainer container that actually produced the shipped results — tested path ≠ production path. |
| should/005 | E.1 | met | commits `ebe8aa1`, `b230d4f` | Each step is its own `apptainer exec` invocation, no persistent container. |
| should/006 | D.2 | met | `.github/workflows/rerun.yml` | CI re-installs/rebuilds the environment each run (probe `ci-present`). |
| should/007 | D.2 | partial | `code/containers.json`, `git ls-files` | `requirements.lock` is archived; the container image itself is only referenced by digest, never stored in the object. |
| **should/008** | D.2 | **partial** | `requirements.lock#L1`, `git log -- requirements.lock requirements.in` | Same sentence and evidence as must/014 — answered identically; noted as a duplicate. |
| should/009 | M.4 | **not-applicable** | `sourcedata/ds007116/dataset_description.json` (`"License": "CC0"`) | N/A: empty subject — nothing in the object is restricted, so there is no restricted component to isolate. |

### MAY

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| may/001 | M.2 | met | `.gitmodules` | External dataset linked as a submodule (probe `subdatasets-resolvable`). |
| may/002 | M.2 | partial | `docs/README.md`, `README.md` | The layout is real (probe `modules-separated`) but nowhere narrated; a reader infers it from directory names and the Makefile DAG. |
| may/003 | M.2 | met | `.gitmodules`, `Makefile` | Submodule and per-target rules let inputs/code/env update independently. |
| may/004 | M.2 | met | `.gitmodules`, `Makefile` | Two explicit composition mechanisms: git submodules and Makefile dependency rules. |
| may/005 | M.2 | partial | `docs/README.md#L1`, `README.md#L1-6` | `docs/README.md` — the file meant for exactly this — is one placeholder line; no module map or navigation aid exists. |

## 5. Flagged items

- **must/007** — `probe-overridden`. Probe `entry-point` reported `met` from "README.md has an install/usage/reproduce section"; a direct check (`make -n brain-volumes`) shows the documented command in that section does not exist as a target. Verdict changed to `partial`.
- **should/002** — `probe-overridden`. Probe `ci-present` reported `met` from "CI re-executes the workflow"; that is a different property than "the documented instructions are tested for accuracy" — CI exercises `make all`, never the README's `make brain-volumes`. Verdict changed to `unmet`.

No `mapping-questioned`-only flags (where I'd have kept the probe's verdict but named a different route) and no `unverified-claim` flags: every judgement item above was checked directly against the object (code read, `git log`, or a literal `make -n` run) rather than left as an unconfirmed assertion.

## 6. Not checked

None. All 31 items received a `met` / `partial` / `unmet` / `not-applicable` status; `should/004`
was answered from the committed CI configuration as equivalent evidence (per
`stamped-conventions` invariant 3) rather than being left `not-checked`, and the expensive
`fresh_rerun.py` probe was not run (no user available to consent to the cost, per the operating
constraints of this run) — it would have gone toward strengthening should/004 further but was not
needed to answer it.

## 7. Goals and kind

**ASSUMPTION (kind, labelled because no user was available to confirm):** this object's kind is
**study** (primary) — README states the goal plainly: "reads the FreeSurfer tables ds007116
ships, joins them with the per-session ages, and plots brain volume ... against age." It has a
secondary **component** aspect: `code/collect_volumes.py` and `code/plot_volumes.py` are each
independently invocable scripts that could serve another study, but neither is documented or
versioned as a reusable tool on its own, so it does not change the primary kind. Per
`project-kinds.md`, "study" emphasizes all seven principles with T and S carrying the most
weight — consistent with the fix-first ordering above (README/CI accuracy under A and T).

## 8. Checklist URL, stamp, and response

Checklist URL (persistence format 3, generated only by `encode_response.py`): see
`checklist-url.txt` alongside this report (9189 characters — too long to inline safely).

> Produced by `assess-alignment-with-stamped-principles` 0.2.0 with `stamped-conventions` 0.2.0,
> checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259bad237fa57b856417db8dba45a1b283a527`),
> on `https://github.com/con/stamped-eval-fixture-r0.git` at commit `070c2502eba13fd4ee78d9cd8e27c1326834a8d2`,
> 2026-10-13, claude-code/claude-sonnet-5.
> Probe output: `2026-10-13-probes.json`. Full response: `2026-10-13-response.json`.

Extra items (no checklist id): `clone-weight` met (no text blob > 10 MiB), `inputs-untouched` met
(submodule clean and pinned), `license-declared` met (`LICENSE`, MIT; the ds007116 stand-in also
declares `License: CC0` in its BIDS metadata).
