# Oracle for R0

ds007116 ships `derivatives/freesurfer-post/*_desc-FreeSurfer_qc.tsv` in plain
git, so the values the task asks for are already in the inputs.

**At this rung that is allowed**: R0 exists to exercise the layout, the run
records and the environment spec, not the computation. From R1 on, the agent
has to compute, and the shipped derivatives serve only as the oracle — a rule
`check_r0.py --forbid-shipped-as-result` enforces for the later rungs.

`check_r0.py` checks the science product, not the STAMPED properties:

- a table exists with one row per session, carrying an age and a volume;
- at least `--min-sessions` sessions (default 50) are covered;
- ages fall in the range ds007116 actually has (8–21 years);
- brain volume correlates positively with age over this age range, which is the
  finding the plot is supposed to show;
- a figure file exists and is not empty.

It deliberately does **not** check the plot's appearance: a figure that exists
and a table that holds the right numbers is as far as a scripted oracle goes.
