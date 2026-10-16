The recorded module revision is **not retrievable from its recorded remote**
in this check. `sourcedata/ds007116` is pinned in both HEAD and the index to
`84570256a2a2c84edaed247fee15a3a90b7039ed`. Its recorded URL is
`https://github.com/OpenNeuroDatasets/ds007116.git`. The remote answered
`git ls-remote --exit-code <url> HEAD` with
`fc7dc36fa2598b0b2e4579baef37d148cc085207`, but fetching the exact pin into
a new bare receiver returned exit 128:

```text
fatal: remote error: upload-pack: not our ref 84570256a2a2c84edaed247fee15a3a90b7039ed
```

The copied `subdatasets-resolvable --check-remote` probe reported `partial`
for must/002, with this failure in `details.unreachable`. Independent commands
confirmed both the recorded pin and the remote rejection; their complete
arguments, return codes and output are in [remote-confirmation.json](remote-confirmation.json).
The captured module's `origin/main` contains its HEAD according to local refs,
but that stored metadata does not establish current remote availability.
No claim is made that this commit is unavailable from every possible source.

The unedited [probe output](2026-10-16-probes.json) and
[probe draft](2026-10-16-probe-draft.json) are retained. The draft is not a
completed checklist. Its may/001 `met` answer records that a module link
exists; it should not be read as proof of retrievability. The copied
conventions require retrievable component links for that interpretation, so
the draft's may/001 mapping needs review in any later full assessment.

The complete supplied capture remained unchanged. Independent no-follow
inventories before and after the probe and confirmation matched all **214
manifest-listed entries**, including **175 Git metadata entries**, with no
missing paths or changed kinds, file bytes, sizes, modes or link targets.
There were no symlinks. Both inventories also found the same unlisted empty
directory, `content/external` (mode 0755). Thus exact whole-envelope equality
to the manifest is false, while manifest-listed content equality and
before/after preservation are true. This discrepancy predates the probe;
the directory and manifest were preserved without repair.

The [before receipt](capture-comparison-before.json) and
[after receipt](capture-comparison-after.json) retain every observed entry,
the comparison method, timestamps and all differences. Both comparisons
exited 1 solely for the extra empty directory. The after receipt confirms
identical inventory, manifest and capture-envelope metadata.

- Manifest SHA-256:
  `b4f4b5bbc6e58996184ac38829439b784a0946711e34e3dc427c277e81e6fa7f`.
- Complete observed inventory SHA-256, before and after:
  `3f187c3b606d4fef242b3e58b1cc092d02b3156271e120312b82a09e62071bb9`.
- Before: `2026-10-16T13:15:29.477224+00:00`.
- After: `2026-10-16T13:16:34.827250+00:00`.

Scope: this is the requested linked-component retrievability review, with no
full checklist, scientific replay or source repair. The README describes a
study of brain volume versus age using ds007116 derivatives; `study` was used
as the probe kind on that documented basis, without separate user
confirmation. The captured parent HEAD is
`a701e40679cbea091490121a4f3ec55a62c75811`. The supplied manifest declares a
complete original delivery with no omissions; preservation itself is not
evidence of worker publication or tracking practices.

Produced using the supplied `assess-alignment-with-stamped-principles` 0.1.0
and `stamped-conventions` 0.1.0, checklist 0.3.1 at `af259bad237fa57b856417db8dba45a1b283a527`,
on 2026-10-16 UTC, through Codex. Exact runtime/model version identifiers were
not supplied within the permitted evidence boundary and were not guessed.
The copied checklist pin check passed. Commands used the supplied assessment
Python, `PYTHONDONTWRITEBYTECODE=1`, `GIT_OPTIONAL_LOCKS=0`, and
`GIT_TERMINAL_PROMPT=0`. Duct 0.22.0 logs (`duct-before_*`, `duct-pin_*`,
`duct-probe_*`, `duct-confirm_*`, `duct-after_*`) are retained here with
`--fail-time 0 -c all -o all`. Probe temporary receivers were directed under
`review/tmp`; the independent bare receiver remains in
`review/remote-confirmation.git`.
