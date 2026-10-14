# STAMPED assessment: dandi/compression-comparisons-t261-study

**Object:** <https://github.com/dandi/compression-comparisons-t261-study> at commit `f2f0802`
**Kind:** study (a BIDS derivative dataset with its own compute)
**Checklist:** 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`)
**Date:** 2026-10-13 · **Assessor:** `assess-alignment-with-stamped-principles` at this commit

MUST: 4 met / 8 partial / 5 unmet (of 17)
SHOULD: 2 met / 1 partial / 4 unmet / 1 not-checked / 1 not-applicable (of 9)
MAY: 5 met (of 5)

No single overall score: a MUST at `partial` is a MUST failure, and `not-checked`
is reported apart from `unmet` throughout. Of the 31 answers, 14
came from a probe, 1 from a probe a reading of the object
overrode, and 16 from reading the object.

## Corrections since the first pass

This reference answer was corrected on 2026-10-13 after a **blind run** of the
same skill by an independent subagent, which saw only the object and the skill
snapshot (`evals/stamped/blind-runs/2026-10-13-assess-t261/`). It disagreed on
eight items and was better evidenced on five of them; three of its
disagreements were probe defects, now fixed:

| item | first pass | now | why |
|---|---|---|---|
| `must/009` | partial | **unmet** | The probe only knew `/home` and `/tmp`, so four `/data/<user>/...` paths in the entry points read as clean. Two of them (`run_sorting_loop.sh`, `run_sorting_sweep.sh`) have no fallback, so the sorting entry points cannot run on another host. |
| `must/005` | partial | **met** | The probe downgraded on 22 oversized `duct-usage.jsonl` blobs, but the item asks about large *binary* data and git-annex carries the binary content (13407 pointers). The clone weight is real and is now its own extra finding. |
| `must/010` | partial | **unmet** | The probe hedged that a specification might live in an uninstalled module; the object carries positive evidence of relying on host tools (a datalad built from commit `30b6dee`, expected on `PATH`). |
| `should/003` | not-checked | **met** | The probe answered from "were the inputs modified", which it could not read. The item asks about separation into distinct modules, which the committed layout shows. |
| `must/001`, `must/003`, `must/011`, `must/014`, `should/008` | met / met / met / unmet / unmet | **partial** ×5 | The blind run's readings were sharper: the venv is essential and untracked; host tools are neither included nor linked; the `/data` mount is undocumented; and there *is* a tracked update process for the pins (16 "Pin the tool to …" commits), just not for a specification. |

Reference answers are not frozen truth, and a correction is recorded with its
reason rather than quietly applied.

## Goals, as the documentation states them

`dataset_description.json#Purpose` states two questions, in order: (1) can an
independent reimplementation reproduce Buccino et al. 2023's lossless
compression results on their own recordings and conditions, and (2) where does
the newly standardised ITU-T T.261 / H.BWC codec sit against that codec set —
on compression ratio, on distortion, and on the spikes recovered from
decompressed data.

**This assessment did not review those goals with the project's maintainer.**
The skill asks for that step; here the goals are taken from the documentation
alone, and the kind (`study`) is the assessor's reading of
`DatasetType: derivative` plus 1216 run records of its own compute. Both are
assumptions a maintainer could correct.

## What to fix first

1. **Publish the tool module and record its real URL.**
   `.gitmodules` records `url = ../..` for `code/compression-comparisons-tools`,
   which resolves only next to the superdataset it was cloned beside, so a
   fresh clone elsewhere cannot get the code that produced the numbers. The
   `datalad-url` beside it is a path on one machine. Replacing it with the
   public `dandi/compression-comparisons` URL closes **must/002**: everything
   else is reproducible *in principle* and this is what stops it in practice.
