# Command and evidence record

All three snapshot probes ran with the supplied Pixi manifest, with `--only env-spec-tracked` and without `--check-remote`. Their unedited JSON outputs are `dependency0-probes.json`, `dependency1-probes.json`, and `annexed-probes.json` in this directory.

## Commands

1. Validated every entry in `/tmp/stamped-assessment-evidence-blind/snapshot-sha256.json` against its corresponding snapshot file. Result: all 19 hashes matched. The checklist JSON's SHA-256 is `da2eb88ed49dff64f098ad92200dec81c1b4404cc2d3ba1e1e1404d0e10e7bba`.
2. Read the pinned item text from `skills/stamped-conventions/checklist/stamped-checklist-0.3.1.json` and the probe implementation `scripts/probes/structure.py` in the snapshot. Relevant helper: `env_spec_tracked`; it explicitly leaves completeness not-checked absent a clear host-tool precondition and directs the assessor to compare imports and invocations with declarations.
3. Ran:
   - `pixi run --manifest-path /Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml python /tmp/stamped-assessment-evidence-blind/skills/assess-alignment-with-stamped-principles/scripts/run_probes.py /tmp/stamped-assessment-evidence-fixtures/test_a_manifest_does_not_prove0/dependency-review --only env-spec-tracked --kind component --quiet -o /tmp/stamped-assessment-evidence-blind/smaller/dependency0-probes.json`
   - same command for `.../test_a_manifest_does_not_prove1/dependency-review`, output `dependency1-probes.json`
   - same command for `.../test_a_spec_whose_content_neve0/annexed-spec`, output `annexed-probes.json`
   All exited 0. The probes report `must/013 met` on both tools. They leave `must/010 not-checked` for both because a spec's presence does not establish completeness. The annex probe reports `must/016 partial` from an unverified configured origin URL (`https://example.org/con/thing`).
4. Read committed target files only: each tool's `analysis.py` and `requirements.txt`; annex object's `README.md`, `.datalad/config`, Git config; recipient Git config; and the supplied `retrieval-receipt.json`.
5. For each object, ran `git rev-parse HEAD`, `git status --short`, and `git log -1 --format='%H%n%s'`. Both tools and the annexed object and recipient were clean. Commits:
   - dependency fixture 0: `a4427bc0d4abcc0b8b299e194b2b20d74a506c12`
   - dependency fixture 1: `9058af8e7eba4450bae7758be98b22d461eae765`
   - annexed spec and recipient: `77dedfe19f21ec17fc704fc5aa30e782345a98d8`
6. Ran `git ls-files --stage` on each tool and on the annexed spec. It confirms both `analysis.py` and `requirements.txt` are tracked for each tool; `.datalad/config` and `README.md` are tracked in the annexed object, while `code/containers/analysis.sif` is a tracked annex symlink (mode `120000`).
7. Read native annex metadata using:
   - `pixi run --manifest-path /Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml git -C <annexed-spec-or-recipient> annex whereis --json code/containers/analysis.sif`
   - `... git -C <recipient> annex lookupkey code/containers/analysis.sif`
   - `... git -C <recipient> annex contentlocation SHA256E-s2304--7a3838d9d993f455975a9a9eac0cf5107aa92f0750b3d1aaacfb193fbd210ce1.sif`
   Source metadata lists two locations (source local and UUID `2b4a96f1-fa74-4fde-b902-3df0bc4933ac`, description `store`). Recipient metadata lists three locations and marks recipient UUID `7c7d7464-04f3-461b-bbf3-550d22bb3524` as `here`. The returned content path exists in the recipient clone.
8. Ran `sha256sum` on `annexed-spec/code/containers/analysis.sif` and `recipient/code/containers/analysis.sif`. Both returned `7a3838d9d993f455975a9a9eac0cf5107aa92f0750b3d1aaacfb193fbd210ce1`, matching the annex key's embedded digest and both hashes in `retrieval-receipt.json`.

## Boundaries and failed attempt

No network access, external service contact, content fetch, dependency installation, target modification, or execution of `analysis.py` occurred. Hashing the already-present symlink target read local bytes; it did not retrieve content.

An initial `git annex contentlocation code/containers/analysis.sif` attempt returned `git-annex: bad key` (exit 1). The command expects an annex key, so `lookupkey` was run first and `contentlocation` was repeated with that key. This was metadata lookup only.

The receipt records a `git clone --no-local` into `recipient/`, changing that clone's origin to the sibling local bare repository, then `git annex get --from origin code/containers/analysis.sif` with return code 0. The clone has a distinct annex UUID from the source; its current local bytes and hash were independently observed as above. This confirms retrieval by that separate clone from the local store on the same host. It does not show public/network access or access by a user without that shared filesystem.
