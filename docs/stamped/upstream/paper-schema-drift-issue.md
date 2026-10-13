# Ready-to-file issue: the paper, the principles schema and the checklist disagree

**Where to file:** <https://github.com/stamped-principles/stamped-principles-schema>
for §1 and §2 below (the schema is what tooling reads), with a cross-link from
<https://github.com/stamped-principles/stamped-checklist-schema> for §3.
Suggested title: *Principles schema 0.2.0 drifts from the paper: three
principles missing, one split, one with no checklist item — plus two identical
checklist items*. Section 3 belongs in
<https://github.com/stamped-principles/stamped-checklist-schema> if the
maintainers prefer one issue per repository.

Checked 2026-10-13 against `stamped-paper@main` `main.tex`,
`stamped-principles-schema@v0.2.0` and `stamped-checklist-schema@v0.3.1`.
Tooling that reads the schema — the checklist app, assessment records, the
STAMPED skills in [con/skills](https://github.com/con/skills) — cannot see
anything the schema does not carry, so each gap below is silently invisible to
every automated assessment.

## 1. Three principles in the paper are absent from the schema

All three are about licensing, which is why none of the 31 checklist items asks
about a licence:

| Paper (`main.tex`) | Level | In principles 0.2.0? |
|---|---|---|
| **S.2** "License declarations for all components are themselves part of the research object and MUST be retrievable alongside the content they govern." (line 132) | MUST | no |
| **M.3** "Each module's license SHOULD be declared independently and checked for compatibility at the boundaries where modules are combined." (line 216) | SHOULD | no |
| **D.3** "Each module SHOULD carry an explicit license with a resolvable identifier." (line 289) | SHOULD | no |

The paper lists 19 principles; the schema carries 17.

Consequence we hit immediately: an object with no `LICENSE`, no `LICENSES/` and
no `REUSE.toml` can answer every one of the 31 checklist items without the
absence ever being reported. Our assessor reports it as an out-of-checklist
finding rather than bending an unrelated id — which works, but means the
headline numbers understate a MUST-level gap the paper does state.

## 2. The paper's T.4 is split in the schema, and the halves read differently

- Paper **T.4**: "Code-driven provenance SHOULD be recorded programmatically
  **and MUST include the versions of all components involved**." (line 156)
- Schema **T.4** (SHOULD): "Code-driven provenance SHOULD be recorded
  programmatically."
- Schema **T.5** (MUST): "Provenance records MUST include the versions of all
  components involved."

The split is sensible — one compound statement with two requirement levels is
hard to check — but the paper has no T.5, so a report citing "T.5" cannot be
traced back to the paper, and a reader comparing the two documents finds a
principle code that exists in only one of them. Either the paper adopts the
split or the schema records that T.5 derives from the paper's T.4.

A smaller wording difference in the same vein: paper A.2 says procedures
"SHOULD be **expressed** as executable specifications", the schema says
"**specified** as executable specifications".

## 3. Two checklist items are the same sentence

`stamped-checklist:must/014` (P.3) and `stamped-checklist:should/008` (D.2) carry
**identical text**, word for word:

> Is there a process for updating environment specifications when dependencies
> change, and are these updates tracked in version control?

(verified by comparing the two `text` fields in `stamped-checklist.json@v0.3.1`.)

One is a MUST, the other a SHOULD, and nothing in the checklist says whether the
two may be answered differently or why the same requirement appears at two
levels. Downstream this is not cosmetic: an assessor has to either answer both
identically — making a reader think two different things were checked — or
invent a distinction the checklist does not state. A blind run of our assessor
flagged it unprompted as the thing it could not resolve from the documents.

Either the SHOULD is the P.3 MUST seen from D.2 and should say so, or one of
them is meant to ask something else and has the wrong text.

## 4. Schema T.4 has no checklist item

Across the 31 items of checklist 0.3.1, the `principle_codes` used are
S.1, T.1, T.2, T.3, T.5, A.1, A.2, M.1, M.2, M.4, P.1, P.2, P.3, E.1, D.1, D.2.
**T.4 appears nowhere**, so "is provenance recorded programmatically rather
than by hand?" — arguably the principle an AI-assisted project most needs to be
asked — is never asked. It is also one of the easiest to check mechanically: a
run record exists for each derived file, or it does not.

## What would help

1. Add S.2, M.3 and D.3 to the principles schema (and, in turn, one or two
   checklist items about licences).
2. Record the T.4/T.5 relationship in whichever direction the authors prefer.
3. Resolve the must/014 == should/008 duplication: distinguish them, or say
   that one restates the other at a different level.
4. Add a checklist item for T.4.

Happy to open the PRs for any of these; we are consuming the schemas
downstream and are pinned at `checklist-v0.3.1` / `principles-v0.2.0`, so the
pins make the drift visible rather than painful.
