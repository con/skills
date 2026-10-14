---
name: create-repronim-stamped-project
description: Create a neuroimaging research project using a ReproNim-oriented adapter for STAMPED, including BIDS-aware organization, versioned data, reproducible environments, and captured execution. Use for an explicitly ReproNim-oriented project.
version: 0.1.0
---

# Apply a ReproNim adapter

Preserve the scientific question and the user's tool choices.
Read [the principles orientation](references/principles.md) and [the implementation reference](references/repronim.md).
Distinguish the principles from this adapter's practical defaults.

Prepare a creation brief containing the question, audience, data permissions, budget, exact source identities, BIDS/raw-versus-derivative boundaries, environment/runtime requirements, provenance strategy, and expected checks.
Use create-stamped-project if available.
Otherwise perform its essential workflow directly: establish the object boundary; create explicit components, environment and execution entry point; run the smallest complete slice; retain evidence; assess all seven properties and unresolved gaps.

Prefer DataLad/git-annex for versioned datasets and transformations and a project-local declared environment such as Pixi where compatible with the project.
Retain upstream datasets as independently identified subdatasets when that is their natural distribution.
Pin content and container digests; record where bytes can actually be obtained.
A Git commit or annex key alone does not guarantee retrieval.

Honor the BIDS version and relevant derivative specification for the chosen modality.
Preserve source metadata and licenses, keep raw inputs immutable, and put generated data/figures in a clearly identified derivative or analysis module. Record subject/session/run selection and exclusions.
BIDS validity does not establish appropriateness of the scientific analysis.

For BIDS Apps, prefer the user's configured orchestration, using MechaBABS when requested.
Inspect its installed version, configuration, and official usage; do not invent commands.
Verify one inexpensive job including output collection and provenance before scaling.
Record scheduler limits and measured pilot resource use.
Do not add a container, remote cluster, or imaging pipeline for a question answerable with simpler data.

Link native agent history, execution/resource logs, and DataLad transformation records with shared run identifiers while keeping their meanings distinct.
Apply the project's capture prerequisites to each delegated repository or worktree.
A disposable environment should leave durable analysis results, source identities, and logs.

Verify fresh retrieval and a bounded replay where feasible.
Report scientific validity separately from the seven STAMPED properties, scope checks to observed platforms and access conditions, and expose remaining limitations.
Tools named here implement choices; their presence is not evidence of successful alignment.
