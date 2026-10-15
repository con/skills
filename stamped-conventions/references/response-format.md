# Response, report and stamp

Every STAMPED assessment produces four files (five with the optional fresh-rerun report), named for **the day the assessment was made** (UTC, `YYYY-MM-DD`) — not the object's commit date, and not the date of an earlier assessment being redone:

| File | What it is |
|---|---|
| `<date>-assessment.md` | the human report (layout below) |
| `<date>-response.json` | the machine-readable per-item answer, with evidence and pins |
| `<date>-probes.json` | what the scripted probes said, unedited, including the ones overridden |
| `<date>-url.txt` | the checklist-app URL, on one line |
| `<date>-fresh-rerun.json` | only when the expensive rerun probe was actually run |

The URL is derived from the response, never maintained by hand.
Two assessments of the same object on the same day get a `-2` suffix on all four; the second one's report says what changed and why.
Where the files are written is the calling skill's business; their names and shapes are this file's.

## Response JSON

A superset of the web app's persistence format 3.
The app ignores keys it does not know, so one file serves both.

```json
{
  "checklist_version": "0.3.1",
  "responses": {
    "stamped-checklist:must/009": {
      "value": "no",
      "reason": "code/plot.py line 12 opens an absolute path under a user home directory.",
      "status": "unmet",
      "evidence": [
        {"uri": "code/plot.py#L12", "description": "open(<absolute path under $HOME>)", "sha256": null}
      ],
      "source": "probe:no-abs-paths",
      "flags": []
    }
  },
  "schema_version": "0.2.0",
  "principles_version": "0.2.0",
  "checklist_source": {
    "repo": "https://github.com/stamped-principles/stamped-checklist-schema",
    "tag": "v0.3.1",
    "commit": "af259bad237fa57b856417db8dba45a1b283a527"
  },
  "extra_items": [
    {"key": "licence-declared", "status": "unmet", "reason": "No LICENSE, LICENSES/ or REUSE.toml; paper S.2/D.3 have no checklist item.", "evidence": []}
  ],
  "object": {"url": "…", "commit": "…", "captured_at": "2026-10-13T12:00:00Z", "kind": "study"},
  "assessor": {"skill": "assess-alignment-with-stamped-principles", "version": "0.2.0", "harness": "claude-code 2.1.x", "model": "…", "date": "2026-10-13",
               "dependencies": ["stamped-conventions@0.2.0"]},
  "scope": "Assessed the repository at the commit above; container images were not pulled."
}
```

- **Required core** (what the app reads): `checklist_version`, and `responses` with a `value` and a string `reason` per id — *in the payload the encoder builds*. The response JSON you write carries `status`, and `encode` derives `value` from it; `validate` therefore does not ask for a `value` and `set` does not write one. A `value` you write by hand that disagrees with its `status` is an error `validate` reports.
- Every one of the 31 pinned ids appears exactly once.
  A missing id is not "no answer"; it is a bug the validator catches.
- `status` is the richer verdict from [`verdicts.md`](verdicts.md); `value` is derived from it, never set by hand.
- `evidence[]` uses stamped-skills-assessment's `Evidence` shape: `{uri, description, sha256?}`.
  `uri` is relative to the object's root, or absolute for anything outside it.
  **The argument lives here, not in `reason`.** 250 characters does not hold two cited accounts plus "the probe's heuristic said X but Y is true", and an override needs all three. Make `reason` the one-line verdict a reader sees in the app, and put each account, each command you ran and each number in an `evidence[]` entry with its own `description`.
- `source` is `probe:<name>`, `judgement`, or `probe:<name>+judgement` when a reading of the object overrode a probe (and then the item is flagged).
  Several probes may be named — `probe:entry-point+probe:ci-present+judgement` — which is what a verdict reached by **comparing two probes' evidence** looks like, and that comparison is itself the finding often enough to be worth recording.
- `flags[]` is optional and holds what a reader has to know about *how* the answer was reached, not what it says:
  - `mapping-questioned` — the probe answered this item from a property the item does not ask about ([`verdicts.md`](verdicts.md) rule 10);
  - `probe-overridden` — a reading of the object changed the probe's verdict;
  - `unverified-claim` — the verdict rests on something not confirmed independently, and the report says so;
  - `upstream-duplicate` — the checklist asks this question twice (must/014 and should/008 are the same sentence), so this answer repeats another by design rather than by mistake.

  Flagged items get their own short list in the report, after the per-item table.
- `extra_items[]` carries findings with no checklist id (licences, T.4) so they are reported without bending an existing id.

## The provenance stamp

`assessor` plus `object` plus `checklist_source` **is** the stamp, and every report repeats it in prose at its foot:

> Produced by `assess-alignment-with-stamped-principles` 0.1.0 with `stamped-conventions` 0.1.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259ba`), on <object url> at commit `<sha>`, 2026-10-13, <harness>/<model>.
> Probe output: `<path to the probe JSON>`.

A report without the stamp cannot be compared against another iteration, so it is not finished.

## Report layout

One page, in this order, so the reader meets the actionable part first:

1. **Verdict line** — `MUST: n met / n partial / n unmet / n not-checked`, then SHOULD and MAY, each with its denominator.
   No single overall score, ever.
2. **What to fix first** — at most five, highest leverage first, each as *what to change* → *why it matters to this project* → *the item ids it closes*.
3. **What the project already does well** — two or three, with citations.
4. **Per-item table** — MUST first, then SHOULD, then MAY: id, principle codes, status, evidence, reason.
   `scripts/encode_response.py table <response>.json` renders exactly this from the response; it is not a table to type by hand.
5. **Flagged items** — every item carrying a `flags` entry, with one line each: what the probe measured versus what the item asks, or what the override was.
   An empty list is worth stating as "none".
6. **Not checked** — each with what would settle it.
7. **Goals and kind** — the project's stated goals (and where they came from: documentation, or the user's answers), its kind, and the emphasis that follows.
8. **The checklist URL**, the stamp, and a pointer to the response JSON.
   The URL is ~8–10 kB of base64 for a full 31-item response, so the report **links** `<date>-url.txt` rather than inlining it; a link a reader can click, not a wall they have to scroll.

## The checklist-app URL

Facts, from [stamped-checklist](https://github.com/stamped-principles/stamped-checklist) at `d24d7ca`:

- `PERSISTENCE_FORMAT = 3` (`src/persistence.js`).
- The `responses` parameter is **standard base64** (not URL-safe) of UTF-8 JSON `{"checklist_version", "responses"}`, then percent-encoded as a query parameter.
- The app builds `?checklist=<v>&responses_version=<v>&cols=auto&sections=off&format=3&responses=<b64>` (`src/script.js`, `syncPersistentURL`).
- It accepts `value ∈ {"yes","no",null}`, requires `reason` to be a **string** (empty is fine), truncates it to 250 characters, shows it only for `"no"`, drops keys it does not know, and **rejects the whole load** on an id that is not in the requested checklist version.

`scripts/encode_response.py` is the only writer of that URL, and `decode` is the reverse — that is how a checklist a person filled in the web app becomes reference answers for calibration, with no extra labelling tool.

## When the full assessment record matters

For eval runs and reviewed assessments, the same run also writes [stamped-skills-assessment](https://github.com/stamped-principles/stamped-skills-assessment) records (`use_case`, `object`, `rubric`, `assessment`, `review`) from this same JSON, so the two can never diverge.
