# STAMPED assessment: dandi/compression-comparisons-t261-study

**Object:** <https://github.com/dandi/compression-comparisons-t261-study> at commit `f2f0802`
**Kind:** study (a BIDS derivative dataset with its own compute)
**Checklist:** 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`)
**Date:** 2026-10-13

MUST: 6 met / 7 partial / 4 unmet (of 17)
SHOULD: 1 met / 5 unmet / 2 not-checked / 1 not-applicable (of 9)
MAY: 5 met (of 5)

No single overall score: a MUST at `partial` is a MUST failure, and `not-checked`
is reported apart from `unmet` throughout.

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
   public `dandi/compression-comparisons` URL closes **must/002** and
   **must/016**, and is the single highest-leverage change in this object:
   everything else is reproducible *in principle* and this is what stops it in
   practice.
2. **Ship an environment specification, not only instructions.**
   The README tells a reader how to build `envs/compbench`, but nothing pins
   what ends up in it: the extras (`wavpack-numcodecs`, `flac-numcodecs`) are
   unpinned, the patched datalad is prose, and the venv is gitignored. A
   tracked `uv pip freeze` / `uv.lock` plus the datalad build reference would
   close **must/012**, **must/014**, **must/015**, **must/017**,
   **should/007** and **should/008** at once, and lift **must/010** and
   **must/013** out of `partial`. For a study whose central claim is a
   *reproduction*, this is the gap that matters most after (1).
3. **Record the sweep-level aggregates.**
   1218 of 22286 derived files — `AUTO_TABLE.md`, `RESULTS.md`, the duct
   traces of aggregate steps — were last touched by an ordinary commit rather
   than a run record, which the README already names as a known gap ("no
   sweep-level run record"). A recorded aggregation step would move
   **must/006** to `met`; the per-cell provenance is already there.
4. **Add CI that rebuilds the environment and re-runs one cheap cell.**
   There is no CI configuration at all, so nothing catches the instructions
   drifting from the object (**should/002**, **should/006**), and the
   environment has never been shown to rebuild from what is published.
5. **Move the oversized duct logs into the annex.**
   22 `duct-usage.jsonl` files exceed 10 MiB in git (largest 11 MiB), so every
   clone carries them in full before any `datalad get`. They are text, which
   is why `-c text2git` keeps them in git, and why this is **must/005**
   `partial` rather than `unmet`.

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
- **A clean tree and a documented layout.** `git status` is empty, and the
  layout is described twice (README and `dataset_description.json`) for
  readers and for machines.

## Per item

| item | principles | status | evidence | reason |
|---|---|---|---|---|
| `must/001` | S.1 | **met** | `.datalad/config`; `dataset_description.json#Layout` | One DataLad dataset root holds code, inputs (as subdatasets) and every derivative; nothing essential sits outside it. |
| `must/002` | S.1 | **unmet** | `.gitmodules` | 1 of 2 linked module(s) do not resolve elsewhere: code/compression-comparisons-tools url=../.. — relative url: resolves only next to this superdataset |
| `must/003` | S.1 | **met** | `.gitmodules`; `README.md#Reproducing` | The benchmark tool is a pinned submodule and the BWC codec is built from source inside it; nothing is assumed preinstalled. |
| `must/004` | T.1, T.3, T.5 | **met** | `git status --porcelain` | git status is empty, including submodules: the committed state is the whole state. |
| `must/005` | T.1, T.3, T.5 | **partial** | `derivatives/compbench-2026-08-22-paper-real-np1-8-general/aind-634569-lsbbp__blosc-zlib-level_9-shuffle_byte-chunk1s/duct-usage.jsonl`; `derivatives/compbench-2026-08-22-paper-real-np1-8-general/aind-634569-lsbbp__gzip-level_9-shuffle_byte-chunk1s/duct-usage.jsonl`; `derivatives/compbench-2026-08-22-paper-real-np1-8-general/aind-634568-lsbbp__gzip-level_9-shuffle_byte-chunk1s/duct-usage.jsonl` | No large binary in git, but 22 text blob(s) exceed 10 MiB (largest derivatives/compbench-2026-08-22-paper-real-np1-8-general/aind-634569-lsbbp__blosc-zlib-level_9-shuffle_byte-chunk1s/duct-usage.jsonl, 11 MiB) — every clone carries them in full. |
| `must/006` | T.1, T.3, T.5 | **partial** | `derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/AUTO_TABLE.md`; `derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/RESULTS.md`; `derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/aind-ibl-np1-CSHZAD026-slice10__blosc-lz4-level_3-shuffle_byte/duct-info.json` | 1218 of 22286 derived file(s) have no re-executable record, e.g. derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/AUTO_TABLE.md; last touched by an ordinary commit. |
| `must/007` | A.1 | **met** | `README.md`; `code/run_sorting_sweep.sh`; `code/run_sweep.sh` | README.md has an install/usage/reproduce section. |
| `must/008` | A.1 | **met** | `README.md`; `code/run_sorting_sweep.sh`; `code/run_sweep.sh` | Starting point present: code/run_sorting_sweep.sh. |
| `must/009` | P.1 | **partial** | `code/run_sorting_sweep.sh#L76`; `derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/aind-ibl-np1-CSHZAD026-slice10__blosc-lz4-level_3-shuffle_byte/duct-info.json#L1`; `derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/aind-ibl-np1-CSHZAD026-slice10__blosc-lz4-level_9-shuffle_byte/duct-info.json#L1` | No script depends on a home path, but 99 host-path mention(s) remain: 98 of them in recorded run output, which is provenance rather than a script |
| `must/010` | P.1 | **partial** | `code/compression-comparisons-tools`; `sourcedata/aind-ephys-compression` | No environment specification in this object; it may be inside the module(s) that are not installed here: code/compression-comparisons-tools, sourcedata/aind-ephys-compression. |
| `must/011` | P.1 | **met** | `README.md` | README names the host assumptions: a patched datalad (gh-7899/7900), a C++ toolchain with -Wno-restrict, and a GPU for Kilosort 4. |
| `must/012` | P.2 | **partial** | `README.md#Reproducing`; `probe:env-spec-tracked` | README lists the install steps, but no tracked spec names versions: wavpack-numcodecs and flac-numcodecs are unpinned and the datalad build is prose. |
| `must/013` | P.3 | **partial** | `code/compression-comparisons-tools`; `sourcedata/aind-ephys-compression` | No environment specification in this object; it may be inside the module(s) that are not installed here: code/compression-comparisons-tools, sourcedata/aind-ephys-compression. |
| `must/014` | P.3 | **unmet** | `README.md`; `.gitignore` | No environment specification exists here to update, and no process for updating one is documented; the pin guard covers the tool commit, not the environment. |
| `must/015` | D.1 | **unmet** | `commit:7733465`; `commit:13f2689`; `commit:37d7125` | The run records capture the environment but nothing pins one: there is no image digest or frozen manifest another person could replicate from. |
| `must/016` | D.1 | **unmet** | `.gitmodules` | 1 of 2 linked module(s) do not resolve elsewhere: code/compression-comparisons-tools url=../.. — relative url: resolves only next to this superdataset |
| `must/017` | D.1 | **partial** | `README.md#Reproducing` | README says how to build the environment, but there is no specification to obtain: no lockfile, image or frozen manifest is published with the object. |
| `should/001` | T.2 | **met** | `.gitattributes`; `.gitmodules` | git plus git-annex through DataLad across the superdataset and both linked modules. |
| `should/002` | A.2 | **unmet** | `probe:ci-present` | No CI configuration: nothing checks that the instructions still work. |
| `should/003` | M.1 | **not-checked** | `git submodule status`; `git submodule status` | 2 of 2 module(s) are not installed here, so their state cannot be read: code/compression-comparisons-tools, sourcedata/aind-ephys-compression |
| `should/009` | M.4 | **not-applicable** | — | N/A: every component is public (AIND open data, MIT code); there are no restricted data or software to isolate. |
| `should/004` | E.1 | **not-checked** | — | Nothing in the object records a fresh-environment rerun, and attempting one here needs 523 GB of inputs and a GPU. fresh_rerun.py was not run. |
| `should/005` | E.1 | **unmet** | `README.md`; `probe:run-env-linked` | One long-lived venv (envs/compbench) is reused across the whole sweep by design; duct records each run but does not isolate it. |
| `should/006` | D.2 | **unmet** | `probe:ci-present` | No CI configuration: nothing checks that the instructions still work. |
| `should/007` | D.2 | **unmet** | `.gitignore`; `probe:env-spec-tracked` | No environment artifact is archived with the object: the venv is gitignored and no container image or binary is kept. |
| `should/008` | D.2 | **unmet** | `README.md` | Same gap as must/014: no tracked environment specification, so no updates to it are tracked either. |
| `may/001` | M.2 | **met** | `.gitmodules` | 2 external component(s) are linked as modules: code/compression-comparisons-tools, sourcedata/aind-ephys-compression |
| `may/002` | M.2 | **met** | `README.md#Layout`; `dataset_description.json` | The modular structure is documented twice: the README's Layout section and dataset_description.json's Layout and SourceDatasets fields. |
| `may/003` | M.2 | **met** | `README.md#Layout`; `dataset_description.json` | Modules update independently: the tool submodule is pinned and run_sweep.sh refuses a drifted or dirty checkout; sourcedata is never modified. |
| `may/004` | M.2 | **met** | `README.md#Reproducing` | Composition is by git submodules and datalad clone/get, with the exact commands given. |
| `may/005` | M.2 | **met** | `README.md#Layout` | Navigation is documented: the Layout sections plus a README in each derivatives/reports-* directory. |

