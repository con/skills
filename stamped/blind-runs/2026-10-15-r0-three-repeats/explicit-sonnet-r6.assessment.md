# STAMPED assessment: ds007116 brain volume vs age (study)

Goals/kind (assumption, no user to confirm): a small study producing one figure from shipped FreeSurfer derivatives; kind = study.
Scope: committed state at 4924acb4. Probes run with --check-remote; probes preceded the CI workflow commit, two items overridden by reading. Fresh rerun not attempted; an independent subagent reproduced the table from a clone.

**Verdict:** no MUST unmet; one MUST partial: must/016 (remote is a filesystem path, not a URL: gap handed by the task; needs a forge remote). must/012/014/017 were partial until README gained a requirements section (re-answered after that commit).
**Fix first:** push to a forge so a stranger can clone.
**Already good:** every product has a DataLad run record naming the pinned lockfile; input linked as a subdataset; clean tree; no absolute paths.

| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | met | judgement | `README.md` | Code, results, figure, docs and plan are under one root; the only input is a linked subdataset with a GitHub URL. Nothing lives on a share. |
| must/002 | S.1 | met | probe:subdatasets-resolvable | `.gitmodules` | All 1 linked module(s) carry urls that resolve from elsewhere: sourcedata/ds007116 |
| must/003 | S.1 | met | judgement | `code/tooling.lock` | No external software outside the environment: python deps are in the lockfile; datalad/git-annex pinned in code/tooling.lock; the input is a subdataset. |
| must/004 | T.1,T.3,T.5 | met | probe:tree-clean | `git ls-files`, `git status --porcelain` | git tracks 19 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | T.1,T.3,T.5 | met | probe:large-in-annex | `git ls-tree -r -l HEAD`, `.datalad/config` | git-annex carries the binary content (1 pointer(s) tracked) and no binary blob over 10 MiB is in git. |
| must/006 | T.1,T.3,T.5 | met | probe:derived-have-records | `figures/brain-volume-gmwm-vs-age.png`, `results/controls.txt`, `results/volumes-batch1.tsv`, `results/volumes-pilot.tsv`, `results/volumes.tsv` | All 5 derived file(s) trace to a re-executable record (8 run record(s), workflows: none). |
| must/007 | A.1 | met | probe:entry-point | `README.md`, `code/extract_volumes.py`, `code/preflight.sh`, `code/run-recorded.sh` | README.md has an install/usage/reproduce section. |
| must/008 | A.1 | met | probe:entry-point | `README.md`, `code/extract_volumes.py`, `code/preflight.sh`, `code/run-recorded.sh` | Starting point present: code/extract_volumes.py. |
| must/009 | P.1 | met | probe:no-abs-paths | `probe:no-abs-paths` | No host-specific absolute paths in tracked text files. |
| must/010 | P.1 | met | probe:env-spec-tracked | `code/requirements.lock` | Dependencies are pinned in code/requirements.lock, and no tracked script expects a tool to be present already. |
| must/011 | P.1 | met | judgement | `code/py.sh` | Only POSIX sh, uv and datalad are needed; no brew/BSD flags/scheduler. Python 3.12 pinned in code/py.sh. OS not stated in README: minor gap. |
| must/012 | P.2 | met | judgement | `README.md` | README states Linux/POSIX shell, modest RAM, no GPU/container/scheduler, and network needs. |
| must/013 | P.3 | met | probe:env-spec-tracked | `code/requirements.lock` | Tracked: code/requirements.lock. |
| must/014 | P.3 | met | judgement | `README.md` | README states updates are a separate commit via uv pip compile; history has only the initial lock (no update yet), so the process is stated, not yet exercised. |
| must/015 | D.1 | met | probe:run-env-linked | `commit:f0d51dc`, `commit:acc8252`, `commit:328f8b6`, `commit:1ef2e67`, `commit:547eba5` | 8 run record(s) reference a pinned image or lockfile, and no ':latest' reference is tracked. |
| must/016 | D.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md` | Published only to a bare repo on the shared filesystem: no URL a stranger can reach. Gap handed by the task; closing needs a forge remote (GitHub/Codeberg) and credentials. |
| must/017 | D.1 | met | judgement | `README.md` | README says how to install uv/datalad and that code/py.sh builds the lock-pinned environment on demand. |
| should/001 | T.2 | met | judgement | `.datalad/config` | Code, results and the input module are all in one DataLad dataset (one VCS). |
| should/002 | A.2 | partial | probe:ci-present+judgement | `.github/workflows/ci.yml` | A workflow re-derives the pilot unit and diffs it, but it has not been run on any runner (no forge), so it is intent, not evidence. |
| should/003 | M.1 | met | probe:modules-separated | `sourcedata`, `sourcedata/ds007116`, `code`, `figures`, `results`, `code/requirements.lock` | 4 kinds of component live in distinct places: inputs in sourcedata, sourcedata/ds007116; code in code; derived in figures, results; environment in code/requirements.lock |
| should/004 | E.1 | not-checked | judgement | `docs/report.md` | Fresh rerun not attempted by the assessor; an independent subagent reviewed a clone, but no CI runner exists. |
| should/005 | E.1 | unmet | judgement | `code/run-recorded.sh` | Each run reuses the host's long-lived uv cache and shell; no container or batch job per run. |
| should/006 | D.2 | partial | probe:ci-present+judgement | `.github/workflows/ci.yml` | Workflow recompiles the lock from requirements.in and diffs it; it does not build a container/environment. Never executed. |
| should/007 | D.2 | unmet | judgement | `code/requirements.lock` | No environment artifact is archived: only a lockfile is tracked; wheels and interpreters are fetched from PyPI at run time. |
| should/008 | D.2 | partial | judgement | `README.md` | Process documented (as must/014) but never exercised in history. |
| should/009 | M.4 | not-applicable | judgement | `sourcedata/ds007116` | No restricted data or software; the input is a public OpenNeuro dataset. |
| may/001 | M.2 | met | probe:subdatasets-resolvable | `.gitmodules` | 1 external component(s) are linked as modules: sourcedata/ds007116 |
| may/002 | M.2 | partial | judgement | `docs/plan.md` | docs/plan.md names components (inputs, code, results, figures) and README shows the layout; no separate modularity doc. |
| may/003 | M.2 | not-checked | judgement | `none` | Only one external module; independence of boundaries is not assessable. |
| may/004 | M.2 | not-checked | judgement | `none` | Single module; composition independence not assessable. |
| may/005 | M.2 | not-applicable | judgement | `sourcedata/ds007116` | A single input module is linked directly; no composition mechanism is needed. |

Flagged: should/002, should/006 probe-overridden (CI added after the probe run); must/011 unverified-claim; must/014 and should/008 upstream-duplicate.
Not checked: should/004, may/003, may/004.
URL: see 2026-10-15-url.txt. Stamp: in 2026-10-15-response.json.
