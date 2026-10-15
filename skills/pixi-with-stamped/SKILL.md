---
name: pixi-with-stamped
version: 0.1.0
description: Use Pixi to make a STAMPED project's dependencies and executable tasks portable, with recorded environments and a tested replay route. Use when the project selects Pixi; honor its lock and logging policies.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
max-lines: 100
---

# Pixi with STAMPED

Use the project's root `pixi.toml` for dependencies and named tasks.
Experiments own their environments and may evolve requirements in separate worktrees; integrate differing requirements as named environments on merge and select them explicitly in tasks (`pixi run -e <name> ...`).
Named environments inherit the default feature unless disabled; use `no-default-feature = true` for incompatible requirements and avoid a shared solve group when versions must differ.
Add ordinary missing packages with `pixi add`; reuse maintained scientific and plotting packages rather than writing dependency-free substitutes.
Run tools through `pixi run`, including DataLad, git-annex and requested duct, so executables come from the declared environment.
A package installed in another project or on the host is not a declared dependency.

Expose useful operations as named tasks with inputs, outputs and parameters appropriate to the work: analysis, figures, validation, replay or worker launch.
Reuse the project's scripts behind those tasks; verify the task actually runs.
Keep host credentials, scheduler choices and external runtime paths in replaceable host configuration.
Declare supported platforms and test only the coverage claimed.
Check binary wheel OS requirements: when they exceed Pixi's default platform floor, declare the verified minimum in `system-requirements` before solving.

## Environment identity

Follow the project's chosen lock policy.
A tracked lock is suitable when requested; a developing shared manifest may instead keep working locks ignored and retain exact validated locks separately.
For the latter policy: preserve the final lock bytes without re-solving, commit them as ordinary Git on a snapshot branch one commit above the task commit, and record immutable code/snapshot IDs, lock hash and platform.
Keep that snapshot separate from main; set ignore and annex rules before the task commit.

When inspecting or archiving another research object, retain and hash its manifest and any lock, including ignored files, and run bookkeeping tools from an explicitly selected operational environment against the target path.
Verify those evidence files remain unchanged; test or repair the target environment only in a separate replay copy, recording any changes.

Choose what stays fixed across data, code, dependencies and host before reassessment or reproduction.
To hold dependencies fixed, restore the matching manifest and retained lock, then synchronize with `pixi install --locked -e <recorded-env>`; a code change alone need not change this selection.
To test current requirements, deliberately solve afresh and record the new selection.
Disposable installations test rebuildability; flexible requirements ease reuse; retained locks improve historical recovery but do not guarantee package availability or host portability.
Use a fresh workspace when testing restoration and output regeneration.

## Execution evidence

Use the project's requested provenance mechanism; for DataLad apply [datalad-annex](../datalad-annex/SKILL.md).
When duct capture is requested, a task should invoke the environment's direct `duct` once and place complete records with that experiment.
Retain command metadata, stdout/stderr, resource usage and the completed summary with outputs; annex large records.
An orchestrator's native logging layout remains authoritative.
Record environment and run identities so scientific outputs, execution records and replay receipts can be connected.
