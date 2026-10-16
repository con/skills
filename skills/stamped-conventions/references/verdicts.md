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
   After inspecting the complete delivery, use `not-applicable` for must/005 when no large binary data exists; apply the may/001 subject boundary below.

   **Not** an N/A ground: *there was nothing of this kind to do*.
   An object with no host assumptions to document satisfies must/011 — the requirement is "write down your assumptions", and having none meets it.
   Answer `met`, and let the reason carry the emptiness ("no host assumptions beyond a POSIX shell and the tracked lockfile; nothing undocumented remains").
   The difference from an empty subject is whether the *requirement* can be satisfied vacuously (must/011: yes) or the *property* has no instance to hold of (should/009 on an all-public object: no).

   **A declared process that has never run is `partial`**, not `met` and not `not-checked`.
   must/014 and should/008 ask for a process *and* for its updates to be tracked; a documented regeneration command with no update in the history is half of that, so say "declared in <file>, no instance in the history yet".
   **The commit that introduced the file is not an instance of updating it.**
   A lockfile committed once, with a regeneration command in its header, is "declared, never run": the creation is the declaration, not an instance of the process.
   **A declared process with instances in the history is `met`**: cite one.
   A blind run stalled on exactly this gap — a re-install step the history shows was carried out seventeen times fits neither "never run" nor "unmet" — so the three cases are: instances in the history → `met`; declared, no instance → `partial`; not declared → `unmet`.
   **The bar for "declared" is a command a reader could run**: `# pinned with uv pip compile code/requirements.in` in a lockfile header clears it; "dependencies are kept up to date" does not, and that is `unmet`.
   This is the commonest borderline case, and it comes up on every young object.
6. **`restricted`** (from STAMPED-dl) is **not a status here**.
   Restricted data that is properly isolated is `met` on should/009 and `not-checked` elsewhere with "access-restricted" as the reason.
7. **Equivalent evidence counts.**
   Name the mechanism you found rather than the tool you expected.
   Preserve the checklist pin; these are explicit property-based interpretations, not edits to its wording:
   - **must/003:** an installable package declaration in a delivered environment specification counts as inclusion; physical vendoring is not required. Judge completeness under must/010, exact environment identity under must/015, and archived artifacts under should/007; missing version pins alone do not show incompleteness.
   - **must/007:** discoverable installation and usage instructions can satisfy the item under another filename or in an equivalent delivered interface; `README.md` and `Makefile` are not mandatory names.
   - **may/001:** assess independently maintained project components, not ordinary runtime or package dependencies. No such components → `not-applicable`; otherwise require independently identified, retrievable links with clear boundaries, not necessarily Git submodules. An unidentified copy or unresolvable path fails. Judge missing or incomplete dependency environments under must/003 and must/010; they do not turn packages into project modules.
   - **must/006:** execution evidence must link the actual results and actions to their environment; a recognized provenance format or tool name alone is neither necessary nor sufficient.
   - **should/002, should/006:** inspect equivalent repeated-testing and environment-reconstitution records, including manual or scheduled runs; missing CI configuration alone proves neither property absent.
   Apply these interpretations consistently within a comparison and name any equivalent evidence used.
8. **Scripted before judged.**
   Run applicable probes and cite their output, then inspect evidence outside their supported representations.
   A tracked-path inventory, recognized filename or parsed DataLad record is not a complete delivered-artifact or provenance inventory.
   Missing probe support is `not-checked` pending inspection, not evidence of absence; record which probe or reading produced each verdict.
9. **Disagreements are surfaced, not averaged.**
   When a probe and a reading of the object disagree, report both and flag the item for the human.
10. **When the object tells two stories about how it runs, that disagreement *is* the answer.**
    An object can carry three accounts of its own execution — what the documentation says, what CI exercises, and what the run records recorded — and they need not agree.
    Judge **A.1 items (must/007, must/008, must/017) on the documented route**, because that is what a reader will follow; judge **T items on the records**, because that is what produced the results.
    Where the accounts disagree, the verdict is at most `partial`, the reason names both accounts, and the disagreement is reported as a finding in its own right: a README promising a container that the `Makefile` never invokes is worse than either an honest README or an honest Makefile.
    Four pairings and where each lands: documentation against the mechanism → **must/007, must/008, must/017**, and **should/002**, because a workflow tested against instructions nobody can follow is not tested; the mechanism against the run records → **must/006 and must/008** (what produced the results is not what is offered to reproduce them); CI against the records → **should/006** (the environment being tested is not the one the results came from); and the object's *metadata* against its own layout — a `dataset_description.json` naming a pipeline the history never ran — which has no checklist item and goes in `extra_items`.
    If naming both accounts will not fit in 250 characters, name the worse one in the reason and put the other in `evidence`; do not drop it.

    **An accurate disclosure is not a disagreement.**
    This rule exists for accounts that conflict *silently* — a README promising a container the `Makefile` never invokes.
    An object whose documentation states the difference and says which route produced the results is telling one story in two parts, and the items above stay `met` on it: the test is whether a reader following the documentation would be misled, not whether two routes exist.
    Two runs in a row marked a disclosed, accurate two-route object `partial` on four items under this rule; that is this rule being over-applied, and the reason to say so here.
    **The disclosure has to be true.**
    A comment in a CI workflow claiming it exercises the recorded environment, in a job whose steps never touch it, is not a disclosure: it is the silent conflict with an extra sentence, and it is worse than silence because it tells a reader not to check.
11. **A right answer reached by the wrong route is still a finding.**
    When a probe answers an item from a property the item does not ask about, the verdict may happen to be right and the reasoning is still wrong.
    Record it in the item's `flags` (`mapping-questioned`), say which property the probe actually measured, and keep your own verdict with `source` ending in `+judgement`.
    That is how a wrong probe-to-item mapping gets fixed instead of being inherited by every later report.

## Mapping to the app

`scripts/encode_response.py` does this mapping; do not hand-roll it.
It also enforces the app's constraints: `value ∈ {"yes","no",null}`, `reason` a string of at most 250 characters, and every id known to the pinned checklist.
