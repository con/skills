# STAMPED orientation and source discipline

STAMPED describes operational properties along spectra.
Choose proportionate improvements for the intended use; do not turn it into a universal tool stack or a certificate of scientific validity.

| Property | Evidence to seek | Common overclaim to avoid |
| --- | --- | --- |
| Self-containment | Explicit object boundary and reachable essential components, including referenced inputs and license declarations | Everything must be copied into one directory |
| Tracking | Exact component states and modification/transformation provenance, including environments | A repository exists, so all results are tracked |
| Actionability | Sufficient replay instructions, preferably executable, plus observed checks | A command is written down, so it has succeeded |
| Modularity | Independently understandable components, explicit interfaces, separable access and license conditions | More directories or submodules necessarily improve reuse |
| Portability | Declared host assumptions and versioned environment definitions; checks on named platforms | A container or a lockfile proves universal portability |
| Ephemerality | A fresh disposable execution environment with retained outputs and provenance | Raw data, results, or scientific history should be thrown away |
| Distributability | Intended recipients can retrieve identified versions through durable routes with usable terms | A digest, public URL, or current local copy guarantees future access |

The authoritative detailed requirements are in the [STAMPED paper](https://github.com/stamped-principles/stamped-paper/blob/main/main.tex).
Use the [principles data](https://github.com/stamped-principles/stamped-principles-schema) and [checklist](https://github.com/stamped-principles/stamped-checklist-schema) as versioned assessment inputs, not silently interchangeable copies of the paper.
Record retrieval date, exact revision, path, and content digest; retain the materials needed to inspect an assessment where licensing permits.

If online retrieval is unavailable, use a supplied or project-pinned version and say which version was actually inspected.
Do not claim to have read the latest version.
Preserve comparisons against a fixed reference bundle.

Design basis inspected 2026-10-14:

- Paper: `310eefa1bd756a04d69161c216d93af4d354dd05`, `main.tex`.
- Principles: `929e87db4e1248aa6b3b32c368da9e825137175e`, data version `0.2.0`.
- Checklist: `8826b99e15f1db1cc2f0d691d892786a4bb51815`, data version `0.3.1`.
- Existing assessment design: [stamped-skills-assessment](https://github.com/stamped-principles/stamped-skills-assessment/tree/c4c0428e6962a631d910d0becb00b7bb1c3c903c).

These sources differ: the paper includes newer licensing requirements and folds component-version capture into T.4; principles/checklist data still use T.5.
Retain the source-qualified identifier and explain the mapping.
Never silently reassign an old criterion to a new statement.

Selected [STAMPED examples](https://github.com/stamped-principles/stamped-examples/tree/5944d90004fbaa5e992d2764728cfd6992b8b12f) illustrate fresh reproducer workspaces, module composition, and executable provenance.
Inspect their curation/verification state and test commands before relying on them.
The uncurated DataLad rerun example conflates ephemeral execution with disposable derived data; follow the paper's meaning above.
