# STAMPED assessment — stamped-eval-fixture-r0 (object at commit `9c85091`)

## Verdict

- **MUST: 12 met / 3 partial / 2 unmet / 0 not-checked** (17) — a MUST `partial` counts as a MUST failure, so **5/17 MUST fail**.
- **SHOULD: 5 met / 3 partial / 0 unmet / 0 not-checked / 1 not-applicable** (9)
- **MAY: 5 met / 0 partial / 0 unmet** (5)

No single overall score.

## What to fix first

1. **Fix the order of README.md's "Reproduce" section** → a reader following it literally cannot reproduce the result: it runs `make all` before cloning, plots before the table it reads exists, and initializes the submodule last. The separate "Usage" section's `make all` already works — the fix is to either delete "Reproduce" or make it match "Usage" → closes **must/008**, contributes to **should/002**.
2. **Make CI exercise the README's own instructions, not just the Makefile** → `.github/workflows/rerun.yml` runs `make all` directly, so it never would have caught the reorder above; nothing currently tests the prose a reader actually follows → closes **should/002**.
3. **Publish the remote `origin` names, or stop naming one** → `remote.origin.url` points at `github.com/con/stamped-eval-fixture-r0`, which returns 404; no one but this machine can retrieve the tracked specification → closes **must/016**.
4. **Re-pin `sourcedata/ds007116` to a commit that exists upstream** → the recorded commit is not a ref in the real `OpenNeuroDatasets/ds007116`, so `git submodule update --init` fails from a fresh clone of the published remote → closes **must/002**.
5. **Either document the `apptainer exec` route or make the Makefile use it** → every run record says the analysis ran inside `code/containers/plotting.sif`; the tracked `Makefile` calls bare `python3` and no doc shows the container invocation, so a reader reproducing via the documented route does not use the pinned environment the results actually came from → closes **must/017**, contributes to **should/006**.

## What the project already does well

- A content-addressed, single-VCS layout with a real re-executable provenance trail: both derived files carry `[DATALAD RUNCMD]` records naming inputs, outputs, and the exact container digest (`git log --grep='\[DATALAD RUNCMD\]'`, commits `0edcc7e`, `55e35e5`).
- The environment is pinned and archived, not merely referenced: `requirements.lock` pins exact versions, `code/containers.json` pins the container by digest (not `:latest`), and the image itself is tracked at `code/containers/plotting.sif`.
- Modularity is both real and documented: `README.md`'s Layout table and `docs/README.md`'s walk-through agree, and the `Makefile`'s file-keyed targets back up the claim that any one part can be swapped without touching the others.

## Per-item table

### MUST

| id | principle | status | source | reason |
|---|---|---|---|---|
| must/001 | S.1 | met | judgement | All tracked content sits under the repo root; nothing is referenced only on a share or cluster path (`README.md` Layout table, `git ls-files`). |
| must/002 | S.1 | **unmet** | probe:subdatasets-resolvable+judgement | Pinned commit `8457025…9ed` is not a ref in the real upstream (`git fetch --depth=1 … 8457025…` → "not our ref"); a fresh clone cannot resolve `sourcedata/ds007116`. |
| must/003 | S.1 | met | judgement | External software lives in the environment spec (`requirements.lock`, digest-pinned `code/containers.json`, tracked `code/containers/plotting.sif`), not assumed present. |
| must/004 | T.1,T.3,T.5 | met | probe:tree-clean | `git status` is empty including submodules; 11 tracked files, all committed. |
| must/005 | T.1,T.3,T.5 | met | probe:large-in-annex | No binary blob over 10 MiB in git. |
| must/006 | T.1,T.3,T.5 | met | probe:derived-have-records | Both derived files trace to a DATALAD RUNCMD record naming the container. |
| must/007 | A.1 | met | probe:entry-point | `README.md` has correct Install and Usage sections. |
| must/008 | A.1 | **partial** | probe:entry-point+judgement | `README.md`'s "Reproduce" section (L41–47) is out of order (make all → clone → plot → collect → submodule init); unusable as written, though "Usage" (L16–22) works. |
| must/009 | P.1 | met | probe:no-abs-paths | No host-specific absolute paths in tracked text files. |
| must/010 | P.1 | met | probe:env-spec-tracked | All deps pinned in `requirements.lock`; nothing expects a pre-installed tool. |
| must/011 | P.1 | met | probe:platform-assumptions | No undocumented platform-specific command found; nothing ties the object to one host. |
| must/012 | P.2 | met | probe:platform-assumptions | Same evidence as must/011. |
| must/013 | P.3 | met | probe:env-spec-tracked | `requirements.lock` tracked in version control. |
| must/014 | P.3 | **partial** | judgement | Regen process is declared (`requirements.lock` header: `uv pip compile code/requirements.in`), but history shows one commit ever (`2c06800`) — no instance of it running since. |
| must/015 | D.1 | met | probe:run-env-linked | Run records reference a pinned digest; nothing tracked uses `:latest`. |
| must/016 | D.1 | **unmet** | probe:env-spec-tracked+judgement | `remote.origin.url` (`github.com/con/stamped-eval-fixture-r0`) 404s on the GitHub API and cannot be fetched; not retrievable by anyone else. |
| must/017 | D.1 | **partial** | judgement | Install documents the pip env, not the container: run records show `apptainer exec plotting.sif …`, but the Makefile calls bare `python3` and no doc gives that invocation. |

### SHOULD

