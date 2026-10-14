# Where this branch diverges from #24, and why

[#24](https://github.com/con/skills/pull/24) and this branch share the base
`ea48c88`. After that point #24 restructured the plan and recorded a set of
decisions; this branch instead **implemented** phase 1 and measured it. Five of
#24's decisions contradict what the implementation found, so this branch keeps
its own and says why here, with the evidence in each case.

This is not a disagreement about taste. Every item below cites something that
was run.

## What this branch adopts from #24 without argument

Taken because they are better than what was here, and credited:

- **Splitting the plan.** One 1,000-line file was unreviewable; the split into
  `PLAN.md` + `evals.md` + `prior-work.md` + `stack-repronim.md` + `talks.md`
  is #24's shape, with this branch's content.
- **Exact column definitions for R0** — `brainseg_brainsegvol`,
  `totalgray_totalgrayvol`, `cerebralwhitematter_cerebralwhitemattervol`, and
  age from `sub-*/sub-*_sessions.tsv`. Verified against the real
  `sub-138950_ses-1_desc-FreeSurfer_qc.tsv` and now in the use case *and* in
  the oracle, which previously matched columns fuzzily — a run that answered
  with `mask_maskvol` would have scored as correct. The fixture's stand-in now
  also mirrors the real per-subject directory layout.
- **A deterministic selection rule** for subjects (sort by age, take ranks
  `round(i·(n−1)/(N−1))`), so every arm and repeat sees the same sample.
- **The pilot protocol for tolerance bands**: two containers hand-run, each band
  the union of their ranges widened by 10 %, so a legitimate tool with a
  different mask definition still passes.
- **Private oracle values.** Published tolerances are a target to fit rather
  than a check. The band values stay out of the public repository; the protocol
  that produces them does not.
- **Private-first results**, with a secret and path scan before a produced
  object is promoted to a public namespace.
- **Raw pass counts, no significance claims.** With three repeats even 3/3
  against 0/3 is p ≈ 0.1 (two-sided Fisher), and `aggregate.py` now says so in
  every report it writes.
- **Per-iteration budget** as a planning number (≈10 inner-loop sessions per
  debugging round, ≈40 outer-loop sessions and 12 h wall per iteration).
- **What a PR against con/skills owes** — there is no template or contributing
  guide here, so `AGENTS.md` now says the upstream-PR rule is about PRs for
  *other* projects, and names what a PR here owes instead.

## The five disagreements

### 1. The verdict vocabulary: five statuses, not `yes`/`no`/`unknown`

**#24:** "#23's `yes`/`no`/`unknown` for v0.1; revisit with calibration data."

**Here:** `met` / `partial` / `unmet` / `not-checked` / `not-applicable`, mapped
onto the app's three values by `encode_response.py`.

**The evidence**, which is the calibration data that decision defers to:

- On `compression-comparisons-t261-study`, **8 of 17 MUST items land on
  `partial`** — "holds by design, violated somewhere specific". Collapsed into
  `no`, the report cannot tell a project with 1218 unrecorded derived files out
  of 22286 from one with no provenance at all. Collapsed into `yes`, it lies.
- `not-checked` is not `unknown` in practice: the plan's own rule is that a
  collector failure must never read as an object defect, and the three places
  it fired in these runs (modules not installed, 523 GB of input, an
  unauthenticated `gh`) each needed "what would settle it" attached. `unknown`
  carries no such obligation.
- `not-applicable` needed **two argued grounds** before a blind run stopped
  improvising: the object's kind, and an empty subject (should/009 where every
  component is public). A third case — a requirement satisfied vacuously, like
  must/011 with no host assumptions to document — turned out to be `met`, not
  N/A, and a fourth — a declared process never yet exercised — turned out to be
  `partial`. Three blind runs hit these; two guessed differently.
- Two mutants exist **only** because `partial` is expressible:
  `readme-reproduce-removed` (must/007 `partial`, because a surviving Makefile
  is still instructions) and `derived-without-record` (must/006 `partial`,
  because most derived files *do* have records).

**What would change our mind:** evidence that `partial` is being used where
`no` would serve, or that the extra states confuse readers of the web app. The
app itself is unaffected — it receives exactly `yes`/`no`/`null`.

### 2. The checklist: a vendored copy with a lock, not tag-pinned URLs only

**#24:** "No vendored copy of the checklist JSON; tag-pinned URLs only."

**Here:** `stamped-conventions/checklist/stamped-checklist-0.3.1.json` plus
`lock.json` (tag, commit, sha256, item counts), refreshed only by
`vendor_checklist.py` and verified by `--check`.

**The evidence:**

