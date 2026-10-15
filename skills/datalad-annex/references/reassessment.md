# Choose what changes

Select the comparison before choosing a replay command.
The [worked guide in PR39](https://github.com/stamped-principles/stamped-examples/blob/e3b7fe237a6c2954fc67d8161394b6d9a24fef6e/content/guides/choosing-what-changes.md) illustrates these choices.

| Question | Hold fixed | Change |
| --- | --- | --- |
| Recover an earlier result | Recorded data, code and dependency selection | Rebuild the installation on a compatible host |
| Reassess new data | Code and dependency selection | Input data |
| Test a code change | Data and dependency selection | Implementation |
| Test updated dependencies | Data and code | Package selection; state whether requirements also changed |
| Rebuild from requirements | Data, code and declared requirements | Fresh installation, optionally a new solve |
| Test portability | Data, code and scientific checks | Host and compatible platform-specific packages |

Record revisions, input identities, the selected environment and host.
Hold other conditions fixed where possible; report unavoidable differences.
Compare scientific invariants or declared numerical tolerances; require identical bytes only where meaningful.
Retrieve retained annex inputs to recover old data; a new upstream download can change the data.

Disposable installations expose hidden state and ease cleanup.
Flexible requirements support reuse on changing systems; retained dependency selections aid historical recovery.
A fresh solve tests current availability and may select different versions.
Locks cannot guarantee future package availability or compatibility on another host; retaining package or container artifacts improves recovery at a storage cost.
Choose the trade-off for the question instead of requiring exact reconstruction for every reassessment.

`datalad rerun RUN_REV` normally applies the recorded command to the current checkout.
Select data, code and dependencies separately; restoring environment files must not overwrite the code change being tested.
For fixed Pixi dependencies, restore the matching manifest and lock from the retained snapshot and use `pixi install --locked -e <recorded-env>`.
Use the explicit calculation command when restoring an older manifest would also replace newer task definitions.

An outer `pixi run` selects its environment before DataLad changes revisions; a checkout does not update a running interpreter.
Select the intended state before launching, or record an explicit inner Pixi invocation that synchronizes after the transition.
For a sequence of historical runs, account for environment changes between revisions.
Record the calculation, not a named task that recursively invokes `datalad run`.
