# STAMPED assessment — `dandi/compression-comparisons-t261-study`

Object: <https://github.com/dandi/compression-comparisons-t261-study> at commit
`f2f0802449095025b589337f8cb6f13be5112b25` (working tree clean; both submodules
uninstalled). Checklist 0.3.1. Assessed 2026-10-13.

## Verdict

| level | met | partial | unmet | not-checked | not-applicable | denominator |
| ----- | --: | ------: | ----: | ----------: | -------------: | ----------: |
| MUST   | 4 | 9 | 4 | 0 | 0 | 17 |
| SHOULD | 2 | 1 | 4 | 1 | 1 |  9 |
| MAY    | 5 | 0 | 0 | 0 | 0 |  5 |

**MUST: 4 met, 9 partial, 4 unmet, 0 not-checked (of 17).** A `partial` never
satisfies a MUST, so 13 of 17 MUST items are open. No single overall score.

The shape of the result: this study is **exceptionally strong on Tracked and
Modular** and **weak on Portable, Ephemeral and Distributable**, and almost
every weak verdict traces to one root cause — *the environment is not an object
in the dataset*. It is a venv on one host (`envs/compbench`, untracked and
absent from the clone) plus binaries at `/data/yoh/...`. Eleven of the thirteen
open MUST items would move if that single thing changed.

## What to fix first

