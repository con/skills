# STAMPED in one screen

Normative text lives in the [paper](https://github.com/stamped-principles/stamped-paper) and in [stamped-principles-schema](https://github.com/stamped-principles/stamped-principles-schema).
This card exists so a session can hold the shape of STAMPED without loading either, and so no skill retypes them.
When a judgement turns on wording, open the paper rather than this card.

**A STAMPED research object is one versioned boundary that carries everything needed to re-run its own results.**

| | Principle | Codes in [principles 0.2.0](https://github.com/stamped-principles/stamped-principles-schema/blob/v0.2.0/stamped-principles.json) | The question it answers |
|---|---|---|---|
| **S** | Self-contained | S.1 (MUST) | Is everything essential reachable under one top-level root? |
| **T** | Tracked | T.1, T.3, T.5 (MUST) · T.2, T.4 (SHOULD) | Is every component content-identified, is every change recorded, and do run records name the versions involved? |
| **A** | Actionable | A.1 (MUST) · A.2 (SHOULD) | Can a reader reproduce the results from the instructions, and are the procedures executable rather than prose? |
| **M** | Modular | M.1, M.4 (SHOULD) · M.2 (MAY) | Are raw data, derivatives, code and environment separable, recombinable, and separated by access requirements? |
| **P** | Portable | P.1, P.2, P.3 (MUST) | Does it avoid undocumented host state, specify the environment explicitly, and version-control that specification? |
| **E** | Ephemeral | E.1 (SHOULD) | Are results produced in disposable environments, one per execution? |
| **D** | Distributable | D.1 (MUST) · D.2 (SHOULD) | Can others persistently retrieve every referenced component, and rebuild the environment from what is published? |

## What to say instead of restating

- The **principles** are the 17 statements above; quote at most the one code under discussion.
- The **checklist** is 31 questions derived from them (17 MUST, 9 SHOULD, 5 MAY), pinned at 0.3.1 in `../checklist/stamped-checklist-0.3.1.json` — read ids and text from there.
- The **web app** at <https://checklist.stamped-principles.org/> is where a person fills or reads a checklist.
- STAMPED **generalises YODA**: a YODA-shaped DataLad dataset is one way to satisfy it, not the definition. Nothing in these skills is YODA-specific.

## Known drift to be aware of (and not to paper over)

- The paper names **S.2**, **M.3** and **D.3** (licensing among them); principles-schema 0.2.0 does not carry them, so no checklist item covers them.
  The assessor reports licence findings as an extra item outside the checklist rather than bending an existing id ([`response-format.md`](response-format.md)).
- **T.4** ("code-driven provenance SHOULD be recorded programmatically") exists in the schema but has **no checklist item**.
  Evidence for it is reported under the T items it supports, with the gap named.
- @asmacdo's draft in [stamped-agent-skills](https://github.com/stamped-principles/stamped-agent-skills) cites "checklist v1.0.1"; that is the web app's `package.json` version.
  The checklist's own `checklist_version` is **0.3.1**.