2. **Unpin the entry points from `/data/<user>/…`.**
   `run_sorting_loop.sh:30` and `run_sorting_sweep.sh:48` assign
   `WV=/data/<user>/compression-comparisons/vendor/wavpack` **unconditionally**,
   so the sorting sweep cannot start on any other host; `run_sweep.sh:84` at
   least falls back to the vendored copy first, and `partial_report.sh:47`
   reads a reference CSV from the same mount. Vendoring wavpack into the
   object, or resolving it relative to `$STUDY` with a documented override,
   closes **must/009** — and this is the gap a reader hits *after* fixing (1).
3. **Ship an environment specification, not only instructions.**
   The README tells a reader how to build `envs/compbench`, but nothing pins
   what ends up in it: the extras (`wavpack-numcodecs`, `flac-numcodecs`) are
   unpinned, the patched datalad is prose, and the venv is gitignored. A
   tracked `uv pip freeze` / `uv.lock` plus the datalad build reference would
   close **must/010**, **must/012**, **must/014**, **must/015**, **must/016**,
   **must/017**, **should/007** and **should/008** at once, and lift
   **must/013** out of `partial`. For a study whose central claim is a
   *reproduction*, this is the gap that matters most after (1) and (2).
4. **Record the sweep-level aggregates.**
   1218 of 22286 derived files — `AUTO_TABLE.md`, `RESULTS.md`, the duct traces
   of aggregate steps — were last touched by an ordinary commit rather than a
   run record, which the README already names as a known gap ("no sweep-level
   run record"). A recorded aggregation step would move **must/006** to `met`;
   the per-cell provenance is already there.
5. **Add CI that rebuilds the environment and re-runs one cheap cell.**
   There is no CI configuration at all, so nothing catches the instructions
   drifting from the object (**should/002**, **should/006**), and the
   environment has never been shown to rebuild from what is published.

## What this project already does well

- **Per-cell provenance at a scale most projects do not reach.** 1216
  `[DATALAD RUNCMD]` records, one per computed cell, each naming the tool
  commit, inputs and command line, plus a duct trace of resources — the
  programmatic provenance of T.4, which the checklist has no item for.
- **An executable guard where prose would have been easier.** `run_sweep.sh`
  refuses to start against a drifted or dirty tool checkout, and a pre-commit
  guard refuses commits while a sweep is in flight. Both are the lessons of
  real incidents turned into artifacts.
- **Measurements treated as immutable, with the failures documented.**
  `dataset_description.json#Layout` states that derivatives are immutable
  while narrative may be corrected; the README records the three incidents
  that cost finished compute, including the datalad bug behind them, rather
  than quietly re-running.
- **Large content handled properly.** 13407 annexed pointers, no binary blob
  over 10 MiB in git, a clean tree, and a layout documented twice (README and
  `dataset_description.json`) for readers and for machines.

## Per item

| item | principles | status | evidence | reason |
|---|---|---|---|---|
| `must/001` | S.1 | **partial** | `.gitignore`; `README.md#Layout` | One DataLad root holds code, inputs and derivatives, but envs/compbench — the venv every result came from — is gitignored, so it is not reachable within the object. |
| `must/002` | S.1 | **unmet** | `.gitmodules` | 1 of 2 linked module(s) do not resolve elsewhere: code/compression-comparisons-tools url=../.. — relative url: resolves only next to this superdataset |
| `must/003` | S.1 | **partial** | `.gitmodules`; `code/run_sweep.sh#L27` | The benchmark tool and the BWC source are one pinned submodule, but the patched datalad and the wavpack/flac binaries are host tools the scripts expect to find. |
| `must/004` | T.1, T.3, T.5 | **met** | `git ls-files`; `git status --porcelain` | git tracks 4422 text, code and configuration file(s), and `git status` is empty including submodules: the committed state is the whole state. |
| `must/005` | T.1, T.3, T.5 | **met** | `git ls-tree -r -l HEAD`; `.datalad/config` | git-annex carries the binary content (13407 pointer(s) tracked) and no binary blob over 10 MiB is in git. |
| `must/006` | T.1, T.3, T.5 | **partial** | `derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/AUTO_TABLE.md`; `derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/RESULTS.md`; `derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/aind-ibl-np1-CSHZAD026-slice10__blosc-lz4-level_3-shuffle_byte/duct-info.json` | 1218 of 22286 derived file(s) have no re-executable record, e.g. derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/AUTO_TABLE.md; last touched by an ordinary commit. |
| `must/007` | A.1 | **met** | `README.md`; `code/run_sorting_sweep.sh`; `code/run_sweep.sh` | README.md has an install/usage/reproduce section. |
| `must/008` | A.1 | **met** | `README.md`; `code/run_sorting_sweep.sh`; `code/run_sweep.sh` | Starting point present: code/run_sorting_sweep.sh. |
| `must/009` | P.1 | **unmet** | `code/partial_report.sh#L47`; `code/run_sorting_loop.sh#L30`; `code/run_sorting_sweep.sh#L48` | 4 host-specific absolute path(s) in 4 script(s) or config(s), e.g. code/partial_report.sh line 47: /data/yoh/compression-comparisons/.specify/specs/paper-reference-lossless.csv |
| `must/010` | P.1 | **unmet** | `code/run_sorting_loop.sh#L20`; `code/run_sorting_sweep.sh#L36`; `code/run_sweep.sh#L34` | 3 tracked script(s) require a tool to be installed on the host already, e.g. code/run_sorting_loop.sh line 20 (see line); that dependency is not in any tracked specification. |
| `must/011` | P.1 | **partial** | `README.md`; `code/run_sorting_sweep.sh#L48` | README documents the patched datalad, the cmake flag and the GPU, but not the /data mount the sorting entry points require, which is the assumption that actually breaks elsewhere. |
| `must/012` | P.2 | **partial** | `README.md#Reproducing` | README lists the install steps, but no tracked spec names versions: wavpack-numcodecs and flac-numcodecs are unpinned and the datalad build is prose. |
| `must/013` | P.3 | **partial** | `code/run_sorting_loop.sh#L20`; `code/run_sorting_sweep.sh#L36`; `code/run_sweep.sh#L34` | No specification in this object; it may be inside the module(s) not installed here: code/compression-comparisons-tools, sourcedata/aind-ephys-compression. |
| `must/014` | P.3 | **partial** | `git log --grep='Pin the tool'`; `.gitignore` | A tracked update process exists for the pins (16 'Pin the tool to ...' commits), but not for an environment specification, because the object has none. Same sentence as should/008. |
| `must/015` | D.1 | **unmet** | `commit:7733465`; `commit:13f2689`; `commit:37d7125` | The run records capture the environment but nothing pins one: there is no image digest or frozen manifest another person could replicate from. |
| `must/016` | D.1 | **unmet** ⚑ probe-overridden | `code/run_sweep.sh#L27-L40`; `code/run_sweep.sh#L84` | Nothing to obtain: no lockfile, image or frozen manifest is published anywhere, and the documented route rebuilds from host tools. Probe hedged on the uninstalled modules; the scripts settle it. |
| `must/017` | D.1 | **partial** | `README.md#Reproducing` | README's 'Reproducing' gives runnable uv/cmake steps and the install-after-pin rule, but there is no specification to obtain, so the documentation cannot point at one. |
| `should/001` | T.2 | **met** | `.gitattributes`; `.gitmodules` | git plus git-annex through DataLad across the superdataset and both linked modules; 13407 annexed pointers and no second system. |
| `should/002` | A.2 | **unmet** | `probe:ci-present` | No CI configuration: nothing checks that the instructions still work. |
| `should/003` | M.1 | **met** | `sourcedata`; `sourcedata/aind-ephys-compression`; `code` | 3 kinds of component live in distinct places: inputs in sourcedata, sourcedata/aind-ephys-compression; code in code; derived in derivatives |
| `should/009` | M.4 | **not-applicable** | — | N/A, empty subject: every component is public (AIND open data on the AWS registry, MIT code), so there are no restricted data or software to isolate. |
| `should/004` | E.1 | **not-checked** | — | Nothing in the object records a fresh-environment rerun, and attempting one needs 523 GB of input and a GPU. fresh_rerun.py was not run. |
| `should/005` | E.1 | **unmet** | `README.md`; `probe:run-env-linked` | One long-lived venv (envs/compbench) is reused across the whole sweep by design; duct records each run but does not isolate it. |
| `should/006` | D.2 | **unmet** | `probe:ci-present` | No CI configuration: nothing checks that the instructions still work. |
| `should/007` | D.2 | **unmet** | `.gitignore`; `probe:env-spec-tracked` | No environment artifact is archived with the object: the venv is gitignored and no container image or built binary is kept. |
| `should/008` | D.2 | **partial** | `git log --grep='Pin the tool'` | Word-for-word the same question as must/014, at a different level; answered from the same evidence. The pins have a tracked update process, the absent environment spec cannot. |
| `may/001` | M.2 | **met** | `.gitmodules` | 2 external component(s) are linked as modules: code/compression-comparisons-tools, sourcedata/aind-ephys-compression |
| `may/002` | M.2 | **met** | `README.md#Layout`; `dataset_description.json` | The modular structure is documented twice: the README's Layout section and dataset_description.json's Layout, SourceDatasets and GeneratedBy fields. |
| `may/003` | M.2 | **met** | `code/run_sweep.sh#L75-L82`; `dataset_description.json` | The tool boundary is enforced rather than declared: run_sweep.sh refuses a drifted or dirty tool checkout, and sourcedata is documented as never modified. |
| `may/004` | M.2 | **met** | `README.md#Reproducing` | Composition is git submodules under DataLad, with the exact clone and get commands given in the README. |
| `may/005` | M.2 | **met** | `README.md#Layout` | Navigation is documented at two levels: the Layout sections, and a README in each derivatives/reports-* directory. |

## Flagged items

- `must/016` — probe-overridden: Nothing to obtain: no lockfile, image or frozen manifest is published anywhere, and the documented route rebuilds from host tools. Probe hedged on the uninstalled modules; the scripts settle it.

## Not checked

- `should/004` — Nothing in the object records a fresh-environment rerun, and attempting one needs 523 GB of input and a GPU. fresh_rerun.py was not run.

Neither is `unmet`: the first needs 523 GB of input and a GPU, the second needs
the linked modules installed. `scripts/fresh_rerun.py` was not run.

## Outside the checklist

- **Licensing (paper S.2/D.3, no checklist item in 0.3.1):** `partial` —
  `dataset_description.json` states MIT for code and derivatives, but no
  `LICENSE` file, `LICENSES/` directory or `REUSE.toml` makes it
  machine-readable.
- **T.4, code-driven provenance (in principles 0.2.0, no checklist item):**
  `met` — see the run records above.
- **Clone weight:** `partial` — 22 text blobs exceed 10 MiB (239 MiB in total,
  largest 11 MiB), which every clone carries in full before any `datalad get`.
  Text in git is what `-c text2git` asks for, so this is not a `must/005`
  defect; it is still weight a reader pays.
- **Inputs untouched:** `not-checked` — both linked modules are uninstalled
  here, so whether an input moved cannot be read. No 0.3.1 item asks it.

## Open the answers

[Open this assessment in the checklist app](https://checklist.stamped-principles.org/?checklist=0.3.1&responses_version=0.3.1&cols=auto&sections=off&format=3&responses=eyJjaGVja2xpc3RfdmVyc2lvbiI6IjAuMy4xIiwicmVzcG9uc2VzIjp7InN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDAxIjp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJPbmUgRGF0YUxhZCByb290IGhvbGRzIGNvZGUsIGlucHV0cyBhbmQgZGVyaXZhdGl2ZXMsIGJ1dCBlbnZzL2NvbXBiZW5jaCDigJQgdGhlIHZlbnYgZXZlcnkgcmVzdWx0IGNhbWUgZnJvbSDigJQgaXMgZ2l0aWdub3JlZCwgc28gaXQgaXMgbm90IHJlYWNoYWJsZSB3aXRoaW4gdGhlIG9iamVjdC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMDIiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IjEgb2YgMiBsaW5rZWQgbW9kdWxlKHMpIGRvIG5vdCByZXNvbHZlIGVsc2V3aGVyZTogY29kZS9jb21wcmVzc2lvbi1jb21wYXJpc29ucy10b29scyB1cmw9Li4vLi4g4oCUIHJlbGF0aXZlIHVybDogcmVzb2x2ZXMgb25seSBuZXh0IHRvIHRoaXMgc3VwZXJkYXRhc2V0In0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDAzIjp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJUaGUgYmVuY2htYXJrIHRvb2wgYW5kIHRoZSBCV0Mgc291cmNlIGFyZSBvbmUgcGlubmVkIHN1Ym1vZHVsZSwgYnV0IHRoZSBwYXRjaGVkIGRhdGFsYWQgYW5kIHRoZSB3YXZwYWNrL2ZsYWMgYmluYXJpZXMgYXJlIGhvc3QgdG9vbHMgdGhlIHNjcmlwdHMgZXhwZWN0IHRvIGZpbmQuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDA0Ijp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiZ2l0IHRyYWNrcyA0NDIyIHRleHQsIGNvZGUgYW5kIGNvbmZpZ3VyYXRpb24gZmlsZShzKSwgYW5kIGBnaXQgc3RhdHVzYCBpcyBlbXB0eSBpbmNsdWRpbmcgc3VibW9kdWxlczogdGhlIGNvbW1pdHRlZCBzdGF0ZSBpcyB0aGUgd2hvbGUgc3RhdGUuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDA1Ijp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiZ2l0LWFubmV4IGNhcnJpZXMgdGhlIGJpbmFyeSBjb250ZW50ICgxMzQwNyBwb2ludGVyKHMpIHRyYWNrZWQpIGFuZCBubyBiaW5hcnkgYmxvYiBvdmVyIDEwIE1pQiBpcyBpbiBnaXQuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDA2Ijp7InZhbHVlIjoibm8iLCJyZWFzb24iOiIxMjE4IG9mIDIyMjg2IGRlcml2ZWQgZmlsZShzKSBoYXZlIG5vIHJlLWV4ZWN1dGFibGUgcmVjb3JkLCBlLmcuIGRlcml2YXRpdmVzL2NvbXBiZW5jaC0yMDI2LTA4LTE5LUNTSFpBRDAyNi1zbGljZTEwcy1iYW5kcGFzcy9BVVRPX1RBQkxFLm1kOyBsYXN0IHRvdWNoZWQgYnkgYW4gb3JkaW5hcnkgY29tbWl0LiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAwNyI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IlJFQURNRS5tZCBoYXMgYW4gaW5zdGFsbC91c2FnZS9yZXByb2R1Y2Ugc2VjdGlvbi4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMDgiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJTdGFydGluZyBwb2ludCBwcmVzZW50OiBjb2RlL3J1bl9zb3J0aW5nX3N3ZWVwLnNoLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAwOSI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiNCBob3N0LXNwZWNpZmljIGFic29sdXRlIHBhdGgocykgaW4gNCBzY3JpcHQocykgb3IgY29uZmlnKHMpLCBlLmcuIGNvZGUvcGFydGlhbF9yZXBvcnQuc2ggbGluZSA0NzogL2RhdGEveW9oL2NvbXByZXNzaW9uLWNvbXBhcmlzb25zLy5zcGVjaWZ5L3NwZWNzL3BhcGVyLXJlZmVyZW5jZS1sb3NzbGVzcy5jc3YifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTAiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IjMgdHJhY2tlZCBzY3JpcHQocykgcmVxdWlyZSBhIHRvb2wgdG8gYmUgaW5zdGFsbGVkIG9uIHRoZSBob3N0IGFscmVhZHksIGUuZy4gY29kZS9ydW5fc29ydGluZ19sb29wLnNoIGxpbmUgMjAgKHNlZSBsaW5lKTsgdGhhdCBkZXBlbmRlbmN5IGlzIG5vdCBpbiBhbnkgdHJhY2tlZCBzcGVjaWZpY2F0aW9uLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAxMSI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiUkVBRE1FIGRvY3VtZW50cyB0aGUgcGF0Y2hlZCBkYXRhbGFkLCB0aGUgY21ha2UgZmxhZyBhbmQgdGhlIEdQVSwgYnV0IG5vdCB0aGUgL2RhdGEgbW91bnQgdGhlIHNvcnRpbmcgZW50cnkgcG9pbnRzIHJlcXVpcmUsIHdoaWNoIGlzIHRoZSBhc3N1bXB0aW9uIHRoYXQgYWN0dWFsbHkgYnJlYWtzIGVsc2V3aGVyZS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTIiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IlJFQURNRSBsaXN0cyB0aGUgaW5zdGFsbCBzdGVwcywgYnV0IG5vIHRyYWNrZWQgc3BlYyBuYW1lcyB2ZXJzaW9uczogd2F2cGFjay1udW1jb2RlY3MgYW5kIGZsYWMtbnVtY29kZWNzIGFyZSB1bnBpbm5lZCBhbmQgdGhlIGRhdGFsYWQgYnVpbGQgaXMgcHJvc2UuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDEzIjp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJObyBzcGVjaWZpY2F0aW9uIGluIHRoaXMgb2JqZWN0OyBpdCBtYXkgYmUgaW5zaWRlIHRoZSBtb2R1bGUocykgbm90IGluc3RhbGxlZCBoZXJlOiBjb2RlL2NvbXByZXNzaW9uLWNvbXBhcmlzb25zLXRvb2xzLCBzb3VyY2VkYXRhL2FpbmQtZXBoeXMtY29tcHJlc3Npb24uIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDE0Ijp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJBIHRyYWNrZWQgdXBkYXRlIHByb2Nlc3MgZXhpc3RzIGZvciB0aGUgcGlucyAoMTYgJ1BpbiB0aGUgdG9vbCB0byAuLi4nIGNvbW1pdHMpLCBidXQgbm90IGZvciBhbiBlbnZpcm9ubWVudCBzcGVjaWZpY2F0aW9uLCBiZWNhdXNlIHRoZSBvYmplY3QgaGFzIG5vbmUuIFNhbWUgc2VudGVuY2UgYXMgc2hvdWxkLzAwOC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTUiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IlRoZSBydW4gcmVjb3JkcyBjYXB0dXJlIHRoZSBlbnZpcm9ubWVudCBidXQgbm90aGluZyBwaW5zIG9uZTogdGhlcmUgaXMgbm8gaW1hZ2UgZGlnZXN0IG9yIGZyb3plbiBtYW5pZmVzdCBhbm90aGVyIHBlcnNvbiBjb3VsZCByZXBsaWNhdGUgZnJvbS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTYiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6Ik5vdGhpbmcgdG8gb2J0YWluOiBubyBsb2NrZmlsZSwgaW1hZ2Ugb3IgZnJvemVuIG1hbmlmZXN0IGlzIHB1Ymxpc2hlZCBhbnl3aGVyZSwgYW5kIHRoZSBkb2N1bWVudGVkIHJvdXRlIHJlYnVpbGRzIGZyb20gaG9zdCB0b29scy4gUHJvYmUgaGVkZ2VkIG9uIHRoZSB1bmluc3RhbGxlZCBtb2R1bGVzOyB0aGUgc2NyaXB0cyBzZXR0bGUgaXQuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDE3Ijp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJSRUFETUUncyAnUmVwcm9kdWNpbmcnIGdpdmVzIHJ1bm5hYmxlIHV2L2NtYWtlIHN0ZXBzIGFuZCB0aGUgaW5zdGFsbC1hZnRlci1waW4gcnVsZSwgYnV0IHRoZXJlIGlzIG5vIHNwZWNpZmljYXRpb24gdG8gb2J0YWluLCBzbyB0aGUgZG9jdW1lbnRhdGlvbiBjYW5ub3QgcG9pbnQgYXQgb25lLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDpzaG91bGQvMDAxIjp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiZ2l0IHBsdXMgZ2l0LWFubmV4IHRocm91Z2ggRGF0YUxhZCBhY3Jvc3MgdGhlIHN1cGVyZGF0YXNldCBhbmQgYm90aCBsaW5rZWQgbW9kdWxlczsgMTM0MDcgYW5uZXhlZCBwb2ludGVycyBhbmQgbm8gc2Vjb25kIHN5c3RlbS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwMiI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiTm8gQ0kgY29uZmlndXJhdGlvbjogbm90aGluZyBjaGVja3MgdGhhdCB0aGUgaW5zdHJ1Y3Rpb25zIHN0aWxsIHdvcmsuIn0sInN0YW1wZWQtY2hlY2tsaXN0OnNob3VsZC8wMDMiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiIzIGtpbmRzIG9mIGNvbXBvbmVudCBsaXZlIGluIGRpc3RpbmN0IHBsYWNlczogaW5wdXRzIGluIHNvdXJjZWRhdGEsIHNvdXJjZWRhdGEvYWluZC1lcGh5cy1jb21wcmVzc2lvbjsgY29kZSBpbiBjb2RlOyBkZXJpdmVkIGluIGRlcml2YXRpdmVzIn0sInN0YW1wZWQtY2hlY2tsaXN0OnNob3VsZC8wMDkiOnsidmFsdWUiOm51bGwsInJlYXNvbiI6Ik4vQSwgZW1wdHkgc3ViamVjdDogZXZlcnkgY29tcG9uZW50IGlzIHB1YmxpYyAoQUlORCBvcGVuIGRhdGEgb24gdGhlIEFXUyByZWdpc3RyeSwgTUlUIGNvZGUpLCBzbyB0aGVyZSBhcmUgbm8gcmVzdHJpY3RlZCBkYXRhIG9yIHNvZnR3YXJlIHRvIGlzb2xhdGUuIn0sInN0YW1wZWQtY2hlY2tsaXN0OnNob3VsZC8wMDQiOnsidmFsdWUiOm51bGwsInJlYXNvbiI6Ik5vdGhpbmcgaW4gdGhlIG9iamVjdCByZWNvcmRzIGEgZnJlc2gtZW52aXJvbm1lbnQgcmVydW4sIGFuZCBhdHRlbXB0aW5nIG9uZSBuZWVkcyA1MjMgR0Igb2YgaW5wdXQgYW5kIGEgR1BVLiBmcmVzaF9yZXJ1bi5weSB3YXMgbm90IHJ1bi4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwNSI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiT25lIGxvbmctbGl2ZWQgdmVudiAoZW52cy9jb21wYmVuY2gpIGlzIHJldXNlZCBhY3Jvc3MgdGhlIHdob2xlIHN3ZWVwIGJ5IGRlc2lnbjsgZHVjdCByZWNvcmRzIGVhY2ggcnVuIGJ1dCBkb2VzIG5vdCBpc29sYXRlIGl0LiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDpzaG91bGQvMDA2Ijp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJObyBDSSBjb25maWd1cmF0aW9uOiBub3RoaW5nIGNoZWNrcyB0aGF0IHRoZSBpbnN0cnVjdGlvbnMgc3RpbGwgd29yay4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwNyI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiTm8gZW52aXJvbm1lbnQgYXJ0aWZhY3QgaXMgYXJjaGl2ZWQgd2l0aCB0aGUgb2JqZWN0OiB0aGUgdmVudiBpcyBnaXRpZ25vcmVkIGFuZCBubyBjb250YWluZXIgaW1hZ2Ugb3IgYnVpbHQgYmluYXJ5IGlzIGtlcHQuIn0sInN0YW1wZWQtY2hlY2tsaXN0OnNob3VsZC8wMDgiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IldvcmQtZm9yLXdvcmQgdGhlIHNhbWUgcXVlc3Rpb24gYXMgbXVzdC8wMTQsIGF0IGEgZGlmZmVyZW50IGxldmVsOyBhbnN3ZXJlZCBmcm9tIHRoZSBzYW1lIGV2aWRlbmNlLiBUaGUgcGlucyBoYXZlIGEgdHJhY2tlZCB1cGRhdGUgcHJvY2VzcywgdGhlIGFic2VudCBlbnZpcm9ubWVudCBzcGVjIGNhbm5vdC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bWF5LzAwMSI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IjIgZXh0ZXJuYWwgY29tcG9uZW50KHMpIGFyZSBsaW5rZWQgYXMgbW9kdWxlczogY29kZS9jb21wcmVzc2lvbi1jb21wYXJpc29ucy10b29scywgc291cmNlZGF0YS9haW5kLWVwaHlzLWNvbXByZXNzaW9uIn0sInN0YW1wZWQtY2hlY2tsaXN0Om1heS8wMDIiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJUaGUgbW9kdWxhciBzdHJ1Y3R1cmUgaXMgZG9jdW1lbnRlZCB0d2ljZTogdGhlIFJFQURNRSdzIExheW91dCBzZWN0aW9uIGFuZCBkYXRhc2V0X2Rlc2NyaXB0aW9uLmpzb24ncyBMYXlvdXQsIFNvdXJjZURhdGFzZXRzIGFuZCBHZW5lcmF0ZWRCeSBmaWVsZHMuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om1heS8wMDMiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJUaGUgdG9vbCBib3VuZGFyeSBpcyBlbmZvcmNlZCByYXRoZXIgdGhhbiBkZWNsYXJlZDogcnVuX3N3ZWVwLnNoIHJlZnVzZXMgYSBkcmlmdGVkIG9yIGRpcnR5IHRvb2wgY2hlY2tvdXQsIGFuZCBzb3VyY2VkYXRhIGlzIGRvY3VtZW50ZWQgYXMgbmV2ZXIgbW9kaWZpZWQuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om1heS8wMDQiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJDb21wb3NpdGlvbiBpcyBnaXQgc3VibW9kdWxlcyB1bmRlciBEYXRhTGFkLCB3aXRoIHRoZSBleGFjdCBjbG9uZSBhbmQgZ2V0IGNvbW1hbmRzIGdpdmVuIGluIHRoZSBSRUFETUUuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om1heS8wMDUiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJOYXZpZ2F0aW9uIGlzIGRvY3VtZW50ZWQgYXQgdHdvIGxldmVsczogdGhlIExheW91dCBzZWN0aW9ucywgYW5kIGEgUkVBRE1FIGluIGVhY2ggZGVyaXZhdGl2ZXMvcmVwb3J0cy0qIGRpcmVjdG9yeS4ifX19)

Produced by `assess-alignment-with-stamped-principles` with
`stamped-conventions`, both at this commit — labelled `0.2.0` while in
development, and `0.1.0` as shipped, because #16's counting rule starts at the
first merge. The run records under `../../blind-runs/` keep the labels they
carried when they ran. Checklist 0.3.1
(`stamped-checklist-schema@v0.3.1`, `af259ba`), on
<https://github.com/dandi/compression-comparisons-t261-study> at commit
`f2f0802449095025b589337f8cb6f13be5112b25`, 2026-10-13, claude-code (cloud
session) / claude-opus-5[1m].
Probe output: [`probes.json`](probes.json); response: [`response.json`](response.json);
URL: [`checklist-url.txt`](checklist-url.txt).
Scope: committed state of the superdataset only; the two linked modules were
not installed, no container was pulled, and no rerun was attempted.
