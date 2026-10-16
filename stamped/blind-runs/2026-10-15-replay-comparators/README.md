# Reject unavailable unlocked annex comparators

Source tested: `24564e88d832fc1c8c0911d92f1b943c86ad9b3c`, a separate comparator commit after route-only integration `a1325319dbc5301fa1651c4bd597a2a539b4f756`.
The prior route-only record and failed-get evidence remain unchanged under `../2026-10-15-replay-route/`.

## Change and frozen-base isolation

For small pointer-shaped files, the helper asks native `git annex find` whether the tracked content is missing.
A missing payload returns no comparator hash.
The existing unavailable-comparator gate then returns `not-checked` before removing outputs or executing the entry point.
Arbitrary ordinary text is not rejected solely because it resembles an annex pointer.
Native git-annex comes from the operational Pixi runtime; this is not a new environment dependency.
The pointer size/prefix prefilter follows the upstream pointer representation: <https://git-annex.branchable.com/internals/pointer_file/>.

`comparator-only.patch` contains this correction.
`combined.patch` contains only the route and comparator changes, applied to frozen assessor source `0208f82504f15b82b7582f34143ab889dd52c68d`.
An independent temporary Git index proved that applying it changes only `skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py` and produces the candidate's exact blob.
`frozen-base-proof.json` records the result and SHA256.
Selected assessor and conventions paths have no other changes; no working-skill revisions or evals pin need enter the frozen assessor branch.
Formal adoption remains an explicit coordinator amendment, never implied by this development branch.

## Mechanical and native evidence

`checks/` retains commands and complete streams: 150 ordinary tests, 26 eval cases, 18/18 detected mutants, and 27 skills linted with zero errors and ten existing warnings.
Three added checks cover ordinary pointer-looking text, native unavailable content, and available ordinary payload hashing.
The mocked keep-output test now stubs the new route reader so it reaches its intended assertion instead of passing on an unrelated fake-source error.

`native-verified/` is the final native matrix on isolated synthetic copies with clean starting status.
Source HEAD, status, config, and file bytes or absence remain unchanged.
Unlocked-only unavailable content is null, is named as unavailable, and prevents entry execution.
Available mixed locked/unlocked outputs, available unlocked output, and ordinary non-annex output reproduce byte-for-byte.
Exact commands, all streams and native helper reports are retained.
The `native*_check.py` scripts preserve their actual paths and require the operational Pixi environment plus the user-level commit-provenance resolver for disposable fixture commits.

`native/` and `native-clean-check/` retain earlier matrices rather than silently replacing them.
The first began after a reviewer altered synthetic sources.
The second had restored correct bytes but a cosmetic modified status from annex's stale index metadata.
Native `git annex restage` cleared that metadata; `restaged-status.json` records clean status before the final matrix.

## Independent checks and a failed review

`primary/` retains an independent helper-based review and original native reports.
It observed dirty source working trees, explicitly disclosed them, and verified that clone baselines matched the committed annex key rather than the altered worktree bytes.
It is evidence for committed-HEAD replay behavior, not pristine-source preservation.

The first small-tier reviewer ran `analysis.sh` directly in the shared synthetic sources, contrary to the read-only/helper scope. Its review and command evidence are retained in `small/`; altered bytes/status are retained in `source-mutation/`.
This is an instruction-following failure, with shared mutable test inputs a harness weakness.
It is not counted as a successful skill test.
Only the synthetic unlocked files were restored after capturing their changed state; no study or formal-run object was touched.
No skill prose was changed to hide this failure.

`small-retry/` is a fresh gpt-6-luna/high reviewer with isolated source copies and an explicit helper invocation, without expected outcomes.
The original and revised prompts are retained verbatim.
It independently obtained unavailable unlocked content with no entry execution, and successful available cases.
The clearer prompt means this is a helper-directed retry, not proof that the original small-tier invocation was followable.

Both successful reviewers qualify single-output success: the entry script logs errors while trying to overwrite an unselected locked output but exits zero and reproduces the selected unlocked table.
The all-output replay removes both outputs and succeeds without those errors.
A selected-output `met` is not a claim that the whole workflow is error-free.
Same-host configured access is also not public retrieval, cross-host portability, or scientific validity.
These qualifications and the failed review remain in the record.
