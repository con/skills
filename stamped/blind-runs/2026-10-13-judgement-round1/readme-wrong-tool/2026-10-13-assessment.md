# STAMPED assessment — brain-volume-vs-age study (object at `f077c15`)

**Assumption (unconfirmed — no user attached to this run):** goals and kind were read from the
object's own documentation, not confirmed interactively.
- **Goals:** answer whether brain volume grows with age (8–20y) and whether the GM/WM ratio falls
  over the same range, from `README.md` and `docs/README.md`.
- **Kind:** **study** (primary), with a reusable-component secondary flavour on the input module
  boundary — matches `project-kinds.md`'s "study" row (all seven principles weighted, T and S
  weighted most).

## Verdict line

- **MUST:** 11 met / 4 partial / 2 unmet / 0 not-checked (of 17)
- **SHOULD:** 3 met / 5 partial / 0 unmet / 1 not-applicable (of 9)
- **MAY:** 5 met / 0 partial / 0 unmet / 0 not-applicable (of 5)

No single overall score, per convention.

## What to fix first

1. **Make the README tell one story about how to set up and run this.** `README.md`'s
   Install/Usage sections say `pixi install` / `pixi run all`; its own Reproduce section three
   paragraphs later says `git clone ... && make all`. No `pixi.toml` exists anywhere in the tree —
   the first route a reader meets is dead on arrival. Closes **must/007, must/008, must/017,
   should/002** in one edit: delete the pixi lines (they were only ever in one commit,
   `f077c15`, which overwrote the original, working `python3 -m venv .venv && pip install -r
   requirements.lock` / `make all` text) or actually adopt pixi and retire `requirements.lock` +
   the venv instructions + the CI step that installs it.
2. **Point CI at the environment the run records actually name, or stop claiming it does.**
   `.github/workflows/rerun.yml` carries a comment saying CI "has to exercise *that* environment,
   not merely some environment," but it only checks the container digest value and that the
   placeholder `.sif` file exists, then runs `make all` with bare `python3` — it never runs
   `apptainer exec code/containers/plotting.sif ...`. Closes **should/005, should/006**.
3. **Exercise the environment-update process once.** `requirements.lock`'s own header names its
   regeneration command (`uv pip compile code/requirements.in`), but no commit in the object's
   history ever re-runs it. A single dependency bump committed through that command would close
   **must/014 and should/008** (the same sentence, twice) outright.
4. **Fix the two items a stranger's clone cannot avoid hitting**, `must/002` and `must/016` — see
   "Not checked" below; these are this fixture's two deliberately simulated gaps
   (`FIXTURE.md`), not fixable by editing the object, so they are listed here for completeness
   rather than as real action items on a real object.
5. **Archive the container image, not just its digest**, or explain in `code/containers.json`
   why a digest-pinned public base image is an acceptable substitute. Closes **should/007**.

## What the project already does well

- **Clean S/M separation.** Four kinds of component live in four distinct places —
  `sourcedata/` (input), `code/`+`Makefile` (code), `results/`+`figures/` (derived),
  `code/containers.json`+`requirements.lock` (environment) — and `docs/README.md` spells out why
  each can be swapped independently (`must/001`, `should/003`, `may/002`–`005`).
- **Every derived file has a real run record.** `git log --grep='\[DATALAD RUNCMD\]'` shows both
  `results/volumes.tsv` (`0edcc7e`) and `figures/brain-volume-vs-age.png` (`55e35e5`) tracing to a
  re-executable, container-naming command (`must/006`, `must/015`).
- **No platform or path lock-in anywhere in tracked text** — `no-abs-paths` and
  `platform-assumptions` both scanned 17 tracked paths and found zero hits (`must/009`,
  `must/011`, `must/012`).

## Per-item table

### MUST

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| must/001 | S.1 | met | `git ls-files`; `.gitmodules` | Everything tracked sits under the repo root. |
| must/002 | S.1 | **unmet** | `git fetch --depth=1 <url> <pinned commit>` → "not our ref" | Pinned submodule commit doesn't exist upstream (fixture-simulated; see FIXTURE.md). |
| must/003 | S.1 | met | `requirements.lock`; `code/containers.json` | External software is pinned in the env spec or linked by digest, not assumed present. |
| must/004 | T.1/T.3/T.5 | met | `git status --porcelain` (empty) | Tree clean, 11 tracked text/code/config paths. |
| must/005 | T.1/T.3/T.5 | met | `git ls-tree -r -l HEAD` | No blob over 10 MiB; no large-content mechanism needed. |
| must/006 | T.1/T.3/T.5 | met | commits `0edcc7e`, `55e35e5` | Both derived files trace to a run record naming the environment. |
| must/007 | A.1 | **partial** | `README.md` Install/Usage vs Reproduce; no `pixi.toml` anywhere | Two disagreeing accounts of install/usage in the same README (rule 10). |
| must/008 | A.1 | **partial** | `README.md`; `Makefile` | Entry point itself is unambiguous, but the documented route to it disagrees with itself. |
| must/009 | P.1 | met | `no-abs-paths` probe, 0 hits | No host-specific absolute paths in tracked text. |
| must/010 | P.1 | met | `requirements.lock` | Dependencies pinned; no script expects a pre-installed tool. |
| must/011 | P.1 | met | `platform-assumptions` probe, 0 hits | No undocumented platform-specific commands found. |
| must/012 | P.2 | met | `platform-assumptions` probe, 0 hits | Same evidence as must/011. |
| must/013 | P.3 | met | `requirements.lock` tracked in git | Env spec is version-controlled alongside code. |
| must/014 | P.3 | **partial** | `requirements.lock` header; `git log` | Regeneration command declared, never exercised in history. |
| must/015 | D.1 | met | commits `0edcc7e`, `55e35e5` | Run records reference a pinned image/lockfile; no `:latest`. |
| must/016 | D.1 | **unmet** | `git ls-remote <remote.origin.url>` fails | `remote.origin.url` names an unpublished repo (fixture-simulated; see FIXTURE.md). |
| must/017 | D.1 | **partial** | `README.md`; `.github/workflows/rerun.yml` | Same README self-contradiction as must/007/008. |

