---
name: datalad-annex
version: 0.1.0
description: Capture native DataLad runs and reruns, retain task records, and verify git-annex retrieval. Use for recorded computation or missing annex content in an existing project.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
max-lines: 90
---

# Native DataLad execution and annex delivery

Use the project's declared environment and task entry points; add missing packages there.
For Pixi, apply [pixi-with-stamped](../pixi-with-stamped/SKILL.md).
Install selected subdatasets at recorded commits with `datalad get -n PATH` when only their metadata is needed.
After a plain Git clone or `git submodule update --init`, initialize each selected annex repository with `git -C PATH annex init` before annex queries or retrieval; Git checkout alone does not initialize its annex.
Keep initialization scoped to required datasets; retrieve payloads separately and preserve ordinary submodule `.git` files and tracked input links.
Separate concurrent writers into external worktrees with their own writable children.

Use native `datalad run --explicit` or `containers-run` with declared code, data, environment inputs and generated outputs.
Keep native `[DATALAD]` and `[DATALAD RUNCMD]` subjects and structured run records intact.
Exempt these machine-generated subjects from Conventional Commit rewriting and validation; normal authored commits still follow the project's convention.
Add required provenance trailers without moving the native marker or changing the run record.
Compose existing hooks; confirm discovery with `datalad rerun --report RUN_COMMIT`, then execute a genuine native rerun.

A DataLad record selects a command, not automatically its historical data, code or environment.
For comparison choices and environment trade-offs, use [reassessment and replay](references/reassessment.md).
State what stays fixed and what changes for the question; `datalad rerun RUN_COMMIT` normally uses the current checkout.
Restore the retained environment only when holding that dependency selection fixed; record a new selection when testing dependency changes.
An outer environment launcher runs before DataLad checkout transitions: select the intended state before launching, or record an explicit inner launcher that synchronizes afterward.
Record the calculation rather than a task that recursively calls `datalad run`.
In a disposable checkout, remove only declared generated paths, keep expected artifacts elsewhere, and require actual regenerated output.
Compare independent expected values and declared numerical tolerances or exact digests; exit zero alone is insufficient.

Annex pointers are not payloads.
Inspect effective attributes before adding files; keep code and small specifications in Git and large outputs/records in annex.
Prefer path, extension or size rules.
Use `datalad create` without `-c text2git` when the installed annex build lacks MagicMime; MIME-based attributes require that optional build support.
Publish required child commits and annex content before the parent gitlink.
Verify a fresh recipient can `git annex get` the expected key from the named remote and match the content hash.
Distinguish same-host delivery from online retrieval.
Git and annex writes use separate routes; cluster results may return through the local host.

When duct is requested, use one direct capture around the substantive command and retain its complete metadata, stdout/stderr, resource data and final summary with the owning module.
Wait for the outer summary before committing its records; retain failed attempts too.
Use an orchestrator's native provenance layout where available.
Keep trial clones outside the repository; retain their revisions and receipts rather than whole checkout archives.
