# STAMPED assessment: ReproNim/simple_workflow (2026-10-15)

**Verdict.** MUST: 10/17 met, 6 partial, 1 unmet, 0 not-checked. SHOULD: 4/9 met, 3 partial, 1 unmet, 1 not-applicable (denominator 8 applicable), 0 not-checked. MAY: 0/5 met, 2 partial, 3 unmet.
No overall score.

**Scope.** Committed state at 225f1dc (clean tree); no submodules; `--check-remote` run (git ls-remote resolves); fresh rerun not attempted; `gh` unauthenticated (issues read through the public API); CircleCI status not retrievable.

**Assumptions (user unavailable, not confirmed).** Goal: a re-executable neuroimaging publication demo (F1000Research 2017) that runs BET/FAST/FIRST on NITRC-IR images and compares to expected output. Kind: **study** (primary), with a reusable container recipe (Simple_Prep_docker) as a secondary component.

## What to fix first
1. Pin the container by digest and record it, and re-sync Dockerfile with Simple_Prep_docker-Dockerfile.in (template lacks fsl-mni152-templates; CI builds the template, the image comes from the Dockerfile) -> the published image and the tested one are different recipes -> must/015, must/014, should/006, should/008.
2. Record the environment (image digest, Dockerfile commit) next to the outputs; nipype PROV records tool versions but no spec -> must/006.
3. Bring the inputs inside the boundary or pin them: the image list lives in a Google Sheet and a live nitrc.org session -> must/001, must/002.
4. State host assumptions (network to nitrc.org, snapshot "knock", x86_64, Python 2.7 era) in the README -> must/011; pin miniconda and note host-route FSL -> must/010.
5. Confirm CI still runs (circleci/classic:201711-01; last commit 2022-02-09) -> should/002, should/004.

## Already good
- Exact conda package builds in `environment.yml`; FSL pinned by apt snapshot date in `Dockerfile`.
- Public image `repronim/simple_workflow` on Docker Hub plus public GitHub repo; README documents Docker, host and Singularity routes.
- CI builds and runs the workflow in a fresh container and checks `MATCH` (`.circleci/config.yml`); nipype PROV files are shipped.

