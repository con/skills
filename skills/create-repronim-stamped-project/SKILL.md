---
name: create-repronim-stamped-project
version: 0.1.0
description: Apply STAMPED project creation to a ReproNim workflow with versioned data, community neuroimaging tools, BIDS-aware boundaries and recorded execution. Use for an explicitly ReproNim-oriented project.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Skill
max-lines: 80
---

# Create a ReproNim-oriented project

Apply [create-stamped-project](../create-stamped-project/SKILL.md) with the selected ReproNim stack.
Preserve the scientific question; add imaging, containers or a cluster only when the task needs them.
Read the applicable parts of [references/repronim.md](references/repronim.md).

Identify source revisions, access terms, dataset selection, relevant standards, raw/derivative boundaries, resource budget and deliverables. Prefer established DataLad/git-annex workflows, community BIDS validators and analysis packages, and the user's selected BIDS App orchestrator.
Use [pixi-with-stamped](../pixi-with-stamped/SKILL.md) when Pixi is selected; use [datalad-annex](../datalad-annex/SKILL.md) for native execution and delivery.

Verify a bounded input through computation, QC and result collection.
Cluster readiness requires a completed compute-node job and tested return route; a local publication relay is sufficient.
Use pilot measurements to size later work.
Retain requested logs with the owning task, following the orchestrator's native layout where available.

Deliver executable tasks, identities, useful outputs and a scoped assessment.
Distinguish BIDS conformance, scientific correctness, retained provenance and successful replay.
