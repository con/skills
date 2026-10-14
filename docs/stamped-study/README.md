# STAMPED skills: pinned exploratory study

The experimental bundle is [commit `8f3acaa4a7c353b6c8ea6928c278478f95328fc5`](https://github.com/con/skills/tree/8f3acaa4a7c353b6c8ea6928c278478f95328fc5), with all five skills at `0.1.0`.
This documentation delivery preserves those five trees exactly.
The four core workflows remain tool-neutral; domain and tool preferences remain in the ReproNim creation adapter.
See the [skill index](../../README.md#stamped-research-skills-experimental) for their distinct scopes.

## Study and source identities

Three sequential baseline/treatment pairs tested additional procedural guidance in preconfigured research projects, with common scientific tasks, locked tools, offline STAMPED references, account controls, `gpt-6-astra`/`ultra`, and 480-second worker caps.
Treatment read the five pinned entrypoints and applied selected steps; baseline already had substantial research and provenance guidance.
Treatment ran first in stages 01/02; baseline ran first in stage 03.
A bounded amendment for changed shared model defaults preserved the explicit worker model/effort overrides; it did not establish constant account history.
The coordinator confirmed all six workers stopped before this documentation continuation; none received post-stop repairs.

The replacement study used [OpenNeuro ds000005 at `b094fc2f41487f92d382a1a432165ae58caae386`](https://github.com/OpenNeuroDatasets/ds000005/tree/b094fc2f41487f92d382a1a432165ae58caae386): 48 event files, 16 participants, and 4,096 rows.
It describes recorded response times across runs, not MRI processing or the original loss-aversion model.
The originally proposed ABCD reproduction was not performed because access was unavailable; an ambiguous Flanker candidate was rejected before experimental launch.

The design pass consulted these immutable sources:

| Source | Revision / role |
| --- | --- |
| [STAMPED paper](https://github.com/stamped-principles/stamped-paper/tree/310eefa1bd756a04d69161c216d93af4d354dd05) | `310eefa1bd756a04d69161c216d93af4d354dd05`; detailed normative principles. |
| [Principles schema](https://github.com/stamped-principles/stamped-principles-schema/tree/929e87db4e1248aa6b3b32c368da9e825137175e) | `929e87db4e1248aa6b3b32c368da9e825137175e`; principles data 0.2.0. |
| [Checklist schema](https://github.com/stamped-principles/stamped-checklist-schema/tree/8826b99e15f1db1cc2f0d691d892786a4bb51815) | `8826b99e15f1db1cc2f0d691d892786a4bb51815`; checklist 0.3.1. |
| [Checklist UI](https://github.com/stamped-principles/stamped-checklist/tree/d24d7ca0515efa6ed639ef2844c351c8e5471154) | `d24d7ca0515efa6ed639ef2844c351c8e5471154`; response format 3. |
| [Agent-skill discussion](https://github.com/stamped-principles/stamped-agent-skills/tree/a723c24585799e121c3f5ba046b1f50901492719) | `a723c24585799e121c3f5ba046b1f50901492719`; scope and decomposition. |
| [Assessment model](https://github.com/stamped-principles/stamped-skills-assessment/tree/c4c0428e6962a631d910d0becb00b7bb1c3c903c) | `c4c0428e6962a631d910d0becb00b7bb1c3c903c`; evidence/review distinctions. |
| [Examples](https://github.com/stamped-principles/stamped-examples/tree/5944d90004fbaa5e992d2764728cfd6992b8b12f) | `5944d90004fbaa5e992d2764728cfd6992b8b12f`; illustrative, with curation states preserved. |

The [module manifest](logs/manifest.json) records the checked report, design notes, three final assessments/reviews, candidate review, DataLad audit, and export-plan identities.
Its five treatment-tree SHA-256 values match both stage-01 and stage-03 manifests and the historical Git trees.
The earlier draft artifact manifest predates Snapper formatting and is not the experimental tree pin.
Paper/schema identifier and licensing-requirement differences remain source-qualified.

The [full report][report], [design notes][design], and [final stage assessments][evaluations] are coordinator publication targets on the study review branch; their checked local bytes are identified in the manifest, and final upload/retrieval verification remains coordinator work.
The design notes' statement that evaluation was pending describes the earlier implementation pass; the completed report and final assessments govern this summary.

## What was checked

| Pair | Numerical checks on each original and replay | Direct scientific command replay |
| --- | --- | --- |
| [01: one participant][stage01] | 33 scalar comparisons and 171 rows; median change −11 ms. | Four scientific files byte-identical in each arm. |
| [02: cohort][stage02] | 489 scalar comparisons and 4,096 audited rows; mean within-person median change +31.34375 ms, 95% bootstrap interval [−70.284375, 132.6578125] ms. | Nine baseline and six treatment derivative files byte-identical. |
| [03: sensitivity][stage03] | 2,042 scalar comparisons, 4,096 rows under two rules, and 192 variant/run summaries; all four intervals include zero. | Seven regular files per arm plus treatment's separately verified annexed bootstrap table; all 40,000 replicate values checked. |

These are descriptive response-time results, with differential missingness and run/task composition limiting interpretation.
They do not establish causal practice, fatigue, learning, or loss-aversion effects.

**Stage 03 treatment failed an independent screening-contract check.**
Identical 15-case probes found `N/A` and ` n/A ` labeled `invalid_numeric_rt` instead of `missing_rt`, contrary to the frozen case-insensitive requirement; baseline passed the probes.
The two cases caused eight failed flag comparisons across the primary/band modes.
Those variants are absent from the pinned data, so numerical endpoints and command replay still passed.
The worker defect remains unrepaired; complete output-contract success is not claimed.

Fresh coordinator replay removed scientific outputs, used new checkouts and locked environment prefixes, and regenerated results on the same host with shared caches and permitted public acquisition.
This does not demonstrate offline dependency closure, another platform, or complete report-builder replay.
The stage-03 annex payload was separately attached by the coordinator; the original snapshot's targetless annex link was preserved.

**Native DataLad rerun is a separate, unresolved integration result.**
Stage-01 treatment and both stage-03 arms retained transformation records, but installed DataLad 1.7.1 requires `[DATALAD RUNCMD]` at the very beginning of the commit message.
Mandatory Conventional Commit subjects prevent native discovery; placing the marker later in the message does not satisfy that parser.
Direct command replay passed, but retained record bytes do not demonstrate successful native `datalad rerun`.
Neither stage-02 arm recorded a DataLad transformation.
The [read-only parser audit][datalad] preserves the incompatibility without patching workers or granting a commit-policy exception.

**Research-object judgments remain separate from numerical and replay checks.**
All six assessments judged scoped Actionability and Modularity demonstrated, and Self-containment, Trackability, Portability, Ephemerality, and Distributability partial.
There is no aggregate score; matching coarse judgments conceal different evidence and gaps.
Treatment added explicit protocol/assessment records and took longer in each pair; this is not a causal cost or efficacy estimate.
Assessment was unblinded by the study designer/reference implementer, without independent human review; shared-account logical isolation and one pair per stage further limit inference.
Reading five entrypoints in supplied seeds does not validate from-empty creation, every complete skill workflow, a full ReproNim adaptation, HPC, or an imaging pipeline.

## Validation and reuse limits

The design pass's focused checks covered local links, metadata, Python syntax, schema invariants, checklist coverage/version refusal, five-state mapping, UTF-16 limits, and URL round trips on synthetic fixtures.
The repository validator checked the five skills with zero errors and five optional `allowed-tools` warnings.
The stock skill-creator validator rejects the top-level `version` required here; canonical files retain `version: 0.1.0`.
These are structural/helper checks, not proof of scientific truth or every workflow.

The optional formal-validation route requires `jsonschema>=4,<5`.
Stage-01 treatment could not execute its assessment validator or Workshop recorder because that prerequisite was missing; the failures remain failed.
Later stages recovered using an already installed Workshop environment, without repairing stage 01.
Passing the experimental schema/bookkeeping contract does not establish upstream assessment-package compatibility.
Stage-02 treatment also left two stdout files and a feedback lock untracked; the stopped snapshot retained them.

This experiment exposed source directories directly; it did not validate APM packaging, installation, frozen restoration, or audit.
No complete APM installation contract is claimed.
The dataset declares PDDL v1.0 and attribution to Tom et al. (2007); those terms do not license new code or these skills.
Repository licensing remains TBD, and unresolved upstream/new-code permissions and independent-recipient delivery remain unresolved.

## Related candidate reviews

The [pinned candidate review][candidates] considered these alternatives without adopting their implementations or changing the treatment:

| Candidate | Reviewed head | Scope |
| --- | --- | --- |
| [PR 23](https://github.com/con/skills/pull/23) | `15da761f63a5a45c507e6596a549720bd43a1e84` | Assessment/alignment instruction pair; reported structural checks, no reported real-project execution. |
| [PR 24](https://github.com/con/skills/pull/24) | `99e8240fdf49b6184b23dc64e3e911376ea3eb3c` | Planning/evaluation documents; no implemented STAMPED entrypoints. |
| [PR 26](https://github.com/con/skills/pull/26) | `664d48bafca7e05d942707713bd896f95932b3a4` | Four workflow skills plus conventions, probes, templates, tests, and saved evaluations; no ReproNim creation entrypoint. |

Candidate-reported test/agreement numbers were not independently reproduced.
A separate coordinator no-op control confirmed that PR 26's pinned replay detector could accept an unchanged pre-existing output after running `true`.
That specific defect check was not a study arm or a general candidate-efficacy verdict.
None of these candidate workflows was validated by the three trial pairs.

## Complete finished development records

[The duct archive](logs/duct/) contains 18 completed captures, 90 files, and 291,226 bytes from the coordinator's intermediate skill-development exports.
Every existing metadata file, stdout/stderr stream, and resource-sample file is preserved byte-for-byte, including failed attempts and historical paths.
Seventeen captures match export plan/report 02; the later completed stage-03 provenance audit is absent from that plan and is separately marked in the [manifest](logs/manifest.json), with direct central-source/intermediate hash verification.
Each file records its central source, intermediate export, final relative path, SHA-256, and size.

Two captures have nonzero exit status; failed subcommands can also appear inside successful captures.
There are no missing stdout/stderr files, eight empty stdout/stderr streams, and one empty resource-sample file.
No stdin was captured or invented.
Local duct resource samples measure monitored local processes, not remote model compute.
Agent-native histories, command captures, and DataLad records establish different evidence.

The current outer native documentation invocation is still running and is **not** included as a completed capture.
The coordinator will export it after this worker stops in a separate curation commit and verify uploaded code/checkpoint references.
Later log packaging, replay, or publication checks do not repair historical worker outcomes or count as worker-produced quality.
Private native transcripts, user configuration, credentials, raw retrieval trees, and private Workshop memory are outside this delivery.

[report]: https://github.com/leej3/stamped-ai-research/blob/codex/stamped-poster-study/research/REPORT.md
[design]: https://github.com/leej3/stamped-ai-research/blob/codex/stamped-poster-study/research/skill-drafts/design-and-validation.md
[evaluations]: https://github.com/leej3/stamped-ai-research/tree/codex/stamped-poster-study/research/mixed-gambles-design/evaluator
[stage01]: https://github.com/leej3/stamped-ai-research/blob/codex/stamped-poster-study/research/mixed-gambles-design/evaluator/stage-01/review.md
[stage02]: https://github.com/leej3/stamped-ai-research/blob/codex/stamped-poster-study/research/mixed-gambles-design/evaluator/stage-02/review.md
[stage03]: https://github.com/leej3/stamped-ai-research/blob/codex/stamped-poster-study/research/mixed-gambles-design/evaluator/stage-03/review.md
[datalad]: https://github.com/leej3/stamped-ai-research/blob/codex/stamped-poster-study/research/mixed-gambles-design/evaluator/conventional-datalad-note.md
[candidates]: https://github.com/leej3/stamped-ai-research/blob/codex/stamped-poster-study/research/skill-candidates/REVIEW.md
