# Instruction friction

The main assessment steps were executable from the supplied snapshot: the checklist pin check passed, the probes ran, and the response validator accepted all 31 items. A few instructions required interpretation or extra work:

- **Probe scope versus delivery scope.** The skill says probes “do not inventory the whole delivery” and directs the assessor to inspect omitted artifacts, while the generated probe set read only the two tracked paths. This produced several misleading drafts: `entry-point` missed the supplied README and script, and `derived-have-records` called the input CSV a derived file. I checked the receipt, original Git status, and all delivered files and corrected those answers. It would help if probe output foregrounded that tracked-only boundary and named likely false positives.
- **Untracked delivered state.** The required evidence review says to include “uncommitted and ignored scientific artifacts,” but does not specify a canonical way to cite those artifacts alongside a stop receipt. I cited the receipt and the delivered paths, and kept worker state separate from the supplied preservation record.
- **Stop-state completeness.** The skill asks assessors to identify “any omissions from the capture,” but the receipt does not say whether its file list is exhaustive or whether separate run records ever existed. I treated the listed delivered files as the capture boundary and report that no run record is present within it; I did not infer that none existed outside the capture.
- **Remote check trigger.** The instruction says to run `--check-remote` whenever a linked module exists. Here the README says `component.py` was copied from an upstream project, but its URL and revision were lost. No remote could be resolved or checked. I reported the upstream component as unresolvable from the delivered evidence rather than treating the probe's “no submodules” result as a pass.
- **Assessment identity.** The stamping step requires harness and model metadata and says to record unavailability rather than guess. The subagent interface did not expose exact versions, so I recorded that limitation in both fields. The report schema could make unavailable identity a structured value rather than free text.
- **No live user.** The rule for a blind run is clear: label goals and kind as assumptions and continue. I applied it, using the README's stated task and classifying the object as a study.

## Checked

I read the case prompt, supplied assessment and conventions skills, all cited conventions references, checklist pin, stop receipt, README, scripts, requirements, input, and result. I ran the pin check and all configured probes. I inspected the object’s Git history, tracked paths, status including ignored paths, and configured remotes; validated the completed response; and generated the checklist URL. The scientific check was arithmetic by inspection. I did not run the workflow.

## Not checked

No replay or fresh-environment test was requested. There is no configured Git remote or linked module URL to verify, no reachable issue tracker, and the README does not preserve the upstream identity of `component.py`. I did not inspect unrelated cases, repositories, or records, and did not determine whether any evidence was omitted before the supplied stop receipt.
