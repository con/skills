# Scoped STAMPED evidence assessment

This report answers only `must/010` and `must/013` for the two dependency-review tools, and `must/016` for the annexed-spec object. Every other checklist item remains unassessed. These are synthetic engineering fixtures; no scientific claim is evaluated. No assessment checklist URL is produced.

## Probe suggestions

The frozen `env-spec-tracked` probe ran against each object with remote checks disabled. It correctly finds each tracked `requirements.txt` and leaves dependency completeness at `not-checked`, noting that imports and invoked tools need comparison. For `annexed-spec`, it reports `must/016 partial` because a Git origin is configured but the probe did not check whether that URL resolves. Probe outputs are preserved unchanged in the three adjacent `*-probes.json` files.

## Final judgments

| Object and commit | Item | Status | Evidence and judgment |
|---|---|---|---|
| `dependency-review` fixture 0, `a4427bc0d4abcc0b8b299e194b2b20d74a506c12` | must/010 | **met** | `analysis.py` imports and calls `numpy`; tracked `requirements.txt` declares `numpy`. The only code and spec in this small object agree. This is a static dependency review; execution of `analysis.py` was prohibited. |
| Same | must/013 | **met** | `requirements.txt` is tracked in that same commit (`git ls-files --stage`; blob `24ce15ab7ead32f98c7ac3edcd34bb2010ff4326`). |
| `dependency-review` fixture 1, `9058af8e7eba4450bae7758be98b22d461eae765` | must/010 | **met** | `analysis.py` imports and calls `numpy`; tracked `requirements.txt` declares `scipy`, whose installed dependency graph includes NumPy. Thus the import is supplied by the declared environment dependency graph rather than an assumed host install. This is static reasoning, not an executed environment check. |
| Same | must/013 | **met** | `requirements.txt` is tracked in that same commit (`git ls-files --stage`; blob `9a635b910d93ff2d9b1c24b7bc7ce15600b65d31`). |
| `annexed-spec`, `77dedfe19f21ec17fc704fc5aa30e782345a98d8` | must/016 | **partial** | The supplied receipt records a separate `--no-local` recipient clone and successful `git annex get` from the sibling local bare store. The recipient clone has a distinct annex UUID; `whereis` marks it `here`, its annex content path exists, and hashing its symlink target yields the same SHA-256 as the source and receipt. This establishes retrieval by that recipient on this host from the shared local store. The source's `store` remote is a filesystem path, and the receipt expressly limits its scope to one host; it does not establish network/public access for other users. |

For the dependency fixtures, a filename-only or “manifest exists” probe could not settle `must/010`; comparing actual imports and declarations did. Fixture 1 is met on the declared transitive dependency path, not because `requirements.txt` is present. Because execution was disallowed, the judgments establish dependency coverage from the committed code/spec and package dependency semantics, not a successful run.

For `must/016`, the probe's remote-URL check is only a suggestion: no remote-network check was authorized. Its configured `origin` (`https://example.org/con/thing`) is not the source of the demonstrated retrieval. The receipt plus observed recipient content supplies stronger, narrowly scoped evidence: an independent checkout retrieved and held matching bytes from the same-host local store. Annex location metadata alone would have shown claims about copies, not recipient retrieval. The status remains partial because availability is limited to a recipient with access to that local filesystem; broader access is unproven.

## Friction notes

- The probe intentionally combines `must/010`, `must/013` and `must/016` in one result. The item-specific statuses must be read from `item_status`; the overall probe status does not answer each item.
- Its `must/010` result needs code review. A spec filename or pin is not dependency completeness. Here, imports and declared dependencies supplied the judgment.
- Its `must/016` result uses the configured Git origin when no network check is made. It misses a local annex remote and a supplied, successful recipient retrieval receipt. Keep retrieval evidence and access scope explicit; `whereis` alone is metadata.
- `git annex contentlocation` takes an annex key, not a worktree path. `lookupkey` followed by `contentlocation <key>` located the recipient's local content without fetching it.
- The required no-execution boundary means the dependency judgments are not claims that either `analysis.py` was run in its declared environment.

## Provenance and limits

Assessor snapshot: `/tmp/stamped-assessment-evidence-blind`, with `source.json` source commit `afd2c0ff8b556788a3ab9e7d35eb0e4b24cd5d59`. All 19 hashes in `snapshot-sha256.json` matched. The snapshot identifies `assess-alignment-with-stamped-principles` 0.1.0 and `stamped-conventions` 0.1.0. Checklist pin: 0.3.1, source commit `af259bad237fa57b856417db8dba45a1b283a527`; the vendored checklist hash matches the snapshot manifest.

Target commits are listed in the table. The annex retrieval receipt is `/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/retrieval-receipt.json`; the command and evidence record, including probe invocation details, is `command-evidence.md`. This was a scoped assessment, not a full STAMPED checklist.
