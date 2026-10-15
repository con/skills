---
name: create-repronim-stamped-project
description: Create a STAMPED computational research project using a ReproNim-oriented workflow, including BIDS-aware data boundaries, DataLad/git-annex, task environments and reproducible execution. Use for an explicitly ReproNim-oriented project; adapt to the user's selected tools and scientific scope.
version: 0.1.0
---

# Create a ReproNim-oriented project

Apply [create-stamped-project](../create-stamped-project/SKILL.md) with this adapter's choices.
Preserve the scientific question; do not add imaging, containers or a cluster to a task that only needs tables.
These tools implement STAMPED properties, not additional normative principles.

Read [references/repronim.md](references/repronim.md) for the applicable dataset, environment and execution details.
Prepare a brief identifying source revisions, permissions, dataset selection, applicable standards/version, raw/derivative boundaries, budget, runtime and intended deliverables.

Prefer the project's established ReproNim tools: DataLad/git-annex for datasets and transformations, its task environment manager, BIDS validators and community analysis packages, and its selected BIDS App orchestration.
Add ordinary missing dependencies to the task environment.
Consult installed-version documentation before choosing command flags.

Verify the actual path from one bounded input through computation, QC and result collection.
Cluster use additionally needs a completed compute-node job and a tested return route; direct cluster publication is optional when a local relay supplies it.
Pilot resource measurements inform scaling.

Deliver executable setup/replay instructions, source and environment identities, useful outputs, requested records and a scoped assessment.
Distinguish BIDS conformance, scientific correctness, retained provenance and successful replay.
Report untested platforms or inaccessible content honestly.
