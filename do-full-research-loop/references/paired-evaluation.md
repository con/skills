# Compare skill conditions without contaminating them

Before either arm begins, retain one protocol describing the question, task prompt, fixture/data snapshot, expected outputs, grading criteria, and equal time/token/turn limits.
Record the runtime, model, reasoning effort, tools, permissions, data access, compute limits, network policy, and available human assistance.
Unknown settings stay unknown; do not guess model identity.

Pin the treatment skill tree by immutable revision and scoped digest, including references/scripts.
Keep the task prompt identical apart from the intervention.
The comparison arm must not see the treatment skill or output.
Use fresh contexts and isolated workspaces; if an account-level instruction exposes STAMPED concepts or infrastructure to both arms, record that shared baseline.
Do not call such a comparison entirely unassisted research.

Predeclare two separate criterion sets:

- Scientific: question/data compatibility, variable semantics and units, exclusions and denominators, valid method and implementation, uncertainty, sensitivity/robustness, and whether claims follow from results.
- Research object: seven STAMPED properties assessed with a pinned rubric, evidence, attempted activities, residual gaps, and replay outcomes.

Fix expected values independently when possible.
The treatment's output is not the oracle for grading the comparison.
Hide treatment labels during review where feasible.
Distinguish agent self-report, independent agent review, deterministic checks, and human adjudication.

Record every run, including failed, timed-out, and interrupted runs.
Identify assistance, intervention timing, retries, excluded runs and why; an assisted rescue does not erase the initial autonomous outcome.
Task completion and correctness are separate outcomes.
Equal declared limits do not establish equal actual resource consumption; retain observed usage and its measurement scope, leaving unavailable values null.

Native history, computational/resource logs, and transformation provenance should share a trial identifier while retaining their distinct identities.
A Stop hook is evidence that a turn ended, not that a task succeeded or a skill was used.
A detected skill path is a candidate use; confirm actual material use from the run.
If a completion collector is used, test a real event and retain deduplication IDs, missing-start cases, and known coverage.
Collection failure is distinct from missing object evidence or scientific failure.
Use an explicit end-of-run assessment when no reliable hook exists.

Start with an exploratory pair.
Use its failures to improve the instrument; reruns after changes are new conditions.
For broader claims, repeat matched trials, vary execution order, report sample sizes and uncertainty, and preserve the protocol revisions.
A tiny successful pair establishes neither general efficacy nor causal attribution to any individual instruction.
