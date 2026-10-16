# Assessment friction

The strongest practical friction was that probe output was not a complete inventory of the delivered state. The supplied skill says, “Start with the supplied delivery inventory and documentation; use Git history and tracked-path probes where applicable, then inspect artifacts and execution records they omit, regardless of names or layout.” That instruction was necessary here: `entry-point` reported no script because `analysis.py` was untracked, and `derived-have-records` treated the tracked input as derived while the actual result was ignored. The original stop receipt resolved both; reading only probe summaries would have produced wrong answers for must/006 and must/008.

The replay boundary is clear but leaves an intentional gap: “Replay is optional and separate because it executes the workflow.” The task asked for an assessment and explicitly said no replay was requested, so the fresh-environment item remains `not-checked`; a separate authorized replay with a suitable numerical comparison would settle it. Likewise, should/009 cannot be settled from the supplied files because access restrictions are not stated.

The provenance requirement says, “Use harness-provided identity or an approved host resolver for model and runtime metadata; if unavailable, record that explicitly rather than guessing.” No exact runtime or model identifier was exposed to this subagent, so the report and response record that limitation. This is accurate but makes the stamp less precise than the template otherwise expects.

The issue-tracker step says to inspect “the project's own issue tracker, TODOs and `AGENTS.md`/`CLAUDE.md`” and explains how to proceed if the tracker is unreachable. The object has no configured Git remote and the complete delivered inventory contains no TODO, `AGENTS.md`, or `CLAUDE.md`; therefore there was no project tracker to inspect. Stating this in the scope is workable, though a standalone object cannot distinguish “no tracker exists” from a tracker that was never linked.

## What I checked

- Read the supplied assessment skill, its co-located `stamped-conventions` snapshot, checklist pin and report schema; the vendor check passed for checklist 0.3.1.
- Read the original stop receipt, all delivered object files including the ignored JSON result, and Git status/history/configuration. The receipt reports `analysis.py` and `requirements.txt` untracked and `products/estimate.json` ignored; the repository has one seed commit and no remote.
- Ran the supplied probe suite with `--check-remote`. It found no linked modules, so there were no module URLs to contact. Inspected probe details and corrected the answers where the tracked-path view missed delivered files.
- Read the CSV values and JSON result and inspected the script and requirement line. The finite values are 2, 4, 6; the stated count and mean match the JSON. I did not execute the script.

## What remains unchecked

- No fresh-environment or pipeline replay was run. No result comparison beyond the requested count and arithmetic mean was performed.
- Whether any component is access-restricted is unstated.
- The project issue tracker could not be identified because no remote is configured.
- Exact Codex runtime and model identifiers were unavailable to this assessment harness.
