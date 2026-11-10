# CRediT Roles — Canonical Reference

The **Contributor Roles Taxonomy** (CRediT) is the NISO/ANSI Z39.104-2022
standard for attributing contributions to scholarly works. There are
exactly **14 roles**. Each has a stable URI that goes into machine-readable
records (JATS XML, JSON-LD, RDF).

**Vocabulary URI**: `https://credit.niso.org/`

When rendering or validating, role names MUST match one of the canonical
strings below (case-sensitive comparison after Unicode-normalising dashes
and the ampersand). The renderer accepts a few common variants (ASCII
hyphen for the en-dash, "and" for "&") and normalises on output.

## The 14 Roles

| # | Term (canonical) | URI suffix | Brief |
|---|------------------|-----------|-------|
| 1 | Conceptualization | `conceptualization` | Ideas; formulation or evolution of overarching research goals and aims. |
| 2 | Data curation | `data-curation` | Management activities to annotate, scrub, and maintain research data for initial use and later re-use. |
| 3 | Formal analysis | `formal-analysis` | Application of statistical, mathematical, computational, or other formal techniques to analyse or synthesise study data. |
| 4 | Funding acquisition | `funding-acquisition` | Acquisition of the financial support for the project leading to this publication. |
| 5 | Investigation | `investigation` | Conducting a research and investigation process, specifically performing the experiments, or data/evidence collection. |
| 6 | Methodology | `methodology` | Development or design of methodology; creation of models. |
| 7 | Project administration | `project-administration` | Management and coordination responsibility for the research activity planning and execution. |
| 8 | Resources | `resources` | Provision of study materials, reagents, materials, patients, laboratory samples, animals, instrumentation, computing resources, or other analysis tools. |
| 9 | Software | `software` | Programming, software development; designing computer programs; implementation of the computer code and supporting algorithms; testing of existing code components. |
| 10 | Supervision | `supervision` | Oversight and leadership responsibility for the research activity planning and execution, including mentorship external to the core team. |
| 11 | Validation | `validation` | Verification, whether as a part of the activity or separate, of the overall replication/reproducibility of results/experiments and other research outputs. |
| 12 | Visualization | `visualization` | Preparation, creation and/or presentation of the published work, specifically visualisation/data presentation. |
| 13 | Writing – original draft | `writing-original-draft` | Preparation, creation and/or presentation of the published work, specifically writing the initial draft (including substantive translation). |
| 14 | Writing – review & editing | `writing-review-editing` | Preparation, creation and/or presentation of the published work by those from the original research group, specifically critical review, commentary or revision — including pre- or post-publication stages. |

Definitions abridged from the NISO standard. The full URI for each role is
`https://credit.niso.org/contributor-roles/<URI suffix>/`.

## Degree of Contribution (Optional)

CRediT optionally allows annotating each role with a degree of contribution:

- `lead` — primarily responsible for that role on the work
- `equal` — shares the role equally with one or more other contributors
- `supporting` — assisted but did not lead

This shows up in the rendered prose as e.g. *"...A.B. (lead), C.D. (supporting)"*
and in JATS XML as `<role specific-use="lead">…</role>` (per JATS4R guidance).

## Sources

- <https://credit.niso.org/>
- <https://credit.niso.org/implementing-credit/>
- <https://jats4r.niso.org/credit-taxonomy/>
- <https://zenodo.org/records/18421449> (example research tasks per role)
- ANSI/NISO Z39.104-2022
