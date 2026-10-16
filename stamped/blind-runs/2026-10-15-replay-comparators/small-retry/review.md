# Small replay-only checks

The three runs used the assessment helper from snapshot commit
`24564e88d832fc1c8c0911d92f1b943c86ad9b3c`. Each `--path` source was cloned
by `fresh_rerun.py` into its separate `--workdir`; `analysis.sh` was invoked
only inside those disposable clones. These are same-host, local-path replays,
not checks of retrieval from a published URL or of portability to another
host. No checklist or scientific evaluation was performed.

## Exact commands

```sh
pixi run --manifest-path /Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml python /tmp/stamped-replay-comparator-review/snapshot/skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py --path /tmp/stamped-replay-comparator-review/small-retry-input/target --entry 'sh analysis.sh' --outputs 'results/unlocked.tsv' --workdir /tmp/stamped-replay-comparator-review/small-retry/target-unlocked -o /tmp/stamped-replay-comparator-review/small-retry/target-unlocked/report.json

pixi run --manifest-path /Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml python /tmp/stamped-replay-comparator-review/snapshot/skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py --path /tmp/stamped-replay-comparator-review/small-retry-input/absent --entry 'sh analysis.sh' --outputs 'results/unlocked.tsv' --workdir /tmp/stamped-replay-comparator-review/small-retry/absent-unlocked -o /tmp/stamped-replay-comparator-review/small-retry/absent-unlocked/report.json

pixi run --manifest-path /Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml python /tmp/stamped-replay-comparator-review/snapshot/skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py --path /tmp/stamped-replay-comparator-review/small-retry-input/target --entry 'sh analysis.sh' --outputs 'results/*.tsv' --workdir /tmp/stamped-replay-comparator-review/small-retry/target-all-tsv -o /tmp/stamped-replay-comparator-review/small-retry/target-all-tsv/report.json
```

## Results and interpretation

- `target` with `results/unlocked.tsv`: `met`. The helper fetched and removed
  the shipped comparator, ran the entry point in the clone, and reported the
  regenerated TSV identical to its baseline. The entry log also contains two
  `Permission denied` messages for `results/locked.tsv`; the selected output
  still matched, so the helper's one-output result is `met`. The log does not
  establish the cause of those messages.
- `absent` with `results/unlocked.tsv`: `not-checked`. The clone succeeded,
  but the helper could not retrieve the shipped TSV, recorded its baseline as
  unavailable, and did not run the entry point. This is missing comparison
  evidence, not a reproduction failure.
- `target` with `results/*.tsv`: `met`. Both shipped TSVs were removed in the
  clone, `sh analysis.sh` returned successfully, and both regenerated files
  matched their recorded baselines.

The target replays used the same-host local annex route recorded by the helper
from the source's local Git configuration. That route made the small input and
locked output available. This assisted transport is a limitation of the
replay context; these results do not show an independent host can retrieve
those files. `content_to_fetch_bytes` was 59 in all reports.

## Native reports

- [`target-unlocked/report.json`](target-unlocked/report.json)
- [`absent-unlocked/report.json`](absent-unlocked/report.json)
- [`target-all-tsv/report.json`](target-all-tsv/report.json)
