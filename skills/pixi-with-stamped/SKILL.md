---
name: pixi-with-stamped
version: 0.1.0
description: Use Pixi to make a STAMPED project's dependencies and executable tasks portable, with recorded environments and a tested replay route. Use when the project selects Pixi; honor its lock and logging policies.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
max-lines: 100
---

# Pixi with STAMPED

Use the project's root `pixi.toml` for dependencies and named tasks.
Add ordinary missing packages with `pixi add`; reuse maintained scientific and plotting packages rather than writing dependency-free substitutes.
Run tools through `pixi run`, including DataLad, git-annex and requested duct, so executables come from the declared environment.
A package installed in another project or on the host is not a declared dependency.

Expose useful operations as named tasks with inputs, outputs and parameters appropriate to the work: analysis, figures, validation, replay or worker launch.
Reuse the project's scripts behind those tasks; verify the task actually runs.
Keep host credentials, scheduler choices and external runtime paths in replaceable host configuration.
Declare supported platforms and test only the coverage claimed.

## Environment identity

Follow the project's chosen lock policy.
A tracked lock is suitable when requested; a developing shared manifest may instead keep working locks ignored and retain exact validated locks separately.
For the latter policy: preserve the final lock bytes without re-solving, commit them as ordinary Git on a snapshot branch one commit above the task commit, and record immutable code/snapshot IDs, lock hash and platform.
Keep that snapshot separate from main; set ignore and annex rules before the task commit.

Before replay, restore the recorded manifest and lock together and install with `pixi install --locked`.
Do this again when replay changes the code revision; never silently solve a new environment while claiming the old one.
Use a fresh workspace to test restoration and output regeneration.

## Execution evidence

Use the project's requested provenance mechanism; for DataLad apply [datalad-annex](../datalad-annex/SKILL.md).
When duct capture is requested, a task should invoke the environment's direct `duct` once and place complete records with that experiment.
Retain command metadata, stdout/stderr, resource usage and the completed summary with outputs; annex large records.
An orchestrator's native logging layout remains authoritative.
Record environment and run identities so scientific outputs, execution records and replay receipts can be connected.
