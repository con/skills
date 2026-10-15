---
name: create-stamped-project
description: Create a computational research project with explicit inputs, component boundaries, an executable workflow, a task environment and a replay route. Use when asked to start or scaffold a STAMPED, reproducible or shareable project without imposing a domain-specific tool stack.
version: 0.1.0
---

# Create a usable research object

From the request and examples, establish question, audience, inputs/access, products, computational scale and existing tools.
Ask for consequential missing facts; do not mine private history for conventions.
Use the smallest workable structure.

1. **Define the boundary.** Name the root, input/output locations, module responsibilities, exact external source identities, retrieval routes and reuse terms.
   Components may be included or persistently referenced.
   Keep raw inputs immutable and access secrets outside shared content.
2. **Create working content.** Add the question/use-case record, essential input inventory, smallest runnable analysis or workflow entry point, environment manifest, output locations and replay instructions.
   Use established community tools and existing project conventions rather than building substitutes.
3. **Realize dependencies as needed.** Add ordinary missing packages to the owning task manifest and retry.
   Follow project policy: loose development constraints are acceptable; retain the exact environment used for final validation through a supported lock, export or image.
   Record host-only requirements separately.
   Never fabricate a runnable study when essential data or access is unavailable.
4. **Integrate the chosen provenance.** Establish input/code/parameter/environment identities and output records. Preserve existing hooks. If native agent capture or execution logging is requested, prepare it at the actual checkout and verify an event/run before delegation; availability alone does not prove capture.
   Keep personal authentication outside project dependencies.
5. **Exercise one complete slice.** Obtain inputs, execute, inspect results, and check restoration in a disposable workspace when feasible.
   Verify needed artifact retrieval, not just repository metadata.
   Preserve useful evidence before cleanup; state the platform/access scope tested.

Write only the setup, execution, validation and boundary facts future sessions need into the existing harness.
Use [align-stamped](../align-stamped/SKILL.md) for broader alignment and [assess-stamped](../assess-stamped/SKILL.md) for the final evidence-based assessment.
These siblings share this collection; install missing declared dependencies through the project's method.

Deliver the usable project, observed checks and remaining limitations.
If the request includes scientific results, continue with [do-full-research-loop](../do-full-research-loop/SKILL.md); a scaffold alone does not complete that request.
Project creation does not independently authorize publication.
