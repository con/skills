# Blind run: `assess-alignment-with-stamped-principles` 0.1.0 on t261, 2026-10-13

The first blind run of this collection, and the one the development rule in
[`../../../AGENTS.md`](../../../AGENTS.md) came out of.

| | |
|---|---|
| Skill under test | `assess-alignment-with-stamped-principles` 0.1.0 + `stamped-conventions` 0.1.0 |
| Snapshot | con/skills at `78ae28a` (branch `claude/ecstatic-cerf-nh4j6w`), copied outside the repository |
| Scope | an object: a full clone of [compression-comparisons-t261-study](https://github.com/dandi/compression-comparisons-t261-study) at `f2f0802`, submodules not installed |
| Condition | `skill-explicit` (the task named the skill) |
| Runner | a fresh general-purpose subagent of the orchestrating session, told not to read con/skills |
| Cost | 45 tool calls, ~162 k tokens, 12 min 45 s |
| Returned | `candidate-assessment.md`, `candidate-response.json`, and five friction items |

## What it agreed and disagreed about

23 of 31 items agreed with the reference answer written by the authoring
session; 8 differed (`diff-vs-reference.json`). It also **overrode four probe
verdicts**, which is the behaviour the skill asks for and had never been
exercised.

| Difference | Classification | What happened |
|---|---|---|
| `must/009` partial, reason rewritten | **probe defect** | The probe only knew `/home` and `/tmp`, so four `/data/<user>/…` paths in tracked entry points read as clean — two of them unconditional, so the sorting sweep cannot run on another host. The run called this "the object's most consequential portability defect and the probe called it clean". |
| `must/005` → met | **probe defect** | The probe downgraded on 22 oversized blobs while its own `details` said `large_binary: []`: the item asks about large *binary* data. |
| `must/010` → unmet | **probe defect** | The probe hedged ("a spec may be inside an uninstalled module") where the object carries positive evidence of relying on host tools. |
| `should/003` → met | **wrong probe→item mapping** | `inputs-untouched` answered "are components separated into distinct modules?" from "were the inputs modified", which it could not read, hiding layout evidence behind `not-checked`. |
| `must/001`, `must/003`, `must/011`, `must/014`, `should/008` | **reference defect** | Five judgement items where the blind run read the object more carefully than the authoring session did. The reference answer was corrected. |

## The friction it reported, and what each became

1. **`--allow <glob>` was documented but did not exist** in `run_probes.py`.
   → flag implemented.
2. **must/014 and should/008 are the same sentence**, with nothing saying
   whether they may diverge. → verified against the pinned checklist, written
   into the principles card, and added to the upstream drift issue draft.
3. **`not-applicable` was tied to object kind only**, leaving "the property has
   no subject here" (should/009 on an all-public object) homeless. → `verdicts.md`
   now names both grounds.
4. **A right verdict reached through a wrong probe→item mapping had nowhere to
   go.** → `flags` (`mapping-questioned`, `probe-overridden`, `unverified-claim`)
   in the response format, a flagged-items section in the report, and rule 10 in
   `verdicts.md`.
5. **The output contract contradicted itself** between the frontmatter, step 3
   and step 6, and `<date>` was undefined; and nothing told the assessor to
   verify the finding it leads with. → one filename table in
   `response-format.md`, and a "verify the finding you are about to lead with"
   step in the skill.

Every probe defect above also became a mutant, so none of them can come back
silently: `host-mount-path-in-script`, `large-text-in-git` (a negative control —
must/005 must *not* move), `host-tool-precondition`, `outputs-under-inputs` and
`remote-removed`. Mutant detection went from 8/8 to 13/13 with no false
positives on the clean fixture.

## Reproducing it

```console
python3 evals/stamped/harness/blind_run.py prepare \
    --skill assess-alignment-with-stamped-principles \
    --object <a clone of compression-comparisons-t261-study> \
    --workdir <scratch>/blind-1
# paste the printed prompt into a fresh subagent, then:
python3 evals/stamped/harness/blind_run.py compare \
    <scratch>/blind-1/out/response.json \
    evals/stamped/gold/compression-comparisons-t261-study/response.json
```

**Where the two now stand:** after the five probe fixes and the five reference
corrections, the same `compare` puts the blind run and the reference at **30 of
31 items in agreement**. The one remaining difference is `must/009`, where the
repaired probe is now more definite (`unmet`, four blocking paths with
line numbers) than the blind run could be when the probe was blind to them
(`partial`, reason rewritten by hand). Convergence of an independent reading
with the reference is the thing the done criteria ask for; one run does not
establish it, and the next iteration uses a different object.

The candidate files here are kept **as the subagent wrote them**, including the
verdicts later superseded: a blind run is evidence about the skill at a version,
and editing it afterwards would destroy that. The reference answer it was
diffed against has since been corrected, so re-running `compare` today against
the current reference shows a different, smaller set of differences — which is
the point.
