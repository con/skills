# Case B capture integrity review

Strict capture integrity fails on one added entry:
`content/workspace/.git/FETCH_HEAD`, an empty regular file, mode `0644`,
SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

The manifest declares 214 entries; including the three required wrapper entries,
217 are expected and 218 are present. There are **zero missing entries and zero
content, mode, kind or symlink-target changes** among the expected entries.
The original fixture capture and fixture-source workspace still match the
manifest. Case B's manifest bytes equal the original fixture manifest and the
preparation SHA-256 `b4f4b5bbc6e58996184ac38829439b784a0946711e34e3dc427c277e81e6fa7f`.

The observed delta is confined to Git operational metadata. No source, scientific
output, tracked content, Git object/ref/index or recorded entry changed. This
does not make the strict capture valid: an unexpected `FETCH_HEAD` is sufficient
to fail its exact-inventory requirement. No exception or repair was applied.

The remote-check probe is the strongly supported cause. Native session record 90
invokes `run_probes.py --check-remote` with `GIT_OPTIONAL_LOCKS=0`.
The retained `snapshot-02/.../probes/modules.py` lines 109–113 run
`git fetch --depth=1 --no-tags <url> <commit>` with `cwd=obj.root`.
The probe receipt records that fetch failing because the pinned commit is not
available upstream. `FETCH_HEAD`'s mtime is 2026-10-16T12:57:40.734079+00:00, inside the
logged probe interval 2026-10-16T12:57:39.741326+00:00 to 2026-10-16T12:57:41.158775+00:00.
This attribution combines command, code, result and timing evidence; there is no
syscall audit proving the individual writer. The later failed annex query is
not needed to explain this delta.

Scope: read-only direct filesystem inventories plus existing preparation,
fixture, skill snapshot, duct and native session evidence. No Git or annex
command ran against the target during this review, and no assessment was
regraded, repaired or replayed. Before/after and final comparisons verify that
the target capture, original fixture capture, fixture-source, fixture-source-input,
assessment outputs (including their logs), snapshot-02 and listed preparation
files retained their bytes, modes, kinds and link targets throughout these
comparisons. Native-session bytes and its receipt were also verified unchanged.
Read access times are outside this integrity comparison.

Machine-readable evidence: `delta.json`, `attribution.json`, and the two
`source-inventory-*.json` files. Reproduction scripts: `compare_capture.py` and
`inspect_attribution.py` (exclusive-create outputs; use a new review directory
for any later review). Full requested duct captures use `compare-` and
`attribution-` prefixes in this directory. All review writes are confined here.
