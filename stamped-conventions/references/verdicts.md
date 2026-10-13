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
5. **`not-applicable` is rare and argued**, and there are exactly two grounds for it:
   - **the kind of object** ([`project-kinds.md`](project-kinds.md)) — an object with no computation at all can be `not-applicable` on E.1; a dataset still has an environment for whatever produced it;
   - **an empty subject** — the thing the item asks about does not exist here.
     should/009 ("are restricted data or software kept in their own modules?") on an object whose every component is public has no subject: `met` would be a citation-free claim about a component that does not exist, and `unmet` would be false.

   Either way the reason names the ground, starting with `N/A:`.
   An item you merely could not check is `not-checked`, never this.

   **Not** an N/A ground: *there was nothing of this kind to do*.
   An object with no host assumptions to document satisfies must/011 — the requirement is "write down your assumptions", and having none meets it.
   Answer `met`, and let the reason carry the emptiness ("no host assumptions beyond a POSIX shell and the tracked lockfile; nothing undocumented remains").
   The difference from an empty subject is whether the *requirement* can be satisfied vacuously (must/011: yes) or the *property* has no instance to hold of (should/009 on an all-public object: no).
6. **`restricted`** (from STAMPED-dl) is **not a status here**.
   Restricted data that is properly isolated is `met` on should/009 and `not-checked` elsewhere with "access-restricted" as the reason.
7. **Equivalent evidence counts.**
   Name the mechanism you found rather than the tool you expected.
8. **Scripted before judged.**
   Where a probe exists for an item, run it and cite its output; use judgement only for what no probe can settle, and record which of the two produced each verdict.
9. **Disagreements are surfaced, not averaged.**
   When a probe and a reading of the object disagree, report both and flag the item for the human.
10. **A right answer reached by the wrong route is still a finding.**
    When a probe answers an item from a property the item does not ask about, the verdict may happen to be right and the reasoning is still wrong.
    Record it in the item's `flags` (`mapping-questioned`), say which property the probe actually measured, and keep your own verdict with `source` ending in `+judgement`.
    That is how a wrong probe-to-item mapping gets fixed instead of being inherited by every later report.

## Mapping to the app

`scripts/encode_response.py` does this mapping; do not hand-roll it.
It also enforces the app's constraints: `value ∈ {"yes","no",null}`, `reason` a string of at most 250 characters, and every id known to the pinned checklist.
