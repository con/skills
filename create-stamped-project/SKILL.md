---
name: create-stamped-project
description: Establish a new computational research project with an explicit research-object boundary, component identities, executable workflow, environment specification, and proportionate STAMPED checks. Use for project creation without imposing a domain-specific tool stack.
version: 0.1.0
---

# Create a STAMPED-informed project

Read [the principles orientation](references/principles.md), then consult and pin the paper and checklist sources.
Establish the user's objective, audience, data/access constraints, expected outputs, collaborators, computational scale, and chosen tools.
Inspect supplied examples and the relevant workspace before asking for missing facts.
Prior conversation or shell history is contextual evidence only when authorized and relevant; do not broadly mine private history or turn old messages into new authorization.

Choose the smallest structure that makes the work understandable and executable.
Explain the research-object root, input and output boundaries, module responsibilities, environment definition, provenance mechanism, and retrieval/distribution route.
Modules may be directly included or persistently referenced.
A particular directory tree, version-control implementation, container runtime, or package manager is not a STAMPED requirement.

Create useful working content: a question/use-case record, an inventory of essential inputs and their exact identities/access/license terms, the analysis entry point or smallest runnable slice, a tracked environment definition, and output and provenance locations.
Mark unresolved inputs explicitly; do not claim a runnable study while indispensable data or credentials are missing.
Keep generated outputs outside raw inputs and private access materials outside shareable content.
Record host requirements rather than assuming a laptop's ambient state.

Use the existing project conventions for agent instructions.
Add only the specific boundary, setup, execution, provenance, and validation facts future work needs.
A generic manifesto is not a substitute for a working entry point.

Verify the smallest complete operation from declared inputs through retained outputs and a replay recipe.
Check restoration in a fresh disposable workspace when feasible; preserve the result and logs before removing the workspace.
Do not claim cross-platform portability from a single-host run.

Finish with a baseline assessment across all seven properties, citing observed evidence and separating gaps, unknowns, and deliberate tradeoffs.
If the alignment skill is available, use it with the actual use case and structure; otherwise apply its essential loop directly: assess, choose a scoped fix, implement, check, and reassess.
When the user asked for the completed study, continue through analysis and reporting using an execution workflow rather than stopping at project setup.