- The assessor is **read-only and must work offline**: it is run on objects
  inside containers and on hosts without egress. A tag-pinned URL makes a
  network fetch a precondition for answering anything.
- `tox -e stamped-evals` runs 15 mutants plus 38 tests **with no network**. With
  fetch-at-runtime, CI either gains a network dependency on another
  organisation's repository or the tests stop covering the item source.
- A tag is **not** immutable. The lock records the commit (`af259ba`) and the
  sha256, so a report's pin means one exact file; `--check` is what proves the
  copy was not hand-edited.
- The duplication #24 is avoiding is real but small (10 kB), and it is not a
  second *source of truth*: nothing may edit it, and the refresh is itself a
  recorded command.

Call it a verified cache if "vendored" is the objection; the mechanism is what
matters.

### 3. Probes ship with the skill, and the graders import them

**#24:** "Probes live under `evals/`, never in a skill."

**Here:** `assess-…/scripts/probes/`, imported by `evals/stamped/harness/`.

**The evidence:**

- A skill installed on its own (`apm install con/skills#<commit> --skill …`)
  must be able to answer the 13 MUST items it claims. Probes under `evals/`
  make the installed skill prose-only, and the user has nothing to run.
- One copy means **the grader and the skill cannot disagree**. That is not
  theoretical: the mutants caught three probe defects (`.json` container
  registrations unscanned, `may/001` answered from a URL verdict, `must/006`
  from a `:latest` tag) that would otherwise have been fixed in one copy and
  not the other.
- The size concern is addressed: the probes are 1,100 lines of Python that no
  session reads — the `SKILL.md` stays at 180 lines, under its own declared
  budget, enforced by `ci/validate_skills.py` E007.

**Where #24 is right:** test fixtures, mutants and harness do *not* belong in a
skill, and they are under `evals/` here.

### 4. A shared conventions skill now, not later

**#24:** "#23 lands first, on its own; a shared conventions skill comes later,
once a second consumer of the pin exists."

**Here:** `stamped-conventions` 0.2.0 exists, and the second consumer exists
with it.

**The evidence:** the pin has **three** consumers already — the assessor, the
graders in `evals/stamped/harness/`, and the encoder that writes the app URL —
and the things they must agree on are exactly what drifted in the earlier
attempts this plan studies (MD5E-vs-SHA256E in STAMPED-dl). A blind run also
found the one disagreement that a single shared file prevents: `dependencies`
existed in the skill's instructions, was missing from the format example, and
was missing from `template()`. Three authorities, one of them right.

**Where #24 is right:** if `assess-stamped` is the only skill that ever reads
the pin, the extra install is friction. That stopped being true when the
graders started reading it.

### 5. The long skill names, for now

**#24:** names follow #23 (`assess-stamped`, `align-stamped`), with the issue's
long names as trigger phrases.

**Here:** the issue's names, verbatim.

**This one is weak, and this branch will yield it.** The argument for keeping
them is only that the issue asked for them and that renaming is a `git mv` plus
a MAJOR bump plus a changelog line. The argument for #23's is better: shorter,
matches `setup-*`, and #23 is already open with those directories. **If #23
merges first, this branch renames to match rather than shipping two assessors**
— the file-level collision is the real argument, and it is #23's to win.

## Settled by #16, not by either branch

[#16](https://github.com/con/skills/pull/16) merged to master while this branch
was open, bringing the `AGENTS.md` **Skill versions** rule: a skill stays at its
initial version while its introducing pull request is open, and counting starts
at the first merge. Both skills here are therefore `0.1.0`, not the `0.2.0` they
carried through development. The eval records under
`evals/stamped/blind-runs/` keep the labels they ran with, because a run record
that is edited afterwards is not a record.

#16 also brought `code-quality-report-conventions` — a shared, non-invocable
conventions skill read by two sibling skills, merged on the same day #24 decided
that a shared conventions skill for STAMPED was premature. The pattern is now
the house style, which is most of the argument in §4 above.

## How to read the two branches together

| | #24 | this branch |
|---|---|---|
| What it is | the plan, reviewed and restructured | the plan implemented and measured |
| Skills | described | `stamped-conventions` 0.2.0, `assess-…` 0.2.0, 13 probes, 2 scripts |
| Evals | designed | 15 scripted mutants (15/15), 6 judgement mutants, 5 blind runs, 38 tests, CI |
| Objects | named | one gold reference answer, one bootstrapped results dataset, one fixture |
| Upstream | planned | a lint-clean LinkML schema and a verified drift issue, ready to file |

Nothing here needs #24 to be wrong about its own scope. The ask is that the
five decisions above be settled against what the runs showed, rather than
before.
