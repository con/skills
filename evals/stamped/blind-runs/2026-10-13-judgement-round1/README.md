# Judgement mutants, round 1 — 2026-10-13

The first runs of the judgement half: prose defects, graded by blind subagents
rather than by scripts. Three were run of the seven prepared, one deliberately
on a smaller model.

| Mutant | Model | Result | What it said |
|---|---|---|---|
| `readme-wrong-make-target` | sonnet | **detected**, now **retired** | Flagged must/007 `partial`, named `brain-volumes`, and confirmed it by running `make -n brain-volumes` ("No rule to make target") rather than asserting it. Then pointed out that `entry-point` already held both the README's commands *and* the Makefile's targets and never compared them — so the defect is script-catchable, the probe now catches it, and the mutant moved to `mutants/mutate.py`. |
| `readme-platform-specific-steps` | sonnet | **detected** | must/011 `unmet`, must/012 `partial`; named `brew`, `sysctl`, `sed -i` and macOS. |
| `readme-claims-absent-container` | **haiku** | **detected** | must/017 `unmet`, naming `neurodesk-freesurfer` and `///repronim/containers`, and spotting that three sources of truth disagree (README, Makefile, run records). A smaller model caught the prose defect. |

Scored 2/2 of the mutants still in the judgement set (`score.json`); the third
is now scored by `calibrate.py` instead, where it is cheap.

## What the runs changed

Three findings in the harness and the object, one per layer:

- **The fixture was not self-consistent.** The haiku run noticed that the
  fixture's run records reference `code/containers/plotting.sif`, an image it
  never created. True, and a defect in the "known-good" object: a container
  mutant then had a second, unintended defect to find. The fixture now ships a
  placeholder at that path with a README saying why.
- **The scorer read drafts as answers.** `score` took whichever `*response.json`
  sorted first, which mid-flight is the probe draft, and called two unfinished
  runs MISSED. It now prefers the newest file and refuses anything still
  carrying five or more "No probe covers this item" placeholders, reporting it
  as *not run*.
- **A smaller model left four items unanswered.** The haiku run returned
  `may/002`–`may/005` still wearing the draft's placeholder reason. The fix is
  not a sentence telling it not to: `encode_response.py validate` now refuses a
  response that carries the placeholder, so the skill cannot report before
  answering all 31.

## And five friction items, all acted on

1. **`dependencies` existed in one authority of three.** The skill asked for
   `assessor.dependencies`; `response-format.md`'s example and
   `encode_response.py`'s `template()` both omitted it. Now all three agree.
2. **The entry-point probe never cross-checked its two lists** — see the
   retirement above. The cheap, deterministic check it was missing is in.
3. **`not-applicable` had no room for vacuous truth.** "Have host assumptions
   been documented?" on an object with no assumptions to document is `met`
   (the requirement is satisfied by having none), not N/A — distinct from an
   empty subject, where the property has no instance at all. `verdicts.md` now
   says which is which.
4. **Step 3 and invariant 3 pulled in opposite directions on should/004.** The
   step read as "run the expensive probe or answer `not-checked`", while the
   conventions say equivalent committed evidence counts — a CI job checking the
   object out into a fresh runner *is* that evidence. The step now says so.
5. **No flag for the checklist's own duplicate.** must/014 and should/008 are
   the same sentence; saying so in free text left a reader unable to tell a
   duplicate from an ordinary second finding. `upstream-duplicate` joins the
   `flags` vocabulary.

## Still to run

`control-clean` (the unmutated object, whose only score is how many judgement
items it accuses — the false-accusation baseline for the judgement half, which
has never been measured), plus `readme-misdescribes-target` (the judgement
replacement for the retired mutant), `readme-wrong-tool`,
`readme-steps-out-of-order`, `readme-host-path-in-instructions` and
`dataset-description-contradicts-layout`.
