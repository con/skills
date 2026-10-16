# Bounded fresh-replay check: small source

The README documents `python analysis.py` as the entry and names
`results/group_summary.csv` as the generated product. It says the PNG and
reference PDF are supplied assets. I therefore selected only
`results/group_summary.csv` for the helper comparison.

The required first invocation omitted output selection. It returned exit code
2 during argument parsing and did not create a clone or JSON report. Its exact
response is retained in `first-response.stderr` (stdout is empty):

> fresh_rerun.py: error: the following arguments are required: --outputs

The explicit-selection replay returned exit code 0 and status `met`. DataLad
cloned the local source, removed and committed the shipped CSV in the disposable
clone, then ran `python analysis.py`. The output checksum before replay was
`a30f49691c25142d9114d2150c55ce809e23019301fdd23c7e08482cfbee0acd`; the helper
reports it under `comparison.identical`. It reproduced one selected output
byte-for-byte. The run occurred on the same host as the source; no container
runtime was used. The helper's native report is `fresh-rerun.json`.

The following source, input, and reference files remained in the clone and
matched the source byte-for-byte by SHA-256: `README.md`, `analysis.py`,
`input/participants.tsv`, `results/reference-atlas-cache/manual.pdf`, and
`skills/example/assets/icon.png`. The selected generated CSV was recreated in
the clone. Its regenerated file is untracked after replay, as shown by the
clone's `git status --short` output (`?? results/group_summary.csv`).

Tool friction was the required `--outputs` argument: the help text states
`--outputs OUTPUTS [OUTPUTS ...]`, and the first attempt failed with the quoted
error above. The README's execution instruction, “Run `python analysis.py`,”
was usable as the entry point. This is only a bounded replay check; it does not
infer checklist verdicts or a scientific result.
