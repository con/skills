# Iteration report (3 runs)

## Conditions

| condition / model | runs | MUST pass (mean) | spread | oracle | skill read | commits during run |
|---|---|---|---|---|---|---|
| skill-explicit / sonnet | 3 | 0.879 | 0.82–0.91 | 3/3 (100%) | no transcript | no transcript |

## Per item

| item | met | partial | unmet | not-checked | n/a | n |
|---|---|---|---|---|---|---|
| may/001 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/002 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/004 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/005 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/006 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/007 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/008 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/009 | 2 | 1 | 0 | 0 | 0 | 3 |
| must/010 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/011 | 0 | 0 | 0 | 3 | 0 | 3 |
| must/012 | 0 | 0 | 0 | 3 | 0 | 3 |
| must/013 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/015 | 3 | 0 | 0 | 0 | 0 | 3 |
| must/016 | 0 | 3 | 0 | 0 | 0 | 3 |
| should/002 | 1 | 2 | 0 | 0 | 0 | 3 |
| should/003 | 3 | 0 | 0 | 0 | 0 | 3 |
| should/006 | 3 | 0 | 0 | 0 | 0 | 3 |

## T1 / T2 disagreements (for the human to settle)

- `stamped-checklist:must/011`: probes say **not-checked**, the blind assessor says **met** — /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r4
- `stamped-checklist:must/012`: probes say **not-checked**, the blind assessor says **met** — /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r4
- `stamped-checklist:should/006`: probes say **met**, the blind assessor says **partial** — /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r5
- `stamped-checklist:must/011`: probes say **not-checked**, the blind assessor says **met** — /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r5
- `stamped-checklist:must/012`: probes say **not-checked**, the blind assessor says **met** — /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r5
- `stamped-checklist:should/006`: probes say **met**, the blind assessor says **partial** — /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r6
- `stamped-checklist:must/011`: probes say **not-checked**, the blind assessor says **met** — /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r6
- `stamped-checklist:must/012`: probes say **not-checked**, the blind assessor says **met** — /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round3/r0-freesurfer-plot--skill-explicit--sonnet--r6

Rates are numerator/denominator; `not-checked` is never folded into a failure.

**Raw counts only, no significance claims.** Repeats are independent per arm, not paired; with three repeats even 3/3 against 0/3 is only p ≈ 0.1 (two-sided Fisher). Per-iteration numbers are smoke thresholds, and a release claim needs the benchmark (about 10 repeats per arm).