## Per-item table
| item | principles | status | source | evidence | reason |
|---|---|---|---|---|---|
| must/001 | S.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md`, `run_demo_workflow.py` | Code, specs and expected outputs sit under one root, but the input images (listed in a Google Sheet named only in README prose, fetched from nitrc.org) and FSL packages live outside it. |
| must/002 | S.1 | unmet | judgement | `run_demo_workflow.py`, `README.md` | No submodules; inputs are downloaded at run time from nitrc.org via a Google Sheet key, so code reaches data across the root boundary; no pinned copy or link. |
| must/003 | S.1 | met | judgement | `Dockerfile`, `Simple_Prep.sh` | On the documented container route, Dockerfile installs FSL from a dated NeuroDebian snapshot and Simple_Prep.sh builds the conda env inside the image; host-route FSL is assumed (see must/010). |
| must/004 | T.1,T.3,T.5 | met | probe:tree-clean | `git ls-files`, `git status --porcelain` | git tracks 131 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| must/005 | T.1,T.3,T.5 | met | probe:large-in-annex | `git ls-tree -r -l HEAD` | No binary blob over 10 MiB in git, and no large-content mechanism is needed: nothing in this object is large binary data. |
| must/006 | T.1,T.3,T.5 | partial ⚠ (a MUST is not satisfied by partial) | probe:derived-have-records+judgement | `expected_output/workflow_provenance_20170410T112143.provn`, `run_demo_workflow.py` | nipype PROV (.provn/.trig) records tool versions (nipype 0.12.0, FSL 5.0.9, python 2.7.12) but not Dockerfile/image digest; no script-level record links outputs to their spec. |
| must/007 | A.1 | met | probe:entry-point+judgement | `README.md`, `README.md` | README.md has numbered install and usage sections (Docker, Simple_Prep.sh, Singularity); probe wanted a heading it did not find (has_section false). |
| must/008 | A.1 | met | probe:entry-point | `README.md`, `Simple_Prep.sh`, `check_output.py`, `run_demo_workflow.py` | Starting point present: Simple_Prep.sh. |
| must/009 | P.1 | met | probe:no-abs-paths+judgement | `run_demo_workflow.py`, `.circleci/config.yml` | Python/shell code uses $PWD, abspath(args) and CLI dirs; probe hits are only ${HOME}/tmp in .circleci/config.yml (CI-runner variables) and in-image /opt/repronim paths. |
| must/010 | P.1 | partial ⚠ (a MUST is not satisfied by partial) | probe:env-spec-tracked+judgement | `environment.yml`, `Simple_Prep.sh`, `Simple_Prep.sh` | environment.yml pins every conda package to build (probe wrongly says unpinned); but host route assumes FSL/curl preinstalled, miniconda is "latest", base apt tools unpinned. |
| must/011 | P.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md`, `Dockerfile` | README names OS X/GNU Linux, FSL, curl, git/unzip, path length, Singularity version; but NITRC network access, x86_64, snapshot-neuro knock and Python 2.7 era limits are not stated. |
| must/012 | P.2 | met | judgement | `README.md`, `environment.yml` | README lists FSL, curl, git or unzip for the host route and Docker/Singularity v2.4.3+ for container routes; Dockerfile and environment.yml carry the rest. |
| must/013 | P.3 | met | probe:env-spec-tracked | `Dockerfile`, `environment.yml` | Tracked: Dockerfile, environment.yml. |
| must/014 | P.3 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `README.md`, `git:66e52bf`, `Simple_Prep_docker-Dockerfile.in` | Process declared (README: Simple_Prep_docker <dist> <snapshot-date>); history has updates (66e52bf, 05cfced) but 66e52bf changed Dockerfile not the .in template, so spec copies drifted. |
| must/015 | D.1 | partial ⚠ (a MUST is not satisfied by partial) | judgement | `environment.yml`, `Dockerfile`, `README.md` | conda builds and apt snapshot date (20170410T000000Z) pin well, but base image is neurodebian:jessie (tag, no digest), miniconda "latest", and no container digest is recorded. |
| must/016 | D.1 | met | probe:env-spec-tracked+judgement | `https://hub.docker.com/v2/repositories/repronim/simple_workflow/`, `git ls-remote https://github.com/ReproNim/simple_workflow` | Specs are in the public GitHub repo (ls-remote resolves) and image repronim/simple_workflow:latest is on Docker Hub (digest sha256:9d9beda9..., pushed 2019-10-18). |
| must/017 | D.1 | met | judgement | `README.md`, `README.md` | README gives docker pull/run, Simple_Prep.sh, Singularity and Simple_Prep_docker build commands; the :latest image build recipe is not tracked, and "/Simple_Prep_docker" has a stray slash. |
| should/001 | T.2 | met | judgement | `git ls-files` | Single version-control system (git) for all components; no data or modules in another system. |
| should/002 | A.2 | met | probe:ci-present | `.circleci/config.yml#L32`, `.circleci/config.yml#L53` | .circleci/config.yml builds the image and runs the workflow on 2 subjects with MATCH check; no evidence CI still runs (circleci/classic image, last commit 2022-02-09). |
| should/003 | M.1 | partial | probe:modules-separated | `Dockerfile`, `environment.yml` | Environment specs, expected_output/ and other_outputs/ are separate directories, but no inputs/code modules; all in one repository without submodules. |
| should/004 | E.1 | met | judgement | `.circleci/config.yml` | No rerun attempted; equivalent committed evidence: CircleCI machine builds the image fresh and runs the workflow in docker run --rm, checking MATCH (not confirmed to have run recently). |
| should/005 | E.1 | met | judgement | `README.md`, `.circleci/config.yml` | Documented container route uses docker run --rm per execution (README and CI), so each run gets a fresh container; the host-route conda env is reused. |
| should/006 | D.2 | partial | probe:ci-present+judgement | `.circleci/config.yml`, `Dockerfile`, `Simple_Prep_docker-Dockerfile.in` | CI builds via Simple_Prep_docker from the .in template, not the tracked Dockerfile/published image; the two differ (template lacks fsl-mni152-templates). CI liveness unconfirmed. |
| should/007 | D.2 | unmet | judgement | `Dockerfile` | No image tarball, binaries or package cache archived in the object; image is only referenced on Docker Hub and FSL comes from external apt snapshots. |
| should/008 | D.2 | partial | judgement | `README.md`, `git:66e52bf` | Same answer as must/014: process declared (Simple_Prep_docker <dist> <date>), updates in history, but Dockerfile and its template drifted at 66e52bf. |
| should/009 | M.4 | not-applicable | judgement | — | N/A: empty subject. No restricted data in the object; non-free FSL is apt-installed at build time and its licence is noted in README, nothing restricted is shipped. |
| may/001 | M.2 | unmet | probe:subdatasets-resolvable+judgement | `git ls-files` | No .gitmodules or subdatasets; external software (apt snapshot, conda) and data (nitrc.org) are referenced by URL, not linked as submodules. |
| may/002 | M.2 | unmet | judgement | `README.md` | README does not describe how environment, code and expected outputs relate or recombine, other than varying the snapshot date. |
| may/003 | M.2 | partial | judgement | `README.md` | Environment can be varied by dist/snapshot date independent of the scripts (README s3), but code and env are copied into one image and expected_output must track both. |
| may/004 | M.2 | partial | judgement | `Dockerfile` | Dockerfile COPY and Simple_Prep.sh compose env, scripts and expected output at build time; this is container composition, with no module mechanism. |
| may/005 | M.2 | unmet | judgement | `README.md` | No documentation or tooling for navigating the structure; README is run-instructions only and other_outputs/ has no explanatory note. |


## Flagged items
- must/006 (probe-overridden): probe saw 29 derived files with no record; nipype PROV files do record tool versions. Partial.
- must/007 (probe-overridden): probe wanted an install heading; README has numbered install/usage sections.
- must/009 (probe-overridden): hits are CI-runner `${HOME}`/`/tmp` and in-image `/opt` paths, not hardcoded host paths in scripts.
- must/010 (mapping-questioned): probe said "pins no versions"; environment.yml pins everything. Real gaps are host-route FSL, miniconda latest.
- should/006 (probe-overridden): probe saw "environment-building step"; the built recipe differs from the tracked Dockerfile.
- must/014 and should/008 (upstream-duplicate): same sentence, same evidence.
- unverified-claim: must/002, must/011, should/002, should/004 (CI liveness and nitrc.org access not confirmed).

## Not checked
None. Known limits: image digest not pulled and compared to the Dockerfile; CircleCI history unreachable; open upstream issue #68 ("Simple_prep.sh works outside of main repo") and closed #63 "Circle-CI is broken" are already tracked, not new findings.

## Goals and kind
Stated in README: accompanies Ghosh et al. 2017, a re-executable neuroimaging demo. Kind: study (assumed, see above). Emphasis: T and S, then A, P.

## Checklist URL
See `2026-10-15-url.txt`. Response: `2026-10-15-response.json`; probes: `2026-10-15-probes.json`.

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on https://github.com/ReproNim/simple_workflow at commit `225f1dc`, 2026-10-15, claude-code (subagent)/claude-sonnet-5-5.
Probe output: `2026-10-15-probes.json`.
