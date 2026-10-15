# Validate the claim and its presentation

Select checks that could expose a consequential mistake; avoid tests that merely restate the implementation.
Reuse established scientific libraries and validators, while keeping the expected result independent of the code under test.

## Scientific checks

- Confirm source meanings and units, selected population, joins, duplicate handling, denominators and missingness.
  Distinguish independent exclusion flags from their unique-row union.
- Check known examples and relevant boundaries: missing-token forms, invalid/nonfinite values, empty groups, unit conversions, unequal counts or weights.
  The task contract determines which cases matter.
- Match uncertainty and resampling to the independent sampling unit.
  Compare paired observations only for a paired design; distinguish descriptive change from a causal effect.
- Use independent summaries, a trusted reference implementation or justified controls; prespecify tolerances.
  Sensitivity analyses test assumptions, not select favorable results.
  Keep actual-data correctness separate from the reusable input contract.

## Useful figures

Choose a compact figure when it clarifies the question; a small table can suffice for a simple result.
Show the relevant individual variation or distribution and uncertainty, rather than only a summary when that hides a material limitation.
Include all predeclared sensitivity variants, with context clearly labeled.

Generate from checked data using established plotting tools.
Retain editable source, generation command and a rendered preview.
Inspect at intended display size: units, labels, legends, clipping, series identity and interval meaning must agree with the checked table.
Parsing SVG or checking file existence is not visual review.
If rendering was unavailable, report that limit rather than crediting a later reviewer to the original worker.

## Fresh replay

In a disposable checkout, obtain exact inputs and restore the recorded environment.
Remove only declared generated outputs, without deleting source data or shared annex content; keep expected artifacts elsewhere.
Run the documented entry point and require at least one regenerated output.
A successful no-op must fail this check.

Compare deterministic artifacts by digest or declared semantic/numeric tolerances. Table identifiers, schema and labels need exact agreement; handle missing/nonfinite values explicitly before numeric comparisons.
Pixel differences may reflect rendering rather than changed data; inspect the actual figure separately.

Record the environment, platform, caches and external services used.
A fresh checkout is not a different host; rebuilding the scientific result is not automatically rebuilding every report or validating native provenance discovery.
Retrieve original outputs and requested logs separately when testing delivery; metadata availability does not prove payload retrieval.
