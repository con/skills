---
name: datalad-annex
description: Record and replay DataLad commands with Conventional Commits in a Pixi project, and verify git-annex delivery. Use for DataLad run/rerun, missing annex content, or preserving captured evidence.
version: 0.1.0
---

Use the root `pixi.toml`; add missing packages there.
Keep the working lock ignored, retain the exact validated lock, and publish its separate environment snapshot according to the project's environment policy.
An installed package in another project is not this project's dependency.

Use native `datalad run --explicit` with declared inputs and outputs.
The prepared checkout hook preserves `[DATALAD RUNCMD]`, adds a Conventional subject and freshly resolved attribution.
Do not remove the marker or overwrite hooks.
If fresh provenance is unavailable, stop before committing and ask the coordinator.

DataLad 1.7.1 does not discover that prefixed record natively.
Use the checked-in adapter, which changes parsing only inside its process:

```sh
pixi run --locked python .agents/skills/datalad-annex/scripts/replay.py discover \
  --dataset . --revision RUN_COMMIT --receipt DISCOVERY_JSON
pixi run --locked python .agents/skills/datalad-annex/scripts/replay.py rerun \
  --dataset . --revision RUN_COMMIT --onto BASE_COMMIT --receipt REPLAY_JSON
```

The adapter rejects unsupported versions/message shapes and requires an actual run result.
Before replay, put the recorded lock in the recipient checkout and verify that its hash and manifest match the recorded run.
After checking out a replay base, run `git submodule update --init --recursive` and confirm a clean dataset; installed children must match that revision's gitlinks.
Checkout transitions must not substitute another manifest or silently solve.
Report compatibility replay separately from unmodified native discovery.

For a regeneration check, use a disposable external clone with generated paths and annex payloads absent, then check an independent expected result.
Exit zero alone is insufficient; the same verifier must reject a no-op.

Annex pointers are not payloads.
Check the exact key/hash after `git annex get` from the named remote.
Local clone retrieval establishes same-host delivery; only a successful remote transfer establishes online delivery.
Git writes and annex writes are separate operations.

Inspect effective `git check-attr` rules and prepared hook receipts before capturing pointer text or nested repositories.
Local `info/attributes` can override tracked rules; broad annex hooks can rewrite captured symlink targets.
Keep trial clones outside the repository; retain their revisions and receipts, not whole checkout archives.
Use the requested module-local direct duct capture once around the trial, preserving failures and its completed outer summary.
