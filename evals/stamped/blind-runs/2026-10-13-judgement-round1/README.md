# Judgement mutants, round 1 — 2026-10-13

The first runs of the judgement half: prose defects, graded by blind subagents
rather than by scripts. Five runs of the seven prepared, one deliberately on a
smaller model, plus the control.

| Mutant | Model | Result | What it said |
|---|---|---|---|
| `readme-wrong-make-target` | sonnet | **detected**, now **retired** | Flagged must/007 `partial`, named `brain-volumes`, and confirmed it by running `make -n brain-volumes` ("No rule to make target") rather than asserting it. Then pointed out that `entry-point` already held both the README's commands *and* the Makefile's targets and never compared them — so the defect is script-catchable, the probe now catches it, and the mutant moved to `mutants/mutate.py`. |
| `readme-platform-specific-steps` | sonnet | **detected**, now **retired** | must/011 `unmet`, must/012 `partial`; named `brew`, `sysctl`, `sed -i` and macOS, and noted that **13 of 13 probes said `met`** on an object that runs on one developer's Mac. That verdict is now mechanical: `platform-assumptions` flags platform-specific commands when no platform is named in the same file, and the mutant moved to the scripted set. |
| `readme-claims-absent-container` | **haiku** | **detected** | must/017 `unmet`, naming `neurodesk-freesurfer` and `///repronim/containers`, and spotting that three sources of truth disagree (README, Makefile, run records). A smaller model caught the prose defect. |

| `readme-misdescribes-target` | sonnet | **detected** (after the net was widened) | It read the prose, caught the falsehood and named it — "claims (falsely) that `make all` alone installs the environment" — then pinned it on should/002 and must/017 rather than on must/007. The mutant's `flag_any` was too narrow, which is a defect in the fixture, not the run: which item a reader chooses for a prose defect is not under test, and `mention_any` is what carries the weight. |
| **`control-clean`** (no defect) | sonnet | **2/18 false accusations** | The baseline that had never been measured — and the most useful run of the five. See below. |

Scored 2/2 at the time (`score.json`); **both of those mutants have since been
retired into the scripted set**, where the same defects now cost nothing to
check. That is the loop working in the direction it should: a judgement mutant
that turns out to be mechanizable becomes a probe, and the judgement set keeps
only what genuinely needs a reader. Scripted mutants went 13 → 15; the
judgement set is 6.

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

## And sixteen friction items, fifteen acted on

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
6. **Platform lock-in through tool choice was invisible to every probe** — the
   run said so after watching 13/13 come back `met` on a macOS-only object. Now
   a probe (`platform-assumptions`), and the mutant is scripted.
7. **Nothing said what to do when the object tells two stories about how it
   runs** — documentation, CI and run records can each describe a different
   execution. `verdicts.md` rule 10 now settles it: judge A.1 items on the
   documented route, T items on the records, cap the verdict at `partial` where
   they disagree, and report the disagreement as a finding of its own.
8. **The skill never said what to do when no user is available** to confirm
   goals and kind — only the conventions gestured at it. Step 2 now says:
   label the assumption, say it was unconfirmed, carry on.
9. **A 9 kB base64 URL has nowhere to go.** The filename table gains
   `<date>-url.txt`, and the report links it instead of inlining it.
10. **`project-kinds.md` had no example of the commonest shape** — a study whose
    product is a re-derivation from another dataset's derivatives. It has one
    now, with what that implies for S.1, M.1, T and E.1.
11. **`ci-present` answered two different items from one coarse regex** — the
    bare word `make` in a CI file was taken as proof both that the workflow is
    tested *and* that the environment behind the results is rebuilt. Split:
    should/002 asks whether CI re-executes the workflow; should/006 asks whether
    it reconstitutes **the** environment the run records name, which CI running
    its own `pip install` does not.
12. **The skill's probe-coverage sentence was wrong** (it said 2 SHOULD items;
    the probes answer 3) — reported independently by two runs. Fixed, and now
    pinned by a test that compares the sentence against the registry, so the
    doc cannot drift again.
13. **"Verify the finding you are about to lead with" had one worked example**,
    and not the one that mattered: a live URL pinned to a commit that does not
    exist upstream. Both that and `git ls-remote` on a publication claim are
    named now.
14. **`not-applicable` still had a borderline case**: a declared process that
    has never run (must/014 on a young object). It is `partial` — "declared in
    <file>, no instance in the history yet" — not `met` and not `not-checked`.
15. **should/008 was not its own row** in the judgement table, which cost one
    run a `validate` failure cycle. It has one.
16. **Nothing said what to do when `gh` is unauthenticated** in step 5. Say so
    in the scope line and move on; the step informs wording, it never blocks.

## The control run, which found that the fixture was not known-good

Given the unmutated object, it accused six judgement items. Four are the
fixture's own simulated properties, now declared in the object's `FIXTURE.md`
and listed in `judgement_calibrate.py`'s `CONTROL_EXPECTED`:

- **must/002 `unmet`** — it fetched the pinned input commit
  (`2c445a41…`) from the real `OpenNeuroDatasets/ds007116` and got
  `upload-pack: not our ref`. **Correct**: the fixture generates the input
  locally and then records the real URL, so the pin cannot resolve for anyone.
  `--check-remote` now verifies the recorded commit and not only the URL shape.
- **must/016 `partial`** — it queried `github.com/con/stamped-eval-fixture-r0`
  and got 404. **Correct**: the fixture's own remote is invented.
- **should/004, should/007** — downstream of the same two simulations.

Two were fair criticisms of the fixture itself, so the fixture changed rather
than the expectations: **may/002** and **may/005** (the modular structure was
nowhere documented, and `docs/README.md` was a one-line stub). The README now
carries a layout table and a sentence on what can be swapped independently, and
`docs/README.md` explains how the parts relate. Those two accusations were
measured against the fixture *as it then was*; the next control run is what
will show the baseline on the improved object.

One of its five friction items was simply **wrong**: it reported `lock.json`'s
sha256 as 65 hex characters. It is 64, and `vendor_checklist.py --check`
recomputes and compares, so the claim could not have been true. Worth recording:
a blind run's friction list is evidence, not verdicts, and this one does not
survive checking.

## Still to run

A fresh `control-clean` on the improved fixture, plus `readme-wrong-tool`,
`readme-steps-out-of-order`, `readme-host-path-in-instructions` and
`dataset-description-contradicts-layout`.
