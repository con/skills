# STAMPED assessment — `jcal2/clean` (R0: brain volume vs. age in ds007116)

## 1. Verdict

- **MUST: 15 met / 1 partial / 1 unmet / 0 not-checked** (17)
- **SHOULD: 6 met / 2 partial / 0 unmet / 0 not-checked / 1 not-applicable** (9)
- **MAY: 3 met / 2 partial / 0 unmet / 0 not-checked** (5)

No single overall score. Every one of the 31 pinned items has an answer; none were left `not-checked` (the probe sweep answered 15, judgement answered the other 16 — see §8 for why this is more than the "11 MUST / 2 SHOULD / may/001" the skill's Step 3 predicts).

## 2. What to fix first

1. **Re-pin or re-fetch `sourcedata/ds007116`.** `.gitmodules` records commit `2c445a415fde6879493df8a9822a6bb3701278f7` at `https://github.com/OpenNeuroDatasets/ds007116.git`. That commit does not exist in the real repository: `git fetch origin 2c445a41...` returns `remote error: upload-pack: not our ref`, and the GitHub API 404s the same SHA. A fresh `git clone` + `git submodule update --init sourcedata/ds007116` — exactly the command the project's own README tells a reader to run — fails. Closes **must/002**.
2. **Once (1) is fixed, confirm the CI actually passes.** `.github/workflows/rerun.yml` checks out `submodules: recursive` and then runs `make all`; today that checkout step depends on the same unresolvable commit, so the workflow cannot reach `make` at all. Closes **should/004** for real, rather than by citing a workflow file that would currently fail on its first step.
3. **Point `remote.origin.url` at wherever this object is actually published**, or publish it there. The tracked checkout's remote (`https://github.com/con/stamped-eval-fixture-r0.git`) 404s on the GitHub API, so there is currently no demonstrated place a stranger could clone this object — and with it, the environment specification — from. Closes **must/016**.
4. **Archive the real `plotting.sif`, or replace the placeholder with a fetchable release asset.** `code/containers/plotting.sif.README` is candid that the ~200 MB image "is not shipped" and the file beside it is a byte-sized stand-in. The digest pin (must/015) is real; the archived artifact (should/007) is not, in this checkout. Closes **should/007**.
5. **Add a short "Project layout" paragraph** (to `README.md` or to the currently one-line `docs/README.md`) naming `sourcedata/` (input), `code/` (code + environment spec), `results/`+`figures/` (derived) and how they recombine. The Makefile's dependency graph already encodes this; it just isn't said in prose anywhere. Closes **may/002** and **may/005**.

## 3. What the project already does well

- **Nothing is dirty.** `git status --porcelain` is empty, including submodules; 10 of 16 tracked paths are the plain text/code/config that must/004 asks about (`git ls-files`, `git status --porcelain` at commit `9c80df0`).
- **Every derived file has a real, checkable run record.** `results/volumes.tsv` was last touched by commit `312a526`, `figures/brain-volume-vs-age.png` by `9c80df0` — both are `[DATALAD RUNCMD]` commits, and both record `apptainer exec code/containers/plotting.sif ...` with the image pinned by digest, independently confirmed with `git log --format=%H -1 -- <path>` rather than taking the probe's word for it (must/006, must/015).
- **One clear entry point.** `README.md` has Install/Usage/Reproduce sections, `Makefile`'s `all` target is exactly what the README documents, and nothing in any tracked script assumes a host-specific absolute path (must/007, must/008, must/009).

## 4. Per-item table

MUST first, then SHOULD, then MAY.

| id | principle(s) | status | evidence | reason |
|---|---|---|---|---|
| must/001 | S.1 | met | `git ls-files`; `.gitmodules` | All 16 tracked paths sit under one root; the one external link (`sourcedata/ds007116`) is reachable via `.gitmodules` nested under that same root, not only named in prose. |
| must/002 | S.1 | **unmet** | `.gitmodules`; `git fetch origin 2c445a41...` | `sourcedata/ds007116` pins commit `2c445a41...`, absent upstream: `git fetch origin 2c445a41...` → `'not our ref 2c445a41...'`; GitHub API 404s the same SHA. A fresh `git submodule update --init` would fail. |
| must/003 | S.1 | met | `requirements.lock`; `code/containers.json` | Python deps pinned in `requirements.lock`; the container is pinned by digest in `code/containers.json` with its artifact path under `code/containers/`, all tracked inside the root; nothing external is assumed pre-installed. |
| must/004 | T.1,T.3,T.5 | met | `git ls-files`; `git status --porcelain` | `git` tracks 10 text/code/config file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | T.1,T.3,T.5 | met | `git ls-tree -r -l HEAD` | No binary blob over 10 MiB in git, and no large-content mechanism is needed: nothing in this object is large binary data. |
| must/006 | T.1,T.3,T.5 | met | `figures/brain-volume-vs-age.png`; `results/volumes.tsv` | All 2 derived file(s) trace to a re-executable record (2 run record(s), workflow: `Makefile`). Independently confirmed via `git log -1 --format=%H -- <path>`. |
| must/007 | A.1 | met | `README.md`; `Makefile` | `README.md` has an install/usage/reproduce section. |
| must/008 | A.1 | met | `README.md`; `Makefile` | Starting point present: `code/collect_volumes.py`, named by `Makefile`'s `all` target. |
| must/009 | P.1 | met | probe `no-abs-paths` | No host-specific absolute paths in any tracked text file (16 scanned). |
| must/010 | P.1 | met | `requirements.lock` | Dependencies are pinned in `requirements.lock`; no tracked script expects a tool to already be on the host. |
| must/011 | P.1 | met | `README.md`; `.github/workflows/rerun.yml` | No host assumption beyond a POSIX shell + `python3` on PATH, stated in README's Install section; CI pins its own OS (`ubuntu-latest`). Nothing undocumented remains. |
| must/012 | P.2 | met | `README.md`; `code/containers.json` | README's Install section lists `python3` + `pip install -r requirements.lock`; `code/containers.json` names the pinned container used for the analysis step. |
| must/013 | P.3 | met | `requirements.lock` | Tracked: `requirements.lock`. |
| must/014 | P.3 | met | `requirements.lock`; `code/requirements.in` | `requirements.lock`'s header names the regeneration command (`uv pip compile code/requirements.in`); both source and lock are tracked, so a future update is version-controlled. *(duplicate of should/008 — see §5)* |
| must/015 | D.1 | met | `commit:9c80df0`; `commit:312a526` | Both run records reference a pinned image by digest; no `:latest` reference is tracked. |
| must/016 | D.1 | **partial** | `requirements.lock`; GitHub API check | `requirements.lock`/`containers.json` are tracked and meant to travel with the object, but this checkout's `remote.origin.url` (`github.com/con/stamped-eval-fixture-r0`) 404s: no demonstrated place to fetch the spec from. |
| must/017 | D.1 | met | `README.md`; `code/containers/plotting.sif.README` | README's Install section documents obtaining the pinned packages and the container; `plotting.sif.README` documents the pinned image artifact. |
| should/001 | T.2 | met | `git ls-files` | Every component is tracked under one Git history; no second VCS (DVC, `git-annex`, LFS) is mixed in here. |
| should/002 | A.2 | met | `.github/workflows/rerun.yml` | CI re-executes the workflow on every push/PR. |
| should/003 | M.1 | met | `sourcedata/`, `code/`, `figures/`+`results/`, lockfile/`containers.json` | 4 kinds of component live in distinct places: inputs, code, derived, environment. |
| should/004 | E.1 | **partial** | `.github/workflows/rerun.yml` | CI re-executes `make all` on a fresh runner — the right mechanism — but its `submodules: recursive` checkout depends on the same unresolvable commit as must/002, so it would fail before `make` runs. |
| should/005 | E.1 | met | `commit:312a526`; `commit:9c80df0` | Both run records invoke `apptainer exec code/containers/plotting.sif ...`: each step runs in its own container invocation. |
| should/006 | D.2 | met | `.github/workflows/rerun.yml` | Same CI job re-exercises the pinned environment on every run. |
| should/007 | D.2 | **partial** | `code/containers/plotting.sif.README`; `code/containers/plotting.sif` | The README beside it discloses that the ~200 MB image isn't shipped; the file itself is a byte-sized placeholder. Path and digest pin exist; the real artifact doesn't. |
| should/008 | D.2 | met | `requirements.lock`; `code/requirements.in` | Same evidence as must/014 — tracked process + tracked files. *(duplicate — see §5)* |
| should/009 | M.4 | N/A | — | N/A: no restricted data or software exists in this object — ds007116 is a public OpenNeuro dataset and everything else is ordinary public code/docs/config. |
| may/001 | M.2 | met | `.gitmodules` | 1 external component is linked as a module: `sourcedata/ds007116`. |
| may/002 | M.2 | **partial** | `Makefile`; `docs/README.md` | The Makefile's rule graph and README's Reproduce section imply how input/code/results relate, but nothing states the modular layout or recombination explicitly; `docs/README.md` is a one-line stub. |
| may/003 | M.2 | met | `.gitmodules`; `requirements.lock` | Input (submodule pin), environment (lockfile/digest) and code are each swappable through their own narrow interface without the others needing to change. |
| may/004 | M.2 | met | `.gitmodules`; `Makefile` | `.gitmodules` links the input module; `Makefile`'s rules compose code, input and output: both are explicit, tracked composition mechanisms. |
| may/005 | M.2 | **partial** | `docs/README.md` | A reader can infer the layout from Makefile/README, but no dedicated documentation or tool helps navigate it; `docs/README.md` says only "Notes on the method live here." |

## 5. Flagged items

- **must/002** `probe-overridden` — `subdatasets-resolvable` checks only that the recorded URL is a well-formed, reachable *kind* of remote; it does not check whether the recorded *commit* resolves there. It doesn't on the real remote. Verdict changed `met` → `unmet`.
- **must/016** `probe-overridden` — `env-spec-tracked` calls a tracked spec `met` whenever `remote.origin.url` is set and isn't an obviously local path; it does not check whether that URL is actually live. It isn't (404). Verdict changed `met` → `partial`.
- **must/014**, **should/008** `upstream-duplicate` — these are the same checklist sentence twice (noted in the conventions as known drift); answered once, from the same evidence, deliberately.
- **should/004** `unverified-claim` — the `partial` rests on an inference (CI's checkout shares the exact commit must/002 shows is unfetchable) rather than an observed CI failure; the object's own CI history could not be inspected (its recorded remote 404s, and `gh` is unauthenticated in this session).

## 6. Not checked

None. Every item the probes left open was answered by judgement in §4; the expensive `fresh_rerun.py` probe was not run (no user available to consent to the cost in this session), but `should/004` was not defaulted to `not-checked` for that reason — the tracked CI workflow is equivalent evidence per the conventions' invariant 3, and was answered (as `partial`) from it.

## 7. Goals and kind

**Stated/inferred goal:** a minimal, fully-recorded study — join FreeSurfer volume tables shipped by OpenNeuro dataset `ds007116` with per-session ages, and plot brain volume (with GM/WM ratio) against age (`README.md`, first paragraph).

**Kind — ASSUMPTION (no user available to confirm):** primary kind **study** (data + compute answering a question, per `project-kinds.md`), with a secondary **component**-like entry point (`code/collect_volumes.py`, `code/plot_volumes.py` could be reused standalone). I did not ask the user because none is available in this run; this is recorded as `object.kind: "study"` in the response JSON, as the skill directs when the user is absent. Under this kind, T and S carry the most weight (per `project-kinds.md`), which is exactly where this assessment's one real finding (must/002, a broken S/T.5 link) lands.

## 8. The checklist URL, the stamp, and the response JSON

**Checklist-app URL** (generated only by `encode_response.py`, not hand-built):

```
https://checklist.stamped-principles.org/?checklist=0.3.1&responses_version=0.3.1&cols=auto&sections=off&format=3&responses=<base64 — see 2026-10-13-response.json>
```

(The full URL is long; it is reproduced in full in the terminal output of `encode_response.py encode 2026-10-13-response.json`, and can be regenerated from the response JSON at any time — it is not stored separately to avoid drift.)

> Produced by `assess-alignment-with-stamped-principles` 0.2.0 with `stamped-conventions` 0.2.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on the local checkout at `/tmp/.../scratchpad/jcal2/clean` at commit `9c80df0aed8d3a69471ef299453b963c09396e27`, 2026-10-13, claude-code (agent SDK)/claude-sonnet-5.
> Probe output: `2026-10-13-probes.json`. Full per-item answers: `2026-10-13-response.json`.

**fresh_rerun.json:** not produced — the expensive rerun probe needs another host, real time and user consent to the cost; none of those were available in this session.
