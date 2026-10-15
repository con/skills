# Scoped independent followability assessment

Synthetic engineering validation, 2026-10-15 UTC. This is not a scientific or
formal full-checklist assessment. Only the five object/item pairs below are
judged; all other items remain unassessed, including extra items emitted by the
probe. No checklist URL was generated.

**Labelled assumptions, not human-confirmed:** the two README-labelled
“Numerical tool” objects are components whose demonstration calls NumPy. The
annex object is treated as a component carrying a synthetic environment artifact,
with access assessed for the supplied same-host recipient context. No claim
about scientific validity, container executability, or public access is made.

## Final judgments

| Object | Item | Final status | Reason |
| --- | --- | --- | --- |
| `test_a_manifest_does_not_prove0/dependency-review` | must/010 | met | The documented isolated-venv route installs requirements.txt, which declares numpy; analysis.py imports only numpy. No other application dependency or invoked external tool appears in the complete committed route. |
| Same | must/013 | met | requirements.txt is a regular Git blob beside README.md and analysis.py at dbcff95b4eb45cb33837c5eaf3ff79bf83d9dadf. |
| `test_a_manifest_does_not_prove2/dependency-review` | must/010 | unmet | analysis.py requires numpy, but the documented isolated-venv route installs a requirements.txt containing only a comment. No local provider or dependency chain supplies numpy; the matching-commit receipt records its missing import. |
| Same | must/013 | met | The empty dependency declaration requirements.txt is tracked beside code at 5697076be929f539b770d19efa899044e38d58b9. Its incomplete contents fail must/010; they do not make the specification untracked. |
| `test_a_spec_whose_content_neve0/annexed-spec` | must/016 | met, limited to the supplied local recipient context | The separate recipient is at the assessed commit and holds the specified 2,304-byte payload with the committed annex-key hash. The receipt records successful local-store retrieval. Public or other-host access remains not-checked. |

Across the five scoped pairs: four met (one expressly local), one unmet.
The immediate repair is to declare NumPy in the empty requirements file. Version
pinning is separate and is not judged here. Python/venv/pip are explicit
bootstrap steps in the README; the numerical-tool must/010 findings concern
application dependencies on that route, not a successful test of host bootstrap.

The three complete committed trees and exact file contents are recorded by
`git ls-tree` and `git show HEAD:<path>` in [commands.jsonl](commands.jsonl).
Those records establish the dependency findings independently of fixture names
or receipts. No fixture answer key was read.

## Execution route and receipt evidence

Both numerical README files say to create `.venv` with `python3 -m venv`, install
`requirements.txt` using `.venv/bin/python -m pip`, and execute `analysis.py`.
Each committed script is two lines: `import numpy` and
`print(numpy.arange(3))`. The complete trees contain only the README, script and
requirements file. The first specification says `numpy`; the second says
`# no packages declared`. There is no alias ambiguity or declared transitive
provider in the empty case, and no local/vendored package in either tree.

The supplied execution receipt names commit
`5697076be929f539b770d19efa899044e38d58b9`, matching the inspected object. It
records return code 1 and `ModuleNotFoundError: No module named 'numpy'`.
Its external `empty-runtime/pyvenv.cfg` confirms system-site-packages are disabled,
but also records `--without-pip`. It is therefore corroborating evidence for the
missing application import, **not** a complete replay of the documented install
route: it lacks a pip-install command/result and uses another venv path.
The omission judgment rests on committed code and declarations; it does not
depend on treating this receipt as an exact replay. Neither analysis was run
for this review.

## Retrieval evidence and its boundary

The committed `.datalad/config` identifies `code/containers/analysis.sif` as the
container image. Its Git entry is an annex symlink whose SHA256E key encodes
size 2304 and SHA-256
`7a3838d9d993f455975a9a9eac0cf5107aa92f0750b3d1aaacfb193fbd210ce1`.

The supplied receipt records a `git clone --no-local` from the source fixture,
then changing the recipient's origin to the local `remote.git`, initializing a
separate annex, and successfully running `git annex get --from origin` for that
image. This proves less than cloning all history from the advertised publication
location: the receipt's Git-history clone source was the original fixture.
It does provide recorded evidence of payload retrieval from the local store.

This review independently checked source and recipient HEADs and trees, distinct
annex UUIDs, current recipient origin, and actual bytes in both annex object
stores. Both payload hashes match the committed key and receipt; both are 2,304
bytes. Source and recipient resolve to different local annex object paths. See
[payload-verification.json](payload-verification.json) and the accompanying
commands. The reviewer did not perform a new retrieval. The receipt is supplied,
unsigned evidence whose described result is corroborated by the current local
state; the historical transfer itself was not independently witnessed.

A configured `https://example.org/con/thing` origin and any annex location claims
are metadata, not access proof. No remote was contacted. The verified recipient
is on the same host and account with a local-store origin. Access by the public,
a different account, or another host remains **not-checked**, not unmet. The
synthetic image's executable validity and the `make all` reproduction instruction
were outside scope and were not tested. This limited pass must not be copied
into an unrestricted publication claim.

## Probe suggestions, kept separate from judgments

Unmodified outputs are [numpy-probes.json](numpy-probes.json),
[empty-probes.json](empty-probes.json), and [annex-probes.json](annex-probes.json).
Each used only `env-spec-tracked`, without `--check-remote`.

- Both numerical probes suggest must/010 `not-checked` and must/013 `met`.
  Manual route inspection resolves must/010 to met and unmet respectively.
  Record source `probe:env-spec-tracked+judgement` and `probe-overridden` for
  both must/010 resolutions. The must/013 suggestions stand after file review.
- The annex probe suggests must/016 `partial` because a remote is recorded but
  reachability is unestablished. The supplied receipt and independent payload
  identity check justify a local-context met judgment, with source
  `probe:env-spec-tracked+judgement` and `probe-overridden`.
- The numerical probes also emit must/016 judgments and the annex probe emits
  must/010 and must/013 judgments. These are unadopted raw suggestions, not
  assessment results, because the request excludes them.

## Pins and provenance

Frozen skill source commit: `c29acfc115ad880030b2c42c0941d0d58c4739f3`, as
reported by the supplied source.json. No originating repository was inspected.
All 19 listed snapshot files matched their SHA-256 manifest. The vendored
checklist helper confirmed checklist 0.3.1 (31 items) against its lock.
See [snapshot-verification.json](snapshot-verification.json).

Object commits:

- NumPy declaration: `dbcff95b4eb45cb33837c5eaf3ff79bf83d9dadf`.
- Empty declaration: `5697076be929f539b770d19efa899044e38d58b9`.
- Annex source and recipient: `77dedfe19f21ec17fc704fc5aa30e782345a98d8`;
  tree `285a9de2e298986a0aacc719e064dd8dbc0aae06`.

The four inspected worktrees were clean when checked. No assessed target was
modified. All writes were to this review directory. Snapshot helpers ran under
the specifically authorized Pixi manifest; repository source and tests were not
inspected. No external services, pipeline execution, or payload fetching was
performed. No dependencies were added.

Applied `assess-alignment-with-stamped-principles@0.1.0` and
`stamped-conventions@0.1.0`, checklist 0.3.1, within the explicitly reduced
validation scope. Harness: Codex subagent. Exact model/runtime versions were not
provided by this assessment harness and are not guessed. The exact delegation
prompt is [prompt.txt](prompt.txt); friction notes are [friction.md](friction.md).
