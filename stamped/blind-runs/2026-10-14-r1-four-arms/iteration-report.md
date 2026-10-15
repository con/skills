# Iteration report (3 runs)

## Conditions

| condition / model | runs | MUST pass (mean) | spread | oracle | skill read | commits during run |
|---|---|---|---|---|---|---|
| bare / sonnet | 1 | 0.364 | — | 1/1 (100%) | no transcript | no transcript |
| pointer / sonnet | 1 | 0.727 | — | 1/1 (100%) | no transcript | no transcript |
| skill-implicit / sonnet | 1 | 0.909 | — | 1/1 (100%) | no transcript | no transcript |

## Per item

| item | met | partial | unmet | not-checked | n/a | n |
|---|---|---|---|---|---|---|
| may/001 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/002 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/004 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/005 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/006 | 1 | 2 | 0 | 0 | 0 | 3 |
| must/007 | 2 | 0 | 1 | 0 | 0 | 3 |
| must/008 | 2 | 0 | 1 | 0 | 0 | 3 |
| must/009 | 2 | 0 | 1 | 0 | 0 | 3 |
| must/010 | 1 | 1 | 1 | 0 | 0 | 3 |
| must/011 | 0 | 0 | 0 | 3 | 0 | 3 |
| must/012 | 0 | 0 | 0 | 3 | 0 | 3 |
| must/013 | 2 | 0 | 1 | 0 | 0 | 3 |
| must/015 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/016 | 0 | 2 | 1 | 0 | 0 | 3 |
| should/002 | 0 | 0 | 3 | 0 | 0 | 3 |
| should/003 | 3 | 0 | 0 | 0 | 0 | 3 |
| should/006 | 0 | 0 | 3 | 0 | 0 | 3 |

Rates are numerator/denominator; `not-checked` is never folded into a failure.

**Raw counts only, no significance claims.** Repeats are independent per arm, not paired; with three repeats even 3/3 against 0/3 is only p ≈ 0.1 (two-sided Fisher). Per-iteration numbers are smoke thresholds, and a release claim needs the benchmark (about 10 repeats per arm).