## Not checked

- `should/003` — 2 of 2 module(s) are not installed here, so their state cannot be read: code/compression-comparisons-tools, sourcedata/aind-ephys-compression
- `should/004` — Nothing in the object records a fresh-environment rerun, and attempting one here needs 523 GB of inputs and a GPU. fresh_rerun.py was not run.

Neither is `unmet`: the first needs the modules installed, the second needs
523 GB of input and a GPU. `scripts/fresh_rerun.py` was not run.

## Outside the checklist

- **Licensing (paper S.2/D.3, no checklist item in 0.3.1):** `partial` —
  `dataset_description.json` states MIT for code and derivatives, but no
  `LICENSE` file, `LICENSES/` directory or `REUSE.toml` makes it
  machine-readable.
- **T.4, code-driven provenance (in principles 0.2.0, no checklist item):**
  `met` — see the run records above.

## Open the answers

[Open this assessment in the checklist app](https://checklist.stamped-principles.org/?checklist=0.3.1&responses_version=0.3.1&cols=auto&sections=off&format=3&responses=eyJjaGVja2xpc3RfdmVyc2lvbiI6IjAuMy4xIiwicmVzcG9uc2VzIjp7InN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDAxIjp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiT25lIERhdGFMYWQgZGF0YXNldCByb290IGhvbGRzIGNvZGUsIGlucHV0cyAoYXMgc3ViZGF0YXNldHMpIGFuZCBldmVyeSBkZXJpdmF0aXZlOyBub3RoaW5nIGVzc2VudGlhbCBzaXRzIG91dHNpZGUgaXQuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDAyIjp7InZhbHVlIjoibm8iLCJyZWFzb24iOiIxIG9mIDIgbGlua2VkIG1vZHVsZShzKSBkbyBub3QgcmVzb2x2ZSBlbHNld2hlcmU6IGNvZGUvY29tcHJlc3Npb24tY29tcGFyaXNvbnMtdG9vbHMgdXJsPS4uLy4uIOKAlCByZWxhdGl2ZSB1cmw6IHJlc29sdmVzIG9ubHkgbmV4dCB0byB0aGlzIHN1cGVyZGF0YXNldCJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAwMyI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IlRoZSBiZW5jaG1hcmsgdG9vbCBpcyBhIHBpbm5lZCBzdWJtb2R1bGUgYW5kIHRoZSBCV0MgY29kZWMgaXMgYnVpbHQgZnJvbSBzb3VyY2UgaW5zaWRlIGl0OyBub3RoaW5nIGlzIGFzc3VtZWQgcHJlaW5zdGFsbGVkLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAwNCI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6ImdpdCBzdGF0dXMgaXMgZW1wdHksIGluY2x1ZGluZyBzdWJtb2R1bGVzOiB0aGUgY29tbWl0dGVkIHN0YXRlIGlzIHRoZSB3aG9sZSBzdGF0ZS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMDUiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6Ik5vIGxhcmdlIGJpbmFyeSBpbiBnaXQsIGJ1dCAyMiB0ZXh0IGJsb2IocykgZXhjZWVkIDEwIE1pQiAobGFyZ2VzdCBkZXJpdmF0aXZlcy9jb21wYmVuY2gtMjAyNi0wOC0yMi1wYXBlci1yZWFsLW5wMS04LWdlbmVyYWwvYWluZC02MzQ1NjktbHNiYnBfX2Jsb3NjLXpsaWItbGV2ZWxfOS1zaHVmZmxlX2J5dGUtY2h1bmsxcy9kdWN0LXVzYWdlLmpzb25sLCAxMSBNaUIpIOKAlCBldmVyeSBjbG9uZSBjYXJyaWVzIHRoZW0gaW4gZnVsbC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMDYiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IjEyMTggb2YgMjIyODYgZGVyaXZlZCBmaWxlKHMpIGhhdmUgbm8gcmUtZXhlY3V0YWJsZSByZWNvcmQsIGUuZy4gZGVyaXZhdGl2ZXMvY29tcGJlbmNoLTIwMjYtMDgtMTktQ1NIWkFEMDI2LXNsaWNlMTBzLWJhbmRwYXNzL0FVVE9fVEFCTEUubWQ7IGxhc3QgdG91Y2hlZCBieSBhbiBvcmRpbmFyeSBjb21taXQuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDA3Ijp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiUkVBRE1FLm1kIGhhcyBhbiBpbnN0YWxsL3VzYWdlL3JlcHJvZHVjZSBzZWN0aW9uLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAwOCI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IlN0YXJ0aW5nIHBvaW50IHByZXNlbnQ6IGNvZGUvcnVuX3NvcnRpbmdfc3dlZXAuc2guIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDA5Ijp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJObyBzY3JpcHQgZGVwZW5kcyBvbiBhIGhvbWUgcGF0aCwgYnV0IDk5IGhvc3QtcGF0aCBtZW50aW9uKHMpIHJlbWFpbjogOTggb2YgdGhlbSBpbiByZWNvcmRlZCBydW4gb3V0cHV0LCB3aGljaCBpcyBwcm92ZW5hbmNlIHJhdGhlciB0aGFuIGEgc2NyaXB0In0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDEwIjp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJObyBlbnZpcm9ubWVudCBzcGVjaWZpY2F0aW9uIGluIHRoaXMgb2JqZWN0OyBpdCBtYXkgYmUgaW5zaWRlIHRoZSBtb2R1bGUocykgdGhhdCBhcmUgbm90IGluc3RhbGxlZCBoZXJlOiBjb2RlL2NvbXByZXNzaW9uLWNvbXBhcmlzb25zLXRvb2xzLCBzb3VyY2VkYXRhL2FpbmQtZXBoeXMtY29tcHJlc3Npb24uIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDExIjp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiUkVBRE1FIG5hbWVzIHRoZSBob3N0IGFzc3VtcHRpb25zOiBhIHBhdGNoZWQgZGF0YWxhZCAoZ2gtNzg5OS83OTAwKSwgYSBDKysgdG9vbGNoYWluIHdpdGggLVduby1yZXN0cmljdCwgYW5kIGEgR1BVIGZvciBLaWxvc29ydCA0LiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAxMiI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiUkVBRE1FIGxpc3RzIHRoZSBpbnN0YWxsIHN0ZXBzLCBidXQgbm8gdHJhY2tlZCBzcGVjIG5hbWVzIHZlcnNpb25zOiB3YXZwYWNrLW51bWNvZGVjcyBhbmQgZmxhYy1udW1jb2RlY3MgYXJlIHVucGlubmVkIGFuZCB0aGUgZGF0YWxhZCBidWlsZCBpcyBwcm9zZS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTMiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6Ik5vIGVudmlyb25tZW50IHNwZWNpZmljYXRpb24gaW4gdGhpcyBvYmplY3Q7IGl0IG1heSBiZSBpbnNpZGUgdGhlIG1vZHVsZShzKSB0aGF0IGFyZSBub3QgaW5zdGFsbGVkIGhlcmU6IGNvZGUvY29tcHJlc3Npb24tY29tcGFyaXNvbnMtdG9vbHMsIHNvdXJjZWRhdGEvYWluZC1lcGh5cy1jb21wcmVzc2lvbi4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTQiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6Ik5vIGVudmlyb25tZW50IHNwZWNpZmljYXRpb24gZXhpc3RzIGhlcmUgdG8gdXBkYXRlLCBhbmQgbm8gcHJvY2VzcyBmb3IgdXBkYXRpbmcgb25lIGlzIGRvY3VtZW50ZWQ7IHRoZSBwaW4gZ3VhcmQgY292ZXJzIHRoZSB0b29sIGNvbW1pdCwgbm90IHRoZSBlbnZpcm9ubWVudC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTUiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IlRoZSBydW4gcmVjb3JkcyBjYXB0dXJlIHRoZSBlbnZpcm9ubWVudCBidXQgbm90aGluZyBwaW5zIG9uZTogdGhlcmUgaXMgbm8gaW1hZ2UgZGlnZXN0IG9yIGZyb3plbiBtYW5pZmVzdCBhbm90aGVyIHBlcnNvbiBjb3VsZCByZXBsaWNhdGUgZnJvbS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTYiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IjEgb2YgMiBsaW5rZWQgbW9kdWxlKHMpIGRvIG5vdCByZXNvbHZlIGVsc2V3aGVyZTogY29kZS9jb21wcmVzc2lvbi1jb21wYXJpc29ucy10b29scyB1cmw9Li4vLi4g4oCUIHJlbGF0aXZlIHVybDogcmVzb2x2ZXMgb25seSBuZXh0IHRvIHRoaXMgc3VwZXJkYXRhc2V0In0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDE3Ijp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJSRUFETUUgc2F5cyBob3cgdG8gYnVpbGQgdGhlIGVudmlyb25tZW50LCBidXQgdGhlcmUgaXMgbm8gc3BlY2lmaWNhdGlvbiB0byBvYnRhaW46IG5vIGxvY2tmaWxlLCBpbWFnZSBvciBmcm96ZW4gbWFuaWZlc3QgaXMgcHVibGlzaGVkIHdpdGggdGhlIG9iamVjdC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwMSI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6ImdpdCBwbHVzIGdpdC1hbm5leCB0aHJvdWdoIERhdGFMYWQgYWNyb3NzIHRoZSBzdXBlcmRhdGFzZXQgYW5kIGJvdGggbGlua2VkIG1vZHVsZXMuIn0sInN0YW1wZWQtY2hlY2tsaXN0OnNob3VsZC8wMDIiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6Ik5vIENJIGNvbmZpZ3VyYXRpb246IG5vdGhpbmcgY2hlY2tzIHRoYXQgdGhlIGluc3RydWN0aW9ucyBzdGlsbCB3b3JrLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDpzaG91bGQvMDAzIjp7InZhbHVlIjpudWxsLCJyZWFzb24iOiIyIG9mIDIgbW9kdWxlKHMpIGFyZSBub3QgaW5zdGFsbGVkIGhlcmUsIHNvIHRoZWlyIHN0YXRlIGNhbm5vdCBiZSByZWFkOiBjb2RlL2NvbXByZXNzaW9uLWNvbXBhcmlzb25zLXRvb2xzLCBzb3VyY2VkYXRhL2FpbmQtZXBoeXMtY29tcHJlc3Npb24ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwOSI6eyJ2YWx1ZSI6bnVsbCwicmVhc29uIjoiTi9BOiBldmVyeSBjb21wb25lbnQgaXMgcHVibGljIChBSU5EIG9wZW4gZGF0YSwgTUlUIGNvZGUpOyB0aGVyZSBhcmUgbm8gcmVzdHJpY3RlZCBkYXRhIG9yIHNvZnR3YXJlIHRvIGlzb2xhdGUuIn0sInN0YW1wZWQtY2hlY2tsaXN0OnNob3VsZC8wMDQiOnsidmFsdWUiOm51bGwsInJlYXNvbiI6Ik5vdGhpbmcgaW4gdGhlIG9iamVjdCByZWNvcmRzIGEgZnJlc2gtZW52aXJvbm1lbnQgcmVydW4sIGFuZCBhdHRlbXB0aW5nIG9uZSBoZXJlIG5lZWRzIDUyMyBHQiBvZiBpbnB1dHMgYW5kIGEgR1BVLiBmcmVzaF9yZXJ1bi5weSB3YXMgbm90IHJ1bi4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwNSI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiT25lIGxvbmctbGl2ZWQgdmVudiAoZW52cy9jb21wYmVuY2gpIGlzIHJldXNlZCBhY3Jvc3MgdGhlIHdob2xlIHN3ZWVwIGJ5IGRlc2lnbjsgZHVjdCByZWNvcmRzIGVhY2ggcnVuIGJ1dCBkb2VzIG5vdCBpc29sYXRlIGl0LiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDpzaG91bGQvMDA2Ijp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJObyBDSSBjb25maWd1cmF0aW9uOiBub3RoaW5nIGNoZWNrcyB0aGF0IHRoZSBpbnN0cnVjdGlvbnMgc3RpbGwgd29yay4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwNyI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiTm8gZW52aXJvbm1lbnQgYXJ0aWZhY3QgaXMgYXJjaGl2ZWQgd2l0aCB0aGUgb2JqZWN0OiB0aGUgdmVudiBpcyBnaXRpZ25vcmVkIGFuZCBubyBjb250YWluZXIgaW1hZ2Ugb3IgYmluYXJ5IGlzIGtlcHQuIn0sInN0YW1wZWQtY2hlY2tsaXN0OnNob3VsZC8wMDgiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IlNhbWUgZ2FwIGFzIG11c3QvMDE0OiBubyB0cmFja2VkIGVudmlyb25tZW50IHNwZWNpZmljYXRpb24sIHNvIG5vIHVwZGF0ZXMgdG8gaXQgYXJlIHRyYWNrZWQgZWl0aGVyLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptYXkvMDAxIjp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiMiBleHRlcm5hbCBjb21wb25lbnQocykgYXJlIGxpbmtlZCBhcyBtb2R1bGVzOiBjb2RlL2NvbXByZXNzaW9uLWNvbXBhcmlzb25zLXRvb2xzLCBzb3VyY2VkYXRhL2FpbmQtZXBoeXMtY29tcHJlc3Npb24ifSwic3RhbXBlZC1jaGVja2xpc3Q6bWF5LzAwMiI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IlRoZSBtb2R1bGFyIHN0cnVjdHVyZSBpcyBkb2N1bWVudGVkIHR3aWNlOiB0aGUgUkVBRE1FJ3MgTGF5b3V0IHNlY3Rpb24gYW5kIGRhdGFzZXRfZGVzY3JpcHRpb24uanNvbidzIExheW91dCBhbmQgU291cmNlRGF0YXNldHMgZmllbGRzLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptYXkvMDAzIjp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiTW9kdWxlcyB1cGRhdGUgaW5kZXBlbmRlbnRseTogdGhlIHRvb2wgc3VibW9kdWxlIGlzIHBpbm5lZCBhbmQgcnVuX3N3ZWVwLnNoIHJlZnVzZXMgYSBkcmlmdGVkIG9yIGRpcnR5IGNoZWNrb3V0OyBzb3VyY2VkYXRhIGlzIG5ldmVyIG1vZGlmaWVkLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptYXkvMDA0Ijp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiQ29tcG9zaXRpb24gaXMgYnkgZ2l0IHN1Ym1vZHVsZXMgYW5kIGRhdGFsYWQgY2xvbmUvZ2V0LCB3aXRoIHRoZSBleGFjdCBjb21tYW5kcyBnaXZlbi4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bWF5LzAwNSI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6Ik5hdmlnYXRpb24gaXMgZG9jdW1lbnRlZDogdGhlIExheW91dCBzZWN0aW9ucyBwbHVzIGEgUkVBRE1FIGluIGVhY2ggZGVyaXZhdGl2ZXMvcmVwb3J0cy0qIGRpcmVjdG9yeS4ifX19)

Produced by `assess-alignment-with-stamped-principles` 0.1.0 with
`stamped-conventions` 0.1.0, checklist 0.3.1
(`stamped-checklist-schema@v0.3.1`, `af259ba`), on
<https://github.com/dandi/compression-comparisons-t261-study> at commit
`f2f0802449095025b589337f8cb6f13be5112b25`, 2026-10-13, claude-code (cloud
session) / claude-opus-5[1m].
Probe output: [`probes.json`](probes.json); response: [`response.json`](response.json).
Scope: committed state of the superdataset only; the two linked modules were
not installed, no container was pulled, and no rerun was attempted.