1. **Give `code/compression-comparisons-tools` a real URL.** `.gitmodules` says
   `url = ../..`, which git resolves to `https://github.com/dandi/..` from the
   published remote — verified by registering the submodule against that remote.
   No fresh clone anywhere can `datalad get` the tool, so *nothing* downstream
   reproduces. The tool is already public at
   `https://github.com/dandi/compression-comparisons` (HTTP 200). This is a
   one-line change and commit `f5c4778` shows it was a knowing shortcut ("for
   now"). → closes **must/002**, unblocks **must/016**.

2. **Commit a frozen environment specification and name it in the run records.**
   Today the dependency set exists only as an unversioned `uv pip install`
   command in the README; `wavpack-numcodecs` and `flac-numcodecs` have no
   versions, and the venv that actually produced 912 cells is not described
   anywhere. A tracked `uv.lock` (or `uv pip freeze` output) committed per sweep,
   plus its path in the `datalad run` invocation, costs one command and is the
   difference between "the numbers are reproducible in principle" and "a stranger
   can rebuild the thing that made them". → closes **must/010**, **must/013**,
   **must/015**, **must/016**, **should/007**, **should/008**, and completes
   **must/006**, **must/014**, **must/017**.

3. **Take `/data/yoh/...` out of the three scripts that need it.**
   `code/run_sorting_sweep.sh#L48` and `code/run_sorting_loop.sh#L30` assign
   `WV=/data/yoh/compression-comparisons/vendor/wavpack` with no fallback at all,
   so on any other host `PATH` and `LD_LIBRARY_PATH` point at nothing and the
   wavpack/flac arms cannot run. `code/partial_report.sh#L47` reaches outside the
   boundary for the paper-reference CSV. Vendor those binaries into the object (or
   install them from the env spec) and move the CSV under the root. → closes
   **must/009**, completes **must/001**, **must/003**, **must/011**.

4. **Track the pre-commit guard, and add one CI job.** The README correctly
   identifies "do not commit while a sweep is in flight" as the trap that cost
   finished compute three times, and `.gitignore#L8` notes the guard was
   installed — but the guard lives in `.git/hooks/`, which no clone receives.
   The artifact that prevents the project's own worst failure is host state. A
   committed hook plus a `core.hooksPath` line, and a CI job that runs the smoke
   profile, would make it travel. → closes **should/002**, **should/006**.

5. **Give the aggregates a re-executable record.** 1218 of 22286 derived files
   have no run record — the two 2026-08-19/20 sweeps and, throughout, the
   `AUTO_TABLE.md` / `RESULTS.md` / `report.parquet` aggregates that the reports
   actually cite. The sweep-level gap is already self-documented in the README;
   the aggregates are the part a reader would most want to re-derive.
   → completes **must/006**.

## What the project already does well

- **Provenance density that is rare at this scale.** 1216 of 1265 commits are
  `[DATALAD RUNCMD]` records carrying `cmd`, `inputs`, `outputs` and `dsid`
  (`commit:7733465`), and each cell additionally writes a `manifest.json` that
  pins the BWC encoder's git sha and version, the Python version, the platform,
  the codec parameters, and the input's sha256 *and* git-annex key
  (`derivatives/compbench-2026-08-25-t261-vs-paper-codecs/aind-625749-lsb__t261-fbf3bd60-chunk10s/manifest.json`).

- **Pin discipline enforced in code, not in prose.** `code/run_sweep.sh#L69-L80`
  refuses to start if the tool submodule has drifted from the recorded gitlink or
  is dirty, and `#L29-L45` refuses a datalad that would record provenance wrongly.
  Sixteen separate `Pin the tool to …` commits show the boundary being moved
  deliberately. This is what **may/003** wants and most projects only claim.

- **Measurements treated as immutable, corrections made visible.**
  `dataset_description.json` states the rule, `cf77347` is an explicit
  `CORRECTION:` commit, `9960819` records a refuted hypothesis rather than
  deleting it, and `derivatives/reports-2026-09-23/full-matrix.md` says "nothing
  in `derivatives/reports-2026-08-29/` was modified". The README's three caveats
  and two traps are written down rather than papered over.

## Per-item results

🚩 marks an item where a reading of the object disagreed with a probe; the
disagreement is spelled out in *Probe disagreements* below.

| item | principles | status | evidence | reason | source |
| ---- | ---------- | ------ | -------- | ------ | ------ |
| `must/001` | S.1 | **partial** | code/partial_report.sh#L45-L47; code/run_sweep.sh#L26,L118; dataset_description.json | One root with inputs/code as modules, but envs/compbench is absent and untracked, partial_report.sh's only working reference CSV is under /data/yoh, and .specify/specs/ and 'the plan' are cited yet absent. | judgement |
| `must/002` | S.1 | **unmet** | .gitmodules#L1-L5; git submodule init; commit:f5c4778 | code/compression-comparisons-tools url=../.. resolves to https://github.com/dandi/.. from the published remote, so a fresh clone cannot get the tool. The tool is public; a full URL fixes it. | probe:subdatasets-resolvable |
| `must/003` | S.1 | **partial** | .gitmodules#L1-L5; README.md#L111-L114; code/run_sweep.sh#L83-L84 | compbench and the BWC encoder source are linked as one pinned submodule and built from it, but the wavpack/flac CLI binaries come from an untracked host directory and datalad is installed outside the boundary. | judgement |
| `must/004` | T.1,T.3,T.5 | **met** | git status --porcelain | git tracks code, README.md, dataset_description.json and configuration; git status is empty including submodules, so the committed state is the whole state. | probe:tree-clean |
| `must/005` | T.1,T.3,T.5 | **met** 🚩 | .gitattributes#L1-L3; probe:large-in-annex | DataLad/git-annex carries the binary content: 13407 annex pointers and no large binary blob in git. The probe's 22 >10 MiB blobs are duct-usage.jsonl resource logs - text, which this item does not cover. | probe:large-in-annex+judgement |
| `must/006` | T.1,T.3,T.5 | **partial** | commit:7733465; derivatives/compbench-2026-08-25-t261-vs-paper-codecs/aind-625749-lsb__t261-fbf3bd60-chunk10s/manifest.json; derivatives/compbench-2026-08-19-CSHZAD026-slice10s-bandpass/AUTO_TABLE.md | 1216 [DATALAD RUNCMD] records carry cmd/inputs/outputs, and each cell's manifest.json pins python, platform and the BWC sha. But 1218 derived files have no record, the 912-cell sweep has no sweep-level record, and no record pins a package set. | probe:derived-have-records+probe:run-env-linked |
| `must/007` | A.1 | **met** | README.md; code/run_sorting_sweep.sh; code/run_sweep.sh | README.md has an install/usage/reproduce section. | probe:entry-point |
| `must/008` | A.1 | **met** | code/run_sweep.sh; README.md#L98-L125 | code/run_sweep.sh is the entry point the README names, and it is present and executable; code/run_sorting_sweep.sh is the second. | probe:entry-point |
| `must/009` | P.1 | **partial** 🚩 | code/run_sorting_sweep.sh#L48; code/run_sorting_loop.sh#L30; code/run_sweep.sh#L83-L84 | Scripts are study-relative via $STUDY, but three of five hardcode a host path: run_sorting_sweep.sh#L48 and run_sorting_loop.sh#L30 set WV=/data/yoh/... unconditionally, partial_report.sh#L47 a host CSV, run_sorting_sweep.sh#L76 /tmp/sorting-gen. | probe:no-abs-paths+judgement |
| `must/010` | P.1 | **unmet** 🚩 | README.md#L106-L114; code/run_sweep.sh#L27-L40; code/run_sweep.sh#L83-L84 | No environment specification exists in this object, and the documented build relies on pre-installed tools by design: uv, cmake, a datalad built from a pinned git commit, and wavpack binaries from a host directory. | probe:env-spec-tracked+judgement |
| `must/011` | P.1 | **partial** | README.md#L80-L83; README.md#L123; code/run_sweep.sh#L83-L89 | The README documents the patched-datalad pin, the cmake flag and the Kilosort GPU, but not the OS, Python 3.13, libwavpack on PATH, TMPDIR/COMPBENCH_* variables, or the pre-commit guard it tells the reader to rely on. | judgement |
| `must/012` | P.2 | **partial** | README.md#L98-L125; README.md#L60; git ls-files | There is no system-requirements list. The 'Reproducing' block carries most of it implicitly (uv, cmake, GPU, a 523 GB input subdataset); nothing states the OS, the Python version, RAM/disk, or the wavpack dependency. | judgement |
| `must/013` | P.3 | **partial** 🚩 | git ls-tree HEAD code/compression-comparisons-tools; README.md#L108-L110; probe:env-spec-tracked | The tool is tracked as a pinned gitlink and carries its own packaging metadata one level down. The study's own dependencies are an unversioned README command line, and envs/compbench is untracked. | probe:env-spec-tracked+judgement |
| `must/014` | P.3 | **partial** | git log -- code/compression-comparisons-tools; commit:a63feb8; README.md#L127-L130 | History shows a real, tracked pin process - 16 'Pin the tool to ...' commits and a63feb8 pinning datalad - and the README states the install-after-pin rule. But there is no environment spec, so the Python dependency set has no process at all. | judgement |
| `must/015` | D.1 | **unmet** | commit:7733465; commit:13f2689; commit:37d7125 | The run records capture the environment but nothing pins one: there is no image digest or frozen manifest another person could replicate from. | probe:run-env-linked |
| `must/016` | D.1 | **unmet** 🚩 | git ls-files; .gitmodules#L1-L5; README.md#L106-L114 | No environment specification is published in any form - no image, no lockfile, no archived env file - and the tool module a rebuild needs does not resolve from a fresh clone (.gitmodules url=../..). | probe:subdatasets-resolvable+judgement |
| `must/017` | D.1 | **partial** | README.md#L98-L130; code/run_sweep.sh#L83-L84 | README 'Reproducing' gives runnable uv/cmake steps and the install-after-pin rule, but never says how to obtain the wavpack/flac binaries the run scripts put on PATH, so the documented recipe does not complete on another host. | judgement |
| `should/001` | T.2 | **met** | .datalad/config; .gitmodules; probe:large-in-annex | One system throughout: git plus git-annex under DataLad, with both external components as DataLad subdatasets. The untracked venv is the only component outside it. | probe:large-in-annex+judgement |
| `should/002` | A.2 | **unmet** | probe:ci-present | No CI configuration in 22863 tracked paths, so nothing checks the instructions; the pre-commit guard the README relies on is untracked host state too (.gitignore#L8). | probe:ci-present+judgement |
| `should/003` | M.1 | **met** 🚩 | dataset_description.json; .gitmodules; git ls-tree HEAD sourcedata/aind-ephys-compression | Raw input, code and derivatives are distinct modules: sourcedata/ is an input subdataset, code/ holds the drivers plus the tool submodule, derivatives/ is one dated directory per sweep. Could not verify the input module is unmodified. | probe:inputs-untouched+judgement |
| `should/009` | M.4 | **not-applicable** | dataset_description.json; curl -I | N/A: no restricted data or software. All three external components answer anonymously - the AIND recordings, the compbench tool and the BWC encoder repository all returned HTTP 200 on 2026-10-13. | judgement |
| `should/004` | E.1 | **not-checked** | README.md#L59-L60; README.md#L123 | Fresh rerun not attempted: it needs the 523 GB input subdataset and a GPU host. fresh_rerun.py against a published clone would settle it. | judgement |
| `should/005` | E.1 | **unmet** | code/run_sweep.sh#L48-L58; probe:run-env-linked; grep -ri docker|singularity|apptainer | Runs deliberately reuse one long-lived venv at envs/compbench; no container, batch job or per-run environment appears in the object or in any of the 1216 run records. Isolation is by a non-editable install, not a disposable environment. | judgement |
| `should/006` | D.2 | **unmet** | probe:ci-present | No CI and no rebuild test: nothing in the object ever reconstitutes the environment and checks it, and there is no spec to reconstitute from. | probe:ci-present+judgement |
| `should/007` | D.2 | **unmet** | git ls-files; README.md#L111-L114; code/run_sweep.sh#L83-L84 | No environment artifact is archived with the object: no image, no built binaries, no venv. BWC must be rebuilt with cmake and the wavpack binaries are expected to already exist on the host. | judgement |
| `should/008` | D.2 | **partial** | git log -- code/compression-comparisons-tools; probe:env-spec-tracked | Same property as must/014: the tool and datalad pins have a visible, tracked update process (16 pin commits, a63feb8), but no environment specification exists for the Python dependency set, so none can be updated. | judgement |
| `may/001` | M.2 | **met** | .gitmodules | 2 external component(s) are linked as modules: code/compression-comparisons-tools, sourcedata/aind-ephys-compression | probe:subdatasets-resolvable |
| `may/002` | M.2 | **met** | README.md#L48-L68; dataset_description.json | The modular structure is documented twice, in prose and in metadata: the README 'Layout' section and the Layout object in dataset_description.json, which says what each module is for. | judgement |
| `may/003` | M.2 | **met** | code/run_sweep.sh#L69-L80; git log -- code/compression-comparisons-tools | The tool boundary is enforced, not just declared: run_sweep.sh refuses to start if the submodule drifts from the recorded gitlink or is dirty, and 16 commits bump that pin independently of the study's own code. | judgement |
| `may/004` | M.2 | **met** | .gitmodules; README.md#L101-L104 | Composition is git submodules under DataLad: both modules are declared in .gitmodules with datalad-ids, and the README's first reproduction step is datalad clone followed by datalad get per module. | judgement |
| `may/005` | M.2 | **met** | derivatives/reports-2026-08-29/README.md; README.md#L48-L68; dataset_description.json | Navigation aids exist at two levels: the README 'Layout' and the dataset_description.json Layout for the object, and a README.md map inside the reports directory indexing the four reports. | judgement |

## Findings with no checklist item

The paper's licensing principles (S.2, M.3, D.3) have no counterpart among the 31
items, and neither does clone weight, so these are reported outside the checklist
(`extra_items` in the response JSON):

| finding | status | detail |
| ------- | ------ | ------ |
| `licence-declared` | partial | `dataset_description.json` declares `"MIT (code and derivatives)"`, but no `LICENSE`, `LICENSES/` or `REUSE.toml` exists under the root, so the terms are metadata only. |
| `clone-weight` | partial | `.gitattributes#L3` sends *every* text file to git regardless of size, so 22 `duct-usage.jsonl` resource logs of 10–12 MiB sit in git history; every clone carries them in full. |
| `ignored-but-tracked` | partial | `.gitignore` lists `.snakemake/` and `.sweep-logs/`, yet 22 000+ paths under `.snakemake/` and one `.sweep-logs/` log are already tracked, so the stated boundary between bookkeeping and results does not hold in the committed tree. |

## Not checked

One item, and one standing limit of this assessment:

- **`should/004`** — the pipeline was not run in a fresh container, batch job or
  clean VM. *What would settle it:* `fresh_rerun.py --url <published url> --entry
  './code/run_sweep.sh paper-real-np1-8-general'` on a throwaway host. It was not
  attempted here: the sweep needs the 523 GB input subdataset
  (`README.md#L59-L60`) and the sorting arm needs a GPU for Kilosort 4
  (`README.md#L123`), and the user did not consent to that cost.
- **Both submodules are uninstalled in the assessed clone**, so nothing inside
  `code/compression-comparisons-tools` or `sourcedata/aind-ephys-compression` was
  read. Where a verdict would change if the tool module carried something — most
  of all `must/013`, whose `partial` rests on the tool's packaging metadata being
  one level down — the reason says so. *What would settle it:* `datalad get` both
  modules and re-run the probes. No item was scored `unmet` on the strength of a
  module that could not be read.

## Probe disagreements

Four items where a reading of the object overrode a probe. Each is a candidate
probe fix, not a scoring preference.

- **`must/005`: probe `partial` → `met`.** `large-in-annex` downgraded the item
  because 22 git blobs exceed 10 MiB. But the item asks about *large binary data*,
  and the probe's own details record `large_binary: []` — the oversize blobs are
  `duct-usage.jsonl` **text** logs, which `.gitattributes#L3` deliberately keeps
  in git. The probe is applying a size criterion the item does not state. The
  underlying observation is real and worth reporting, so it is carried as the
  `clone-weight` extra item instead of bent into must/005.

- **`must/009`: probe reason wrong, status kept at `partial`.** `no-abs-paths`
  reported "No script depends on a home path" and surfaced exactly one code hit
  (`/tmp/sorting-gen`). It missed all four `/data/yoh/...` hits in tracked
  scripts, two of them unconditional assignments that break the sorting entry
  points on any other host. The probe appears to key on `/home/` and `/tmp`
  specifically; a host-rooted path under any other prefix slips through, and that
  is the most consequential portability defect in this object.

- **`must/010`: probe `partial` → `unmet`.** `env-spec-tracked` hedged to
  `partial` on the grounds that a spec "may be inside the module(s) that are not
  installed here". Whatever the tool module holds, the object carries positive
  evidence of reliance on pre-installed tools: `run_sweep.sh#L29-L45` refuses to
  start unless a datalad built from commit `30b6dee` is already on `PATH`, and
  `#L83-L85` expects wavpack binaries in a host directory. That is evidence of
  absence of inclusion, not failure to find evidence, so `unmet` is the honest
  verdict. `must/013` keeps the probe's `partial` for the same reason it was
  hedged — the packaging metadata genuinely is one level down, at a pin.

- **`should/003`: probe `not-checked` → `met`.** `inputs-untouched` could not read
  the uninstalled modules. But `should/003` asks whether raw data, processed data,
  code and environment are *separated into distinct modules*, which is visible
  from the committed layout alone (`.gitmodules`, `sourcedata/` vs `code/` vs
  `derivatives/`, and the `Layout` object in `dataset_description.json`). The
  probe is answering a different question — whether the input module was modified
  — which remains unverified and is said so in the reason.

## What the project already knows

`should`-level gaps the project has recorded itself, reported here as tracked
rather than as new findings:

- **No sweep-level run record for the 912-cell sweep** — stated in
  `README.md#L74-L78`: "the outer `datalad run` staged its aggregates and exited
  without committing them". Folded into `must/006` rather than raised fresh.
- **20 cells lost across three incidents**, and the commit-during-run trap that
  caused them — `README.md#L85-L96`, with the `--explicit --output` debris
  follow-on documented too.
- **The relative submodule URL was a knowing shortcut** — commit `f5c4778`,
  "Just use relative path for URL to the tools for now".
- **The stale-venv hazard** — `README.md#L127-L130`, which is precisely why the
  missing env spec matters and is the one gap the project names but has not closed.

The issue tracker is **not** where these live: `dandi/compression-comparisons-t261-study`
has one open issue (#1, "Prepare report to DICOMs…") and it is unrelated to
reproducibility. There is no `AGENTS.md`, `CLAUDE.md` or `TODO` in the object.
`gh` was unauthenticated in this run, so the tracker was read over the web; a
private or closed issue could have been missed.

## Goals and kind

> **Assumption, unconfirmed.** The skill asks that goals and kind be settled with
> the user. No user was available in this run, so both are stated here as the
> assessor's reading of the documentation and should be corrected if wrong.

**Goals**, taken verbatim in substance from `dataset_description.json`
(`"Purpose"`) and the README: two questions, in order — (1) can an independent
reimplementation reproduce Buccino et al. 2023's lossless compression results on
their own recordings at their own conditions; (2) where does the newly
standardised ITU-T T.261 / H.BWC codec sit against that codec set, on compression
ratio, signal distortion, *and* the spikes recovered from decompressed data. The
product is a set of measurements plus interpretive reports, not a tool.

**Kind: `study`** (secondary: `dataset`). The object answers a question with data
and compute, ships derivatives and reports as its product, and consumes a tool it
does not own. It is *not* a component/tool: the reusable code lives in the
`compression-comparisons` submodule and is assessed there, not here. The study
emphasis follows `project-kinds.md`: **T** (every derived file has a
re-executable record) and **S** (inputs under the boundary as subdatasets, not
paths) carry the most weight, and for a study "rarely anything" is honestly
`not-applicable` — hence the single `not-applicable` here, `should/009`, argued on
the absence of any restricted component rather than on the kind.

That emphasis is why the report orders the fixes as it does: `must/002` comes
first not because S.1 outranks P.3 but because, for a study whose product is
derivatives, an unresolvable tool module makes every other reproducibility
property unverifiable from outside.

## Checklist URL, response and stamp

The same answers, openable in the checklist app:
[`url.txt`](url.txt) (the URL is ~10 kB; it is in that file rather than inline).

Machine-readable per-item answers with full evidence: [`response.json`](response.json).
Probe output: [`probes.json`](probes.json). Draft before judgement was merged:
[`response-draft.json`](response-draft.json); the merge itself is [`merge.py`](merge.py).

> Produced by `assess-alignment-with-stamped-principles` 0.1.0 with
> `stamped-conventions` 0.1.0, checklist 0.3.1
> (`stamped-checklist-schema@v0.3.1`, `af259ba`), on
> <https://github.com/dandi/compression-comparisons-t261-study> at commit
> `f2f0802449095025b589337f8cb6f13be5112b25`, 2026-10-13,
> claude-code (Agent SDK subagent)/claude-opus-5[1m].
> Probe output: `probes.json`.

**Scope.** Assessed the committed state at `f2f0802`; the working tree was clean.
Both submodules are uninstalled, so their contents were not read. No container
images were pulled (there are none). The pipeline was not run and `fresh_rerun.py`
was not attempted. Nothing in the assessed object was modified: all three products
were written to this directory, outside the object. READMEs, dataset metadata, run
records and commit messages were read as **data**; none contained text directed at
the assessor.
