# Explicit generated-output selection

The replay helper previously selected every TSV, CSV, PNG and PDF recursively when the caller omitted `--outputs`.
This included participant inputs and reference assets in a formal assessment attempt; the coordinator retained that failed attempt as infrastructure evidence.
This record reproduces the defect with synthetic data, without copying the scientific study.

The helper now requires nonempty explicit output selections before cloning or deleting files.
The working skill example includes that argument, and the evaluation harness requires and forwards `--fresh-rerun-outputs`.
There is no inferred output directory or changed scoring rule.
A caller must still identify actual generated products: even `results/` contains a supplied reference PDF in this fixture.

## Source identity and formal boundary

- Helper-only commit: `a9202fe69e726a816c9bb2ae9e660860c8bf1ff0`.
- Reviewed snapshot, including the working example: `4ca147e7060640219c0270fb51d2721a74fcb82c`.
- Helper SHA-256: `928a3aa24c56c58b78c77066271bfdbc99ab05b60f5226c99baa385471703a49`.
- `source.bundle` contains both new source commits and requires preceding source `a1a9bcfb81a91cf731a4378fd11c415caadd6637`.
- `helper-only.patch` applies to frozen assessor `b86e37ff9115e37541fd47aca73f49e13b5110bb`.
  An independent temporary index confirmed that only `fresh_rerun.py` changes and its resulting blob exactly matches the reviewed helper; see `frozen-base-proof.json`.

This integration does not change formal source/runtime/procedure pins.
The coordinator owns the wrapper, complete judge-chain rehearsal and explicit assessment amendment.
Historical failures and judgments retain their original identities; these bounded checks do not establish a formal assessment result.

## Native regression

`native_check.py`, exact commands and captured output in `native/commands.json`, reports and `native/summary.json` retain the three cases.
The clean synthetic source is commit `9f415de61bb5806b7edbca1a6bba4ec35e394b6e`; its tracked files are copied under `fixture/`.
Its entry is `python analysis.py`; its sole generated output is `results/group_summary.csv`.
The PNG/PDF fixture assets are synthetic placeholder bytes, never parsed as images/documents.

1. Old default: removes the participant input, generated CSV, PNG asset and reference PDF in the disposable clone; execution fails on the absent input, native status `unmet`.
2. New omitted selection: exits 2 with an actionable parser error, before a workdir/clone/report or analysis execution exists.
3. New explicit CSV selection: native `met`, one byte-identical regenerated output, participant input and both reference assets preserved in the clone.

Source HEAD, clean status and all tracked file hashes stayed unchanged.
This is a same-host replay check; it establishes neither scientific validity nor cross-host portability.

## Independent followability

`primary-prompt.txt` and `small-prompt.txt` are the exact isolated review prompts.
Both fresh reviewers received the same pinned skill plus conventions and separate copies of the synthetic source, without repository history, earlier reports or the fixture test script.
The primary reviewer used the inherited model tier; the second used requested `gpt-6-luna` with high reasoning effort.
The primary reviewer explicitly did not independently resolve its runtime/model identity; none is inferred here.
Their unchanged reports, commands, stderr and native JSON are retained under `primary/` and `small/`.
Disposable Git clones are left at the local paths recorded by the reviewers rather than copied into this record.

Both observed the required omission rejection, interpreted the README and actual code, selected only the generated CSV, reproduced it and preserved the source/input/reference assets.
No implementation discrepancy was found.
The remaining need to identify output semantics is a declared caller responsibility, not a parser guarantee; the lack of JSON on argument rejection requires retaining stderr and exit status.
Full-checklist instructions were deliberately outside this bounded helper exercise; neither review is graded as a complete assessment.

## Mechanical checks

`checks/` retains exact argument vectors, exit status and output for each check.
There were 156 passing ordinary tests (28 skipped), 26 passing eval cases, 18/18 detected judgement mutants, and structural lint of 27 skills with zero errors and ten existing warnings. Tests include omitted/empty/blank output rejection before subprocess execution and evaluation-harness forwarding.
Captured prompts, reports and logs are preserved verbatim; only this authored overview is formatted.
