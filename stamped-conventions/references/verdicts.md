# Verdict vocabulary

One status per checklist item, one reason, and evidence for anything other than `not-applicable`.
This reconciles @asmacdo's draft (pass/partial/fail/unknown), STAMPED-dl's met/partial/unmet/restricted/n-a, the [K-Dense #265](https://github.com/K-Dense-AI/scientific-agent-skills/pull/265) review ("not checked with the tooling available" is not "unmet"), and the judgement statuses of [stamped-skills-assessment](https://github.com/stamped-principles/stamped-skills-assessment).

| `status` | Use it when | App `value` | App `reason` holds |
|---|---|---|---|
| `met` | Cited evidence shows the property holds across the object | `"yes"` | Not shown by the app; the citation lives in the response JSON |
| `partial` | It holds by design but is violated somewhere specific, or holds in some components only | `"no"` | Where it falls short, concretely |
| `unmet` | Evidence shows the property is absent | `"no"` | The shortest fix |
| `not-checked` | You could not check: tool missing, cost, access, or out of the agreed scope | `null` | Why, and what would settle it |
| `not-applicable` | The property cannot apply to this kind of object | `null` | `N/A: <reason>` |

## Rules

1. **A MUST item is never satisfied by `partial`.**
   Report `partial` and count it as a MUST failure.
2. **`not-checked` is reported separately from `unmet`, always.**
   Never fold it in, never score it as zero, and never let it disappear from a denominator: say `14/17 MUST met, 2 unmet, 1 not-checked`.
3. **`met` requires a citation** a reader can open: a path (with a line number where it helps), a commit, a run record, a URL, or a command with its output.
   "The project uses DataLad" is not evidence; `.datalad/config` at commit `abc1234` is.
4. **`unmet` requires evidence of absence**, not failure to find evidence.
   If you only failed to find it, that is `not-checked`.
5. **`not-applicable` is rare and argued.**
   The object's kind decides it ([`project-kinds.md`](project-kinds.md)), and the reason names the kind.
   An object with no computation at all can be `not-applicable` on E.1; a dataset still has an environment for whatever produced it.
6. **`restricted`** (from STAMPED-dl) is **not a status here**.
   Restricted data that is properly isolated is `met` on should/009 and `not-checked` elsewhere with "access-restricted" as the reason.
7. **Equivalent evidence counts.**
   Name the mechanism you found rather than the tool you expected.
8. **Scripted before judged.**
   Where a probe exists for an item, run it and cite its output; use judgement only for what no probe can settle, and record which of the two produced each verdict.
9. **Disagreements are surfaced, not averaged.**
   When a probe and a reading of the object disagree, report both and flag the item for the human.

## Mapping to the app

`scripts/encode_response.py` does this mapping; do not hand-roll it.
It also enforces the app's constraints: `value ∈ {"yes","no",null}`, `reason` a string of at most 250 characters, and every id known to the pinned checklist.
