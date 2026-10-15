# Judgement mutants, round 4 — 2026-10-14

The round that re-ran the control, to find out whether round 3's two fixes —
the fixture's missing System requirements section, and rule 10's
over-application — actually moved the number, or only looked like they would.

| Run | Model | Result |
|---|---|---|
| `readme-host-path-in-instructions` | haiku | **detected** — must/009, must/011 and must/012 `partial`, naming `FREESURFER_HOME` and the "lab filer", and catching that the README's own "no environment variable is required" contradicts its exports |
| **`control-clean`** | sonnet | **0/19 unexplained accusations** |

## The control is clean

Every verdict it gave below `met` is on the fixture's own declared list
(`SIMULATED` in `fixtures/make_r0_object.py`): must/002, must/014, must/016,
should/006, should/007, should/008. Nothing else was accused.

| Round | Control | Denominator |
|---|---|---|
| 1 (2026-10-13) | 7 | 19 |
| 2 | 3 | 19 |
| 3 (2026-10-14) | 6 | 22 |
| **4** | **0** | **19** |

That is the [§10.1](../../../../docs/stamped/evals.md#101-done-criteria)
criterion "no collateral accusation on the clean fixture", met for the first
time — so the ratchet in `tests/test_eval_cases.py` is now the gate itself,
zero, checked against the most recent round.

Round 3's diagnosis was right: four of its six accusations came from rule 10
being read as "two routes are a disagreement" when the object discloses them
accurately, and two from the fixture genuinely documenting no system
requirements. Both were artefact fixes, and both held.

## What this round changed

The host-path run (on the smaller tier) found five more, every one of them a
sentence:

1. **`set` replaced the whole answer**, and the run lost the citation it had
   just gathered — on an item it was overriding, which is the worst place to
   lose one. Evidence now survives a `set` that does not supply its own;
   `--drop-evidence` clears it deliberately.
2. **`value` in two places.** `response-format.md` listed it as required core
   while `validate` never asks for it and `set` never writes it: it belongs to
   the payload the encoder builds, which the file now says.
3. **Relative paths.** Step 3's commands resolve only from the skill's own
   directory, and a run working from its output directory rewrote every one.
   The skill says so now.
4. **Rule 5 and the creation commit.** "Declared, never run" did not say
   whether the commit that *introduced* a lockfile counts as an instance of
   regenerating it. It does not, and must/014 and should/008 turn on exactly
   that.
5. **A disclosure has to be true.** Round 3 added "an accurate disclosure is
   not a disagreement"; this run found the other edge — a CI comment claiming
   the job exercises the recorded environment, in a job whose steps never touch
   it. That is not a disclosure, it is the silent conflict with an extra
   sentence, and worse than silence because it tells a reader not to check.

And one tool gap, from the control: the skill asked for `assessor.harness`,
`model`, `scope` and the object's kind, and nothing could write them, so four
runs in a row patched them in with a Python snippet of their own.
`encode_response.py stamp` does it now.

The probe's must/016 also learned to ask: with `--check-remote` it runs
`git ls-remote` on the object's own origin (not only on module urls, which is
all it checked before) and answers `met` or `unmet` from the result.

## Files

```
score.json                     the scorer's output, with a model per run
<run>/prompt.md                what each subagent was given, verbatim
<run>/out/                     its four output files, as it wrote them
```
