# STAMPED assessment: con/stamped-eval-fixture-r0 (2026-10-15)

**Labelled assumptions (user not available, not confirmed):** kind = **study** (README: "a tiny, fully recorded study"; docs/README.md states the question). Goals taken from docs/README.md: does brain volume grow with age over 8-20 years, and does the GM/WM ratio fall over that range. Neither was confirmed with a user.

**Verdict line.** MUST: 8 met / 6 partial / 3 unmet / 0 not-checked (of 17). SHOULD: 3 met / 4 partial / 1 unmet / 0 not-checked / 1 not-applicable (of 9). MAY: 5 met / 0 partial / 0 unmet / 0 not-checked (of 5).

## What to fix first

1. **Make the pinned module commit reachable.** Re-publish `sourcedata/ds007116` at a commit the upstream remote has, or re-pin `.gitmodules` to one. Why: a stranger cannot init the input, and the CI checkout fails on the same commit. Closes must/002, unblocks should/002 and should/004.
2. **Publish the superdataset to a remote that anonymous clones can reach.** Why: the environment spec and the run records currently travel with nobody. Closes must/016.
3. **Fix the Reproduce order and make the two routes agree.** Order it as clone, `git submodule update --init`, then `make all`. Make the Makefile call `.venv/bin/python`, or say to activate the venv. Why: following the section as written runs collect before the input exists and silently writes a header-only table. Closes must/007, must/008, must/017 (and should/002 once CI runs it).
4. **Write the host assumptions down and bring apptainer into the spec.** Name apptainer, the python3 version and the OS in README, and give the install command. Why: every recorded run needs apptainer, and no document names it. Closes must/010, must/011, must/012.
5. **Make the recorded container obtainable, and have CI run it.** Archive the image (git-annex) or document the pull by digest, and run the recorded `apptainer exec` in CI instead of only checking a placeholder exists. Why: the placeholder cannot reproduce the recorded environment. Closes should/006, should/007, must/017.

Also open: must/014 and should/008 (the same question) need a lockfile update recorded in history. The header command also needs `-o requirements.lock`.

## What the project already does well

- Layout is clean: input as a linked submodule, code, results and figures apart, and docs/README.md explains the coupling (should/003, may/002, may/005).
- Two `[DATALAD RUNCMD]` records exist, and their outputs match the tracked files: `PNG-placeholder:3` matches the 3 data rows in `results/volumes.tsv` (must/006, must/004).
- Environment is pinned: `requirements.lock` with exact versions, and the container is pinned by digest, never `:latest` (must/013, must/015).

## Per-item table

Sources: `P:` = scripted probe (named), `J` = judgement from a reading of the object. Verdict counts are over the 31 pinned items.

| Item | Principles | Status | Source | Reason (first words) |
|---|---|---|---|---|
| must/001 | S.1 | met | J | Everything the object ships sits under the root |
| must/002 | S.1 | unmet | P:subdatasets-resolvable+J | Pinned module commit 84570256 not fetchable from recorded url |
| must/003 | S.1 | met | J | Python packages pinned; container registered |
| must/004 | T.1,T.3,T.5 | met | P:tree-clean | Code, text, config tracked; git status empty |
| must/005 | T.1,T.3,T.5 | met | P:large-in-annex | No blob over 10 MiB |
| must/006 | T.1,T.3,T.5 | met | P:derived-have-records | Both derived files trace to run records |
| must/007 | A.1 | partial | P:entry-point+J | Reproduce out of order; make calls host python3 |
| must/008 | A.1 | partial | P:entry-point+J | Two starting points; collect before submodule init |
| must/009 | P.1 | met | P:no-abs-paths | No host absolute paths in tracked text |
| must/010 | P.1 | partial | P:env-spec-tracked+J | Python pinned; host python3 and apptainer not in spec |
| must/011 | P.1 | unmet | P:platform-assumptions+J | Host assumptions undocumented; apptainer unnamed |
| must/012 | P.2 | partial | P:platform-assumptions+J | Python deps listed; no system requirements |
| must/013 | P.3 | met | P:env-spec-tracked | requirements.lock and containers.json tracked |
| must/014 | P.3 | partial | J | Regeneration command declared; no update in history |
| must/015 | D.1 | met | P:run-env-linked | Digest pinned, named by both records |
| must/016 | D.1 | unmet | P:env-spec-tracked+J | Remote not reachable anonymously |
| must/017 | D.1 | partial | J | Install documented; no obtain step for the image |
| should/001 | T.2 | met | J | git used for every component |
| should/002 | A.2 | partial | P:ci-present+J | CI runs make all only; checkout fails at pinned commit |
| should/003 | M.1 | met | P:modules-separated | Inputs, code, derived, environment in distinct places |
| should/004 | E.1 | partial | J | Fresh hosted runner, but checkout cannot reach make all |
| should/005 | E.1 | met | J | Each recorded run is one apptainer exec |
| should/006 | D.2 | partial | P:ci-present+J | CI checks a placeholder, never runs the recorded container |
| should/007 | D.2 | unmet | J | Image not archived; tracked .sif is a placeholder |
| should/008 | D.2 | partial | J | Same as must/014 |
| should/009 | M.4 | not-applicable | J | N/A: every component public; no restricted module |
| may/001 | M.2 | met | P:subdatasets-resolvable+J | Input linked as submodule |
| may/002 | M.2 | met | J | docs/README.md documents structure and recombination |
| may/003 | M.2 | met | J | Plot and collect depend on named files only |
| may/004 | M.2 | met | J | Makefile rules and submodule compose the parts |
| may/005 | M.2 | met | J | Layout table and docs/README.md navigate it |

## Flagged items

- must/002: probe partial overridden to **unmet**. Pinned commit confirmed unfetchable; local `.git/config` override hides it in this checkout.
- must/007, must/008: probe "entry point present" overridden. The documented route is out of order and does not match the Makefile.
- must/010, must/011, must/012: host and apptainer assumptions the probe cannot see; must/011 overrode a not-checked to unmet.
- must/014 and should/008: `upstream-duplicate`, same sentence.
- must/016: probe met overridden. Anonymous `git ls-remote` fails.
- should/002, should/006: probe presence of a make/digest string overridden; mapping-questioned.
- should/004: `unverified-claim`. Inferred failure of the checkout; CI run history not seen.
- may/001: probe partial for resolvability overridden to met; that property belongs to must/002.

## Not checked

- CI run history: whether `rerun.yml` has ever passed. Needs `gh` (not authenticated) or the Actions page.
- Container digest against a registry: not pulled, per the skill.
- Fresh rerun (`fresh_rerun.py`): not run. The user is absent, so no consent, and it needs another host.
- Issue tracker (Step 5): `gh` not authenticated, so skipped. No TODO or known-gap file in the object.

## Goals and kind

Goals and kind are labelled assumptions (see top). Emphasis for a study: T and S carry most weight; the record for each derived file was checked, and the input is linked, not copied.

## Checklist URL and stamp

Checklist URL (about 7.8 kB): see `2026-10-15-url.txt`.
Response JSON: `2026-10-15-response.json`. Probe output: `2026-10-15-probes.json`.

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on https://github.com/con/stamped-eval-fixture-r0.git at commit `29bc6a2`, 2026-10-15, claude-code/claude-haiku-5-5.
