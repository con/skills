# Fresh replay check

Snapshot skill commit: `89374d7727efd2bccc48cfa917d7751ff95f497e`.
The snapshot checklist pin check passed: checklist 0.3.1 (31 items) matches
`lock.json`. This is a bounded replay check, not a full STAMPED assessment.

## Exact commands

```sh
mkdir -p /tmp/stamped-replay-route-review/small
pixi run --manifest-path /Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml python /tmp/stamped-replay-route-review/snapshot/skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py --path /tmp/stamped-replay-route-review/native/target --entry 'sh analysis.sh' --outputs 'results/*.tsv' -o /tmp/stamped-replay-route-review/small/target-fresh-rerun.json
pixi run --manifest-path /Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml python /tmp/stamped-replay-route-review/snapshot/skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py --path /tmp/stamped-replay-route-review/native/absent --entry 'sh analysis.sh' --outputs 'results/*.tsv' -o /tmp/stamped-replay-route-review/small/absent-fresh-rerun.json
```

## Results and interpretation

For `native/target`, the helper returned `met`. It made a fresh DataLad clone,
retrieved 59 bytes of content through a local storage route found in the source
Git configuration, removed the two shipped TSV outputs, and ran `sh
analysis.sh` successfully on the same host. Both `results/locked.tsv` and
`results/unlocked.tsv` were byte-identical to their shipped baselines. The
native helper report is [target-fresh-rerun.json](target-fresh-rerun.json).

This establishes computational repeatability for these two outputs through
that local route on this host. It does not establish publication access or
portability to another host, and it does not establish scientific validity.
The helper report records `host_scope: same-host`, source transport
`local-source-git-config`, and a local `storage` URL. No container runtime was
available or used.

For `native/absent`, the helper returned `not-checked`, not a reproduction
failure. The clone succeeded, but its configured content route could not
provide the input or output contents. The helper could not fetch
`results/locked.tsv`, which had no available baseline, so it stopped before
running the entry point. Its report shows no local source transports and one
unavailable comparator. The native helper report is
[absent-fresh-rerun.json](absent-fresh-rerun.json). This establishes that the
replay could not be checked with the available local storage route; it does
not establish that the analysis command fails or that its outputs differ.

## Wording and tool friction

The skill says, “The execution probe is separate because it runs the
workflow,” and presents the invocation with `--url <published url>`. That
wording alone leaves unclear how to do an explicitly local, route-focused
check. The helper's `--path` option resolves this: its help calls this
“indicative only” and says it “does not test D.1.” The user-specified local
targets therefore support a same-host replay check, not a publication test.

The skill also says, “Record whether the clone ran on the same host or another
host.” The helper records `same-host` automatically here, but this check does
not compare hosts. Its phrase “fresh clone” could be read as stronger evidence
of portability than the actual same-host/local-route result; the report's host
and transport fields are needed to qualify that result.
