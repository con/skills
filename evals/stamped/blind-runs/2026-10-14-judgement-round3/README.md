# Judgement mutants, round 3 — 2026-10-14

Run because the prose changed: this round follows a day of wording edits to
`SKILL.md`, `verdicts.md` and `response-format.md`, and the
[cadence rule](../../../../docs/stamped/evals.md#2-the-blind-subagent-run--the-core-test)
says the judgement set runs whenever the prose of a skill does.

Three blind runs: the control on the unmutated fixture (sonnet), one prose
defect per tier.

| Mutant | Model | Result |
|---|---|---|
| `readme-claims-absent-container` | sonnet | **detected** — led with it: "README.md#L14 says every step … goes through the `neurodesk-freesurfer` container. Nothing tracked uses that container." |
| `readme-steps-out-of-order` | haiku | **detected** — "Reproduce out of order; make calls host python3", naming the order, the build-before-clone and the plot-before-table |
| **`control-clean`** | sonnet | **6/22 judgement items accused**, 7 more on the fixture's declared list |

**2/2 detected**, one per tier. And the control was again the most useful run of
the three.

## What it changed — the scorer, the fixture, and two rules

**The absent-container mutant was first scored as a MISS, and the mutant was
wrong, not the run.** The run set must/006 to `partial`, which the mutant's
`stay_met` forbade — but `verdicts.md` rule 10 sends a
mechanism-against-records disagreement to exactly that item. The run was being
penalised for following the skill. `stay_met` lost must/006, as round 1's
version of this mutant lost its too-narrow `flag_any`, and for the same
reason: **which item a reader pins a prose defect on is not under test.**

**The probe claimed must/016 `met` from a configured remote.** All three runs
overrode it, two of them after finding the URL returns 404. A configured
`origin` is a *claim* of publication, and the probe cannot check it offline, so
it now answers `partial` and says so; **no remote at all** is `unmet`, which is
evidence of absence rather than an unverified claim. The `remote-removed`
mutant now expects `unmet`, which is the distinction it should have been
measuring all along.

**Three runs said the fixture documents no system requirements** (must/011,
must/012 `partial`), and they were right: `apptainer` is required by every run
record and was named nowhere. The fixture now has a System requirements
section. A "known-good" object that fails a MUST is not a control.

**Rule 10 was being over-applied, and the rule says so now.** The fixture
deliberately has two routes — the records ran in a container, `make all` runs
the lockfile — and its README states the difference and says which produced the
results. Two runs read that *disclosure* as the two-accounts disagreement and
marked four items `partial`. Rule 10 is for accounts that conflict silently; an
accurate disclosure is one story in two parts, and the items stay `met`. The
test is whether a reader following the documentation would be misled.

Smaller, all from the same three runs:

- `GIT_TERMINAL_PROMPT=0 git ls-remote` — without it a missing GitHub
  repository *prompts for credentials* instead of failing, and two runs lost
  time to it before falling back to `curl`.
- A new judgement check for the defect this round's mutant injects:
  **documentation naming something nothing tracks**. That is not rule 10's two
  accounts; it is one account with no mechanism behind it, and it lands on
  must/017.
- The probe draft's `assessor` block claimed the *script* as the skill, left
  `version` null and carried the host's local date. It now names the skill,
  reads `version:` from the SKILL.md beside it, and writes a UTC date.
- `details.recorded_images` carried entries like
  `figures/brain-volume-vs-age.pngcode/containers/plotting.sif` — a missing
  space between a record's command and its extra inputs.
- The skill's "Validation scope" section had been left with an orphan
  paragraph between its lead-in and its list; both runs reported it as garbled.

## The control's remaining accusations

`must/006, must/008, must/011, must/012, must/017, should/002` — six, against
three in round 2, on a *larger* judgement denominator (22 against 19). Four of
the six are the rule-10 over-application and two are the fixture's missing
requirements list, so both causes are now addressed in the artefacts rather
than in a reviewer's memory. Round 4 re-runs the control to measure whether
that is true; until it does, **the number to quote is 6/22, not an expectation.**

## Files

```
score.json                     the scorer's output, with a model per run
<mutant>/prompt.md             what each subagent was given, verbatim
<mutant>/out/                  its four output files, as it wrote them
```
