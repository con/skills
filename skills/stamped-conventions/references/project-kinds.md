# Project kinds and emphasis

Settle the kind **before** judging the object, from its documentation and the user's answers, not from a guess.
Ask when it is not plain; a wrong kind moves the emphasis and produces a confidently wrong report.
The kind is recorded in the response JSON (`object.kind`) and, for eval runs, as the `rubric`.

| Kind | What it is | Emphasis | Typically `not-applicable` |
|---|---|---|---|
| **dataset** | Data as the product: raw, derivative, or both | **M**odularity (raw vs derived vs code), **P**ortability of whatever produced it, **D**istributability (retrievable by others, licence stated) | E.1 only if the data was not computed at all (acquired raw data) |
| **component / tool** | Code others call: a library, a container recipe, a workflow | **E**phemerality (each execution in a disposable environment), **P**ortability, **A**ctionability (tests and an entry point) | Nothing by default; a tool with no results of its own answers must/006 about its own test runs |
| **study** | A question answered with data and compute: the usual shape of these skills' output | All seven; **T** (results linked to actions and environments) and **S** (essential inputs included or retrievably linked within the declared boundary) carry the most weight | Rarely anything |
| **skill / agent harness** | A skill, prompt collection or agent configuration — including the skills in this collection | **T** (`version:`, changelog), **A** (tests outside the skill directory), **P** (no host assumptions), **D** (installable at a pin) | may/001 where there are no external modules |

## A shape that comes up constantly

**A study whose product is a re-derivation from another dataset's derivatives** — it consumes published results, adds a join, a table and a figure, and produces no raw or intermediate data of its own.
It is a **study**, not a dataset: the product is an answer, and the inputs belong to someone else.
What follows: S.1 and M.1 are judged on identifiable inputs and component boundaries, using the equivalent-evidence interpretations in [`verdicts.md`](verdicts.md); T is judged on the few derived files it does make, and "few" is not a discount; E.1 is weighed lightly if the computation is seconds of CPU, and never counted against the object for being cheap.

## Mixed objects

Most real projects are more than one kind.
Name the **primary** kind, list the secondary ones, and judge each item against the component it applies to — a study that ships a reusable converter is judged on E.1 for the converter and on T for the results.
Say in the report which component each verdict was read from.

## What the emphasis changes, and what it does not

- It changes **what to fix first** (report order), and the "why it matters" sentence attached to each fix.
- It changes which items are honestly `not-applicable`.
- It does **not** change a MUST into a SHOULD, and it never lowers the evidence bar.
