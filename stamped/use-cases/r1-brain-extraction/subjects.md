# The ten subjects, and why these ten

Chosen by the selection rule in `use_case.yaml`: of the 128 ds007116 subjects
that have a `ses-1` `rec-normrefaced` T1w, a `ses-1` age, and a shipped
FreeSurfer `qc.tsv` to compare against, sort by age (ties by subject id) and
take ranks `round(i·(n−1)/(N−1))`. Deterministic, so every arm and every
repeat sees the same ten and two iterations can be compared.

| subject | age at ses-1 |
|---|---|
| `sub-23113` | 8.69 |
| `sub-20919` | 9.96 |
| `sub-21161` | 10.69 |
| `sub-21146` | 11.27 |
| `sub-20336` | 11.92 |
| `sub-22670` | 13.04 |
| `sub-21035` | 13.69 |
| `sub-21493` | 14.44 |
| `sub-20902` | 15.23 |
| `sub-23676` | 16.70 |

Re-derive with `python3 oracle/select_subjects.py <path to a ds007116 clone>`.
