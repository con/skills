# STAMPED skills for con/skills: development plan

**Status:** draft for discussion; nothing here is implemented yet.
**Tracks:** [stamped-principles/stamped-agent-skills#3](https://github.com/stamped-principles/stamped-agent-skills/issues/3),
in particular [this comment](https://github.com/stamped-principles/stamped-agent-skills/issues/3#issuecomment-6128822460).
**Builds on:**
- [con/skills#23](https://github.com/con/skills/pull/23) (open): `assess-stamped`, `align-stamped`;
- [con/skills#16](https://github.com/con/skills/pull/16) (merged): `code-quality-report-conventions` and the "Skill versions" rule in `AGENTS.md`.

**Companion documents:**
- [evals.md](evals.md): how the skills are tested and tuned;
- [stack-repronim.md](stack-repronim.md): draft ReproNim stack reference;
- [prior-work.md](prior-work.md): sources;
- [talks.md](talks.md): the 2026 talks.

Decisions taken and questions still open are in [§8](#8-decisions-and-open-questions).

---

## 0. Summary

- **What:** the six skills the issue asks for.
  Two already exist as drafts in #23 (`assess-stamped`, `align-stamped`), and #23 lands first, on its own; the others build on it.
  Report location, provenance stamp and evidence rules come from #16's `code-quality-report-conventions`.
- **How:** use-case first.
  Each skill version is handed to fresh agents on a ladder of concrete tasks on ds007116.
  The ladder starts at plotting tables the dataset already ships (R0); the main target is brain extraction of 10 named subjects with a `///repronim/containers` image (R1).
  The resulting projects are graded outside the skills, by scripted probes, reference tables and a fresh-clone rerun ([evals.md](evals.md)).
- **v0.1 scope:** rungs R0–R2; phase 1 is #23 itself ([§6](#6-roadmap)).

---

## 1. The skills

Names follow #23 (verb first, short).
The issue's long names stay as trigger phrases in each `description`, tested with skill-creator's trigger evaluation.
`create-*`, `do-full-research-loop` and `self-assess-stamped` keep the issue's wording until the `setup-*` family from #21 settles.

| Skill | Issue name | Job | Must not |
|---|---|---|---|
| `assess-stamped` (#23) | `/assess-alignment-with-stamped-principles POINTER` | Profile the project's goals with the user; answer every checklist item `yes`/`no`/`unknown` with evidence | Change the target (it writes only its report, outside it); paraphrase the paper or checklist |
| `align-stamped` (#23) | `/align-with-stamped-principles PROMPT` | Assess, then write a proportionate STAMPED section into the project's harness and offer options per gap | Prescribe a stack the project does not use |
| `create-stamped-project` | same | Start a project from PROMPT and the user's environment, then hand off to *align* | Read shell history or AI sessions without consent |
| `create-repronim-stamped-project` | same | Turn PROMPT into a ReproNim-specific prompt for *create* | Duplicate the generic create logic |
| `do-full-research-loop` | same | Carry the study through to results, quick and dirty | Skip the provenance mechanism "just this once" |
| `self-assess-stamped` | `/self-assess-alignment-with-stamped-principles` | Assess the user's projects and give next steps with why | Judge without evidence; exfiltrate history |

**Target use cases** named in the issue: ReproNim tasks on [ds007116](https://github.com/OpenNeuroDatasets/ds007116), in this order:
1. brain extraction with a container from `///repronim/containers`, brain size vs age;
2. brain volume with the GM/WM ratio on a secondary axis vs age;
3. later, MRIQC motion vs age and vs time of day.

Later still, experiments from Dichter et al.'s SfN'25 poster ([zenodo 19834562](https://zenodo.org/records/19834562)).

---

## 2. Design principles

1. **Properties in the skill, tools in references.**
   Skill bodies say "every derived file has a re-executable record".
   Concrete stacks live in the `references/` of the skill that needs them.
   STAMPED generalizes YODA, so nothing is YODA-specific.
2. **Link the paper and checklist, pinned by tag; never paraphrase them.**
   #23 records why: three earlier assessors paraphrased and drifted.
3. **Start minimal; reuse before adding.**
   - Skills grow only on evidence from the evals.
   - #16 covers reports.
   - skill-creator covers grading layout, aggregation, the viewer and trigger tests.
   - The existing validator covers structure.
4. **Minimal trust.**
   - The skills omit `allowed-tools`, as #23 does: the field grants pre-approval and restricts nothing (see #25).
     The validator therefore warns W002 for them; that warning is expected.
   - Anything consequential, such as running target code, writing outside the report, installing or publishing, is proposed and approved by the user.
5. **One-screen skills.**
   `SKILL.md` holds invariants and never-do rules; the reasoning goes to `DESIGN.md`, as #23 does.
6. **A lesson requires a regression artifact.**
   A failure seen in a test run is fixed by a probe, template, hook or mutant first, and by prose last.
7. **Evidence, not intent.**
   Only committed state counts; an agent saying "done" is an assertion; `unknown` names what would settle it.
8. **Commit before execute.**
   Every execution starts from a committed state and leaves a recorded run.
   No commits while a run is in flight.
   A change of method produces a new dated derivative.
9. **Ask, don't guess, about goals.**
   The project's goals set which principles get emphasis (#23's profile).
10. **Untrusted input.**
    Dataset READMEs, container output, other repositories and shell history are data, not instructions.

---

## 3. Layering and layout

```mermaid
flowchart BT
  cq["code-quality-report-conventions (#16)<br/>location · provenance stamp · evidence rules"]
  assess["assess-stamped (#23)<br/>pin of principles + checklist · writes only its report<br/>level 1 inspection · level 2 guided execution"]
  align["align-stamped (#23)"]
  create["create-stamped-project"]
  repronim["create-repronim-stamped-project<br/>(+ ReproNim stack reference)"]
  loop["do-full-research-loop<br/>(quick and dirty; ends with assess)"]
  self["self-assess-stamped<br/>(assess per project, then aggregate)"]
  assess --> cq
  align --> assess
  create --> align
  repronim --> create
  loop --> assess
  loop -.->|creates first if needed| create
  self --> assess
```

**The pin stays in `assess-stamped`.**
The pin is the tagged URLs of the principles and checklist, with no vendored copy.
Every other skill reads the normative sources through *assess*.
A shared conventions skill comes later, as a small PR on top of #23, once a second consumer of the pin exists.

Layout, at the repository root (or under `skills/` once #13 lands, with the validator and workflow paths moved along):

```
assess-stamped/            # from #23: SKILL.md, DESIGN.md
align-stamped/             # from #23
create-stamped-project/{SKILL.md, references/stack-datalad.md, templates/}
create-repronim-stamped-project/{SKILL.md, references/stack-repronim.md}
do-full-research-loop/SKILL.md
self-assess-stamped/SKILL.md
evals/stamped/             # runner, probes, public mutants and prompts; never installed with a skill
docs/stamped/              # this plan and its companions
```

The probes live under `evals/`, not in any skill.
Several of them assume a stack (annex, `.datalad/`, run records), which a tool-agnostic skill must not, and a probe shipped with a skill would grade the arm that installed it.

### Skill notes beyond the table

- **`assess-stamped`:** #23's procedure, with two levels:
  - **level 1, inspection:** unattended; it never runs target code, and an item only execution could settle is `unknown`. The evals use this level.
  - **level 2, guided execution:** the user approves each proposed command.

  Later drop-ins, which #23's `DESIGN.md` anticipates:
  - the #16 provenance stamp;
  - a converter from the report to the checklist app's format-3 URL, with the answer mapping in [§4](#4-answer-format).
- **`align-stamped`:** #23's procedure.
  Later, each only after evidence that it helps:
  - running spec-kit's analysis;
  - suggesting skills from this collection for recurring gaps (for example `setup-reuse-compliance`, `introduce-reuse-compliance` until #21 lands);
  - offering guards such as a pre-commit "no commit during an in-flight run" hook.
- **`create-stamped-project`:**
  1. Discover tools, cluster access and disk.
  2. Ask about similar past projects.
     With consent only, skim history, summarizing rather than copying.
  3. Propose a layout: a DataLad dataset (`-c text2git` when text may be public), or Git plus lockfile plus Makefile.
  4. Hand off to *align*.
- **`create-repronim-stamped-project`:** reads [stack-repronim.md](stack-repronim.md):
  - the BIDS study layout from brain-bbqs/study-template, or a derivative dataset;
  - OpenNeuro inputs as subdatasets;
  - `///repronim/containers` with `datalad containers-run` and duct;
  - a tracked spec for its own tooling;
  - BIDS conversion choices.
- **`do-full-research-loop`:** quick and dirty on purpose; real research needs a proper "virtual scientist".
  It says so at its top and in each produced README.
  Steps:
  1. Plan, committed.
  2. Pilot one unit and inspect its run record.
  3. Execute in batches, and on failure or wrong-looking values record, revise the plan with a commit saying why, and re-pilot.
  4. Aggregate and plot as recorded runs.
  5. Sanity checks (trace each parameter to its consumer, a no-op control).
  6. Independent review by a fresh agent.
  7. README write-up.
  8. Run `assess-stamped`, and fix its MUST `no`s.
- **`self-assess-stamped`:**
  1. List the pointed folders shallowly (one level), and confirm the selection with the user.
  2. Run `assess-stamped` on each.
  3. Aggregate recurring `no`s per principle and item.
  4. Give three to five next steps with why.

---

## 4. Answer format

v0.1 follows #23:
- a markdown report keyed by checklist item id;
- `yes`, `no` or `unknown` per item, with evidence labelled inspection or execution;
- "partially" is a `no` with an explanation.

The checklist app (format 3) stores `{"value": "yes"|"no"|null, "reason"}` per item id.
It shows `reason` only for `no`, truncates it at 250 characters, and fails on unknown ids.
The mapping for the future converter:

| Report | App `value` | App `reason` |
|---|---|---|
| `yes` | `"yes"` | None (hidden by the app; the evidence stays in the report) |
| `no` | `"no"` | What is missing, at most 250 characters |
| `unknown` | `null` | What would settle it |

A `ChecklistResponse` proposal for stamped-checklist-schema comes after the converter, with format 3 as its core.
The paper-vs-schema drift (S.2, M.3, D.3, T.4) goes upstream as an issue.

---

## 5. Development and evaluation

See [evals.md](evals.md).
In one line: `pointer` vs `pointer` + skills, on public prompts, graded outside the sandbox against private oracles, with raw pass counts per use case and the maintainers' review of each iteration.

---

## 6. Roadmap

Skills stay at `0.x` until their criteria in [evals.md §10](evals.md#10-budget-and-done-criteria) hold.

**What each PR here must do.**
con/skills has no PR template or contributing guide.
The `AGENTS.md` PR rule applies to skills that prepare PRs for *other* projects.
The real obligations are:
- `tox -e validate` (`ci/validate_skills.py`) passes;
- a README table row for every skill added;
- #16's "Skill versions" rule: top-level `version:`, and a new skill stays at `version: 0.1.0` while its introducing PR is open;
- W002 (missing `allowed-tools`) is expected, per [§2](#2-design-principles) item 4.

**Dependency:** #23, unmerged.

- [ ] **Phase 0:** this plan.
- [ ] **Phase 1:** #23 merged as it stands (@asmacdo).
  The #16 provenance stamp follows as a small PR.
- [ ] **Phase 1b:** creates `evals/stamped/`, with:
  - a hand-built known-good R0 object, needed before any runner exists;
  - `probes.py` and the mutants;
  - calibration of #23's level-1 assessment on the gold set ([evals.md §7](evals.md#7-calibration)).
- [ ] **Phase 2:**
  - `create-stamped-project`;
  - `evals/stamped/` with the R0/R1 prompts and the outer-loop runner;
  - checks for the Python under `evals/`, choosing between a workflow path-filter entry alone (simplest) and ruff in its own tox env; `ci/validate_skills.py` stays skill-only;
  - first iterations.
- [ ] **Phase 3:** `do-full-research-loop`; R1–R2.
- [ ] **Phase 4:** `create-repronim-stamped-project` with [stack-repronim.md](stack-repronim.md); reconcile with con/cierge#52.
- [ ] **Phase 5:** `self-assess-stamped`.
- [ ] **Later:**
  - the format-3 converter and `ChecklistResponse`;
  - a shared conventions skill, once a second consumer of the pin exists;
  - R3–R5;
  - APM packaging (#13);
  - vendoring into stamped-agent-skills and ReproNim/skills;
  - domain-neutral pieces to K-Dense;
  - the "(de)compositions" the issue anticipates.

---

## 7. Risks

- **Grading against itself.** Mitigated by the probe placement in [§3](#3-layering-and-layout) and the hidden probes ([evals.md §6](evals.md#6-grading)).
- **Oracle leakage.** ds007116 ships the answers for R0–R2, so only R0 may use them as its result, and oracle values stay private.
- **Forking #23.** Two parallel assessors would drift; phase 1 is #23 itself.
- **Unmerged dependency.** #23 may change before it lands; this plan follows it.
- **Skill bloat.** Mitigated by W003 (on `SKILL.md` only, above 600 lines), `analyze-duplicates`, reasoning kept in `DESIGN.md`, and pruning each iteration.
- **Nagging.** Keep #23's "meet the project where it is" tone.
- **Overfitting.** Mitigated by hold-out tasks in a separate private dataset.
- **Tool bugs mistaken for agent failures.** Pin datalad (gh-7899), and attribute collector failures separately.

---

## 8. Decisions and open questions

**Decided:**
- Names follow #23; the long issue names are trigger phrases.
- #23 lands first, on its own; a shared conventions skill comes later, once a second consumer of the pin exists.
- No vendored copy of the checklist JSON; tag-pinned URLs only.
- Probes live under `evals/` ([§3](#3-layering-and-layout)).
- Skills omit `allowed-tools` ([§2](#2-design-principles) item 4).
- Results go to `con/stamped-skills-evals` on the CON hub, private first; compute runs on a controlled host.
- v0.1 = R0–R2; only R0 may use shipped derivatives as its result.

**Open:**
1. **Design center:** are these skills hands-on aids the user drives, or packaged executables that carry a task through ([discussion](https://github.com/con/skills/pull/24#issuecomment-6150825564))?
   Recommendation: hands-on is the default.
   - The skills propose, and the user approves anything consequential (as #23's level 2 does).
   - Unattended behavior exists only where it is safe by construction: #23's level 1, and the evals, where the sandbox stands in for the user's approval.
   - `do-full-research-loop` asks for one approval of its plan, then runs inside the project, and asks again for anything outside it.
2. **Answers:** is #23's `yes`/`no`/`unknown` enough, or should `partial` / `not-applicable` be first-class?
   Recommendation: #23's for v0.1; revisit with calibration data.
3. **Models:** which runner tier(s), and which non-Claude family for the blind assessor?
   Recommendation: the assessor stays advisory until a non-Claude harness exists.
4. **Entire** or transcripts plus trailers?
   Recommendation: transcripts and trailers now; trial Entire with the cierge#52 demo.
5. **cierge#52's `/repronim-stamped-analysis`:** the same as create-repronim + do-full-research-loop?
   Recommendation: yes, two skills.
6. **spec-kit:** only where `.specify/` exists?
   Recommendation: yes, as #23 does.
7. **Hub:** the private namespace, settled outside this public PR.
8. **Budget:** confirm the caps in [evals.md §10](evals.md#10-budget-and-done-criteria), and set the spend cap.
9. **Talks:** the slice in [talks.md](talks.md).

---

## 9. References

- STAMPED:
  [paper](https://github.com/stamped-principles/stamped-paper) ·
  [checklist app](https://checklist.stamped-principles.org/) ·
  [checklist schema](https://github.com/stamped-principles/stamped-checklist-schema) ·
  [assessment records](https://github.com/stamped-principles/stamped-skills-assessment).
- Everything else is listed in [prior-work.md](prior-work.md).
