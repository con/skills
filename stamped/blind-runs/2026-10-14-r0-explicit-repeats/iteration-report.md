# Iteration report (3 runs)

## Conditions

| condition / model | runs | MUST pass (mean) | spread | oracle | skill read | commits during run |
|---|---|---|---|---|---|---|
| skill-explicit / haiku | 1 | 0.727 | — | 1/1 (100%) | no transcript | no transcript |
| skill-explicit / sonnet | 2 | 0.818 | 0.73–0.91 | 2/2 (100%) | no transcript | no transcript |

## Per item

| item | met | partial | unmet | not-checked | n/a | n |
|---|---|---|---|---|---|---|
| may/001 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/002 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/004 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/005 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/006 | 1 | 0 | 2 | 0 | 0 | 3 |
| must/007 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/008 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/009 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/010 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/011 | 0 | 0 | 0 | 3 | 0 | 3 |
| must/012 | 0 | 0 | 0 | 3 | 0 | 3 |
| must/013 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/015 | 1 | 0 | 0 | 2 | 0 | 3 |
| must/016 | 0 | 3 | 0 | 0 | 0 | 3 |
| should/002 | 0 | 1 | 2 | 0 | 0 | 3 |
| should/003 | 3 | 0 | 0 | 0 | 0 | 3 |
| should/006 | 1 | 0 | 2 | 0 | 0 | 3 |

Rates are numerator/denominator; `not-checked` is never folded into a failure.

**Raw counts only, no significance claims.** Repeats are independent per arm, not paired; with three repeats even 3/3 against 0/3 is only p ≈ 0.1 (two-sided Fisher). Per-iteration numbers are smoke thresholds, and a release claim needs the benchmark (about 10 repeats per arm).
