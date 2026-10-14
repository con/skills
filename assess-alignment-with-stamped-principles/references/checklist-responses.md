# Checklist format 3 export

The web UI implementation inspected at [`d24d7ca0515efa6ed639ef2844c351c8e5471154`](https://github.com/stamped-principles/stamped-checklist/blob/d24d7ca0515efa6ed639ef2844c351c8e5471154/src/persistence.js) uses stable checklist item IDs with `value: "yes" | "no" | null` and a string `reason` capped at 250 characters.
This is an implementation-derived format, not a published response schema.
The upstream checklist schema describes the questions, not these answers.

Prepare a detailed per-item answer file:

```json
{
  "checklist_version": "0.3.1",
  "items": {
    "stamped-checklist:must/001": {
      "status": "demonstrated",
      "reason": "Boundary verified; see assessment criterion S-root and evidence E1."
    }
  }
}
```

Include every ID from the chosen checklist.
Mark unassessed items unknown; the helper refuses omissions, extra IDs, mismatched versions, or overlong reasons.
Use `demonstrated` only with sufficient evidence, `not_demonstrated` for an observed unmet target, and `partial`, `unknown`, or `not_applicable` for their distinct rich meanings.
The last three export as null; their status is retained in the original detailed answer file and prefixed to the short reason.
A null must not become an automatic negative result.

The helper requires Python 3.9+ and only its standard library.
From any directory, substitute actual paths:

```sh
python /path/to/skill/scripts/export_checklist.py \
  --checklist /path/to/pinned-stamped-checklist.json \
  --answers /path/to/detailed-answers.json \
  --output /path/to/checklist-responses.json \
  --url-output /path/to/checklist-url.txt
```

The JSON file is the UI local-storage representation.
The optional URL uses `checklist`, `responses_version`, `format=3`, and a UTF-8/Base64 encoding of `{checklist_version,responses}`.
Producing the URL does not open or publish it.
Keep sensitive information out of URL reasons.
Preserve full evidence and judgments in the separate assessment, including any source-version mismatch.
