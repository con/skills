---
name: align-with-stamped-principles
description: Improve an existing project's STAMPED alignment using a scoped baseline assessment, concrete changes, and evidence-based reassessment. Use when asked to add STAMPED or improve a research object's reproducibility practices.
version: 0.1.0
---

# Align an existing research object

Start from the project's intended use and existing stack.
Read [the principles orientation](references/principles.md), consult pinned paper and checklist sources, and inspect the actual object before changing it.

If available, use assess-alignment-with-stamped-principles for the baseline.
Otherwise record the same essential information directly: exact object snapshot and boundary; use case and assumptions; each principle's observed implementation, evidence, judgment, uncertainty, and relevant gap.
Inspecting instructions is different from executing them.
Keep unknowns visible and scientific validity separate from research-object quality.

Choose changes for this use case.
For a static dataset, access, metadata, component identities and modularity may dominate; for transformations, explicit execution and disposable environments may be essential.
Keep normative requirements distinct from the project's priorities and tradeoffs.

Explain what will change, which gap it addresses, and how success will be checked.
Perform authorized, scoped, reversible improvements without adding an unnecessary approval round.
Preserve the project's chosen tooling and working instruction hierarchy.
Introduce another tool only when it addresses a demonstrated gap better than the existing mechanism.
Do not make STAMPED synonymous with a particular package manager, data manager, or hosting service.

Typical changes are a missing component manifest, exact source identities, explicit inputs/outputs, a replay entry point, tracked environment definition, documented host configuration, or an accessible distribution route.
Prefer an executable improvement with evidence over a promise in documentation.
Retain limitations when the ideal is impractical.

When useful, add concise guidance to the existing agent harness at the proper scope: object boundary, established execution and provenance route, where the environment is defined, and how to verify results.
Preserve existing AGENTS.md/CLAUDE.md or other conventions and avoid duplicating their content.
Do not install a skill dependency or write global account configuration merely to add a pointer.
Recommend optional complementary skills only for actual gaps.

Reassess the resulting snapshot using the original criteria.
Link each claimed improvement to a diff and observed check; distinguish implemented and verified, implemented but unverified, planned, blocked, and deferred work.
Preserve failed attempts.
Loop again only for concrete newly discovered defects within scope; stop when the requested improvements are verified or the remaining barrier is documented with a useful next action.
Deliver the before/after assessment and the executable result, not just revised agent instructions.