| id | principle | status | source | reason |
|---|---|---|---|---|
| should/001 | T.2 | met | judgement | One VCS (git) across code, docs, results and the input module (itself a git repo via submodule). |
| should/002 | A.2 | **partial** | probe:ci-present+judgement | CI re-executes `make all` (accurate) but never runs the literal commands under README's "Reproduce" heading — the section that is currently wrong. |
| should/003 | M.1 | met | probe:modules-separated | Inputs, code, derived products and environment live in 4 distinct places. |
| should/004 | E.1 | met | judgement | Tested on a fresh cloud instance: GitHub Actions `ubuntu-latest`, a new VM per run. |
| should/005 | E.1 | met | judgement | Both run records wrap their command in `apptainer exec code/containers/plotting.sif …` — a disposable container invocation per execution. |
| should/006 | D.2 | **partial** | probe:ci-present+judgement | CI checks the digest and the placeholder `.sif`'s presence, then runs `make all` with no `apptainer exec` — the named environment is checked for, never reconstituted. |
| should/007 | D.2 | met | judgement | `code/containers/plotting.sif` is tracked at the path every run record names (the object's own `.sif.README` flags it as a reduced fixture stand-in). |
| should/008 | D.2 | **partial** | judgement | Same sentence, same evidence as must/014 — declared, never exercised in history. |
| should/009 | M.4 | not-applicable | judgement | N/A: no restricted data or software in this object — `sourcedata/ds007116` is CC0. |

### MAY

| id | principle | status | source | reason |
|---|---|---|---|---|
| may/001 | M.2 | met | probe:subdatasets-resolvable | `sourcedata/ds007116` linked as a module. |
| may/002 | M.2 | met | judgement | Modular structure documented in both `README.md`'s Layout table and `docs/README.md`'s walk-through. |
| may/003 | M.2 | met | judgement | `Makefile` targets are file-keyed, matching README's claim that parts can be swapped independently. |
| may/004 | M.2 | met | judgement | Composition mechanism explicit: git submodule for input, `Makefile` for chaining steps, digest for environment. |
| may/005 | M.2 | met | judgement | `docs/README.md` exists specifically to help navigate the modular structure. |

## Flagged items

- **must/002** `probe-overridden` — `subdatasets-resolvable` reported "met" from URL shape alone; `git fetch` against the real upstream showed the pinned commit does not exist there.
- **must/008** `probe-overridden` — `entry-point` reported "met" from section presence alone; reading the "Reproduce" section's actual command order shows it is broken.
- **must/014** `upstream-duplicate` — same sentence as should/008; answered once, repeated by design.
- **must/016** `probe-overridden` — `env-spec-tracked` reported "met" from the presence of a `github.com` URL; the GitHub API and `git ls-remote` show that repository does not exist.
- **should/002** `probe-overridden` — `ci-present` reported "met" from the presence of a re-run workflow; the workflow tests the Makefile route, not the (currently broken) README route.
- **should/006** `probe-overridden` — same workflow, different gap: CI checks environment *metadata*, never actually invokes the container.
- **should/007** `unverified-claim` — "met" rests on the object's own disclosure (`.sif.README`) that the archived file is a reduced stand-in; not independently confirmed beyond reading that file.
- **should/008** `upstream-duplicate` — same sentence as must/014.

## Not checked

None. All 31 items received a judgement verdict (none left `not-checked`); the one expensive probe (`fresh_rerun.py`) was not run — see Scope — but equivalent evidence (the CI workflow) answers should/004 directly, so nothing falls to `not-checked` as a result.

## Goals and kind

**Goals** (from `README.md` and `docs/README.md`, not confirmed with a user — this is a scripted, unattended run): the object answers whether brain volume grows with age (8–20y) and whether the GM/WM ratio falls over the same range, using FreeSurfer tables shipped by `ds007116`, joined with per-session ages and plotted.

**Kind — ASSUMPTION (unconfirmed, no user available):** **study** — a question answered with data and compute, consuming another dataset's derivatives and producing a small joined table and one figure of its own. Per [`project-kinds.md`](../stamped-conventions/references/project-kinds.md) this is "a study whose product is a re-derivation from another dataset's derivatives," so S.1/M.1 were judged on whether the input is *linked* (it is, via `.gitmodules`) rather than copied, and E.1 was weighed lightly given the computation is a few seconds of CPU. All seven principles were in scope; nothing was treated as `not-applicable` on kind grounds.

## Checklist URL and stamp

Filled checklist: see [`2026-10-14-url.txt`](2026-10-14-url.txt).

> Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on `https://github.com/con/stamped-eval-fixture-r0.git` at commit `9c85091aa23ded6b51b25a327e5f267e8e10b4af`, 2026-10-14, claude-code (agent harness)/claude-sonnet-5.
> Probe output: [`2026-10-14-probes.json`](2026-10-14-probes.json).
> Full response: [`2026-10-14-response.json`](2026-10-14-response.json).

## Scope

Assessed the local clone at the commit above. `FIXTURE.md` (in the object) discloses this is a calibration fixture with two deliberately simulated facts — the submodule pinned to a commit not on the real upstream, and an unpublished `origin` remote. Both were independently re-verified over the network (`git fetch --depth=1` for the commit; the GitHub API and `git ls-remote` for the remote) rather than taken on the file's word; both confirmed unmet (must/002, must/016). `gh` is unauthenticated, so the project's own issue tracker was not checked (Step 5); this does not block the assessment, and the repository is unpublished in any case. The expensive `fresh_rerun.py` probe was not run (no second host, no user to grant consent); should/004 is answered instead from equivalent committed evidence (the CI workflow running on a fresh cloud VM), per the conventions' "equivalent evidence counts" invariant.
