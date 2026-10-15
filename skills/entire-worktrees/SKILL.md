---
name: entire-worktrees
version: 0.1.0
description: Prepare native Entire capture for agent worktrees or fresh clones and verify real session/checkpoint evidence. Use before launching captured workers or diagnosing missing capture.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
max-lines: 90
---

# Native capture across workspaces

Use the project's prepared launch task when available.
Prepare each writable checkout before its agent starts: recorded submodules, declared environment, native Entire configuration and composed hooks.
Keep host credentials and tool locations outside tracked files; reuse existing providers.
Retain preparation receipts with the owning experiment.

Hook trust may be path-specific.
Reuse approvals only for byte-identical already-approved hooks; preserve denials and review changed hooks.
Compose capture, formatting and provenance hooks without replacing or double-wrapping them.
Clear inherited session identifiers before starting a fresh native CLI session.

Worktrees isolate tracked files, not host instructions, credentials or externally linked skills.
Where isolated conditions matter, inspect the effective loaded instructions and skill paths.
Keep common resource guidance identical across comparison arms and verify exclusions actually take effect in the installed runtime.

Configuration alone is not capture evidence.
Exercise a real file change and commit; verify native transcript, checkpoint, session identity and intended checkout.
Test branch switches, new worktrees, fresh clones and delegated children separately.
A child's session directory may remain in its parent's checkout; inspect actual file events and commit linkage.

Within the project's publication scope, publish intended code/checkpoint refs, compare remote object IDs and verify hosted session identity.
Use actual dashboard links and report hosted verification separately from local capture.
Limit coverage claims to the tested launch route; retain a small repeatable probe so future changes can be checked.