### SHOULD

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| should/001 | T.2 | met | `git -C sourcedata/ds007116 log` | Plain Git used throughout; no annex/DataLad split. |
| should/002 | A.2 | **partial** | `.github/workflows/rerun.yml` | CI tests only the Makefile route; the README's pixi route is untested and broken. |
| should/003 | M.1 | met | `modules-separated` probe | 4 kinds of component in 4 distinct places. |
| should/004 | E.1 | met | `.github/workflows/rerun.yml` `runs-on: ubuntu-latest` | Pipeline runs on a fresh GitHub-hosted VM each time. |
| should/005 | E.1 | **partial** | commits `0edcc7e`/`55e35e5` vs `Makefile` | Run records used a fresh container per step; the current Makefile/CI route does not. |
| should/006 | D.2 | **partial** | `.github/workflows/rerun.yml` vs run records | CI's comment claims to reconstitute the recorded environment; its steps never invoke it. |
| should/007 | D.2 | **partial** | `code/containers/plotting.sif.README` | Digest pinned, but the real image is explicitly not archived (documented placeholder). |
| should/008 | D.2 | **partial** | `requirements.lock` header; `git log` | Same sentence as must/014, same evidence. |
| should/009 | M.4 | N/A | `sourcedata/ds007116/dataset_description.json` (CC0); `LICENSE` (MIT) | No restricted component exists in this object. |

### MAY

| id | principle | status | evidence | reason |
|---|---|---|---|---|
| may/001 | M.2 | met | `.gitmodules` | External input is linked as a submodule. |
| may/002 | M.2 | met | `docs/README.md`; `README.md` Layout table | Modular structure is documented. |
| may/003 | M.2 | met | `README.md`; `Makefile` | Boundaries are independently updatable by construction (file-keyed targets). |
| may/004 | M.2 | met | `.gitmodules`; `Makefile`; `code/containers.json` | Submodule + Makefile + container registration are explicit composition mechanisms. |
| may/005 | M.2 | met | `docs/README.md` | Written specifically to help a reader navigate the module layout. |

### Extras (no checklist id)

| key | status | reason |
|---|---|---|
| license-declared | met | `LICENSE` (MIT) present. |
| clone-weight | met | No tracked text blob exceeds 10 MiB. |
| inputs-untouched | met | Linked module is clean and at the recorded commit. |

## Flagged items

| id | flags | what the probe measured vs. what was overridden |
|---|---|---|
| must/002 | `probe-overridden` | `subdatasets-resolvable` checked URL *shape* only; `git fetch` of the pinned commit against the real upstream shows it does not exist there. |
| must/007 | `probe-overridden` | `entry-point` checked only that an install/usage *section* exists, not that its contents agree with the rest of the README. |
| must/008 | `probe-overridden` | Same probe, same gap — judged on the documented route per verdicts.md rule 10. |
| must/014 | `upstream-duplicate` | Paired with should/008 — same sentence, same evidence. |
| must/016 | `probe-overridden` | `env-spec-tracked` treated `remote.origin.url` as proof of publication without checking reachability; `git ls-remote` shows it is not publicly resolvable. |
| must/017 | — | Pure judgement item; no probe exists for it. |
| should/002 | `probe-overridden` | `ci-present` credited "the workflow" broadly; CI only exercises one of the README's two disagreeing routes. |
| should/005 | — | Pure judgement item; the two accounts (run records vs. current Makefile/CI) disagree on container-per-step isolation. |
| should/006 | `mapping-questioned`, `probe-overridden` | `ci-present` read its own in-file comment as evidence; the comment's claim is not what the steps actually do. |
| should/008 | `upstream-duplicate` | Paired with must/014. |

## Not checked

None. All 31 items received a status other than `not-checked` (13 from probes directly, 2 from
probe-overridden judgement, the remaining 16 from reading the object). The two `unmet` items
(must/002, must/016) are not `not-checked`: both have direct evidence of absence (a failed `git
fetch`/`git ls-remote` against the real, named remote), which is exactly what `FIXTURE.md` says
to expect of this fixture.

## Goals and kind

See the labelled assumption at the top. No secondary kind beyond the study itself; the input
module (`sourcedata/ds007116`) is treated as someone else's component, linked rather than owned.

## Checklist URL and provenance stamp

Filled checklist: [`2026-10-13-url.txt`](2026-10-13-url.txt)
Full per-item evidence: [`2026-10-13-response.json`](2026-10-13-response.json)
Raw probe output: [`2026-10-13-probes.json`](2026-10-13-probes.json)

> Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0,
> checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on
> `https://github.com/con/stamped-eval-fixture-r0.git` (per `remote.origin.url` — see must/016
> finding above on whether that URL is actually reachable) at commit `f077c1507fb9960951c2f35d70828b095194ec62`,
> 2026-10-13, claude-code (agent)/claude-sonnet-5.
> Probe output: `2026-10-13-probes.json`.
