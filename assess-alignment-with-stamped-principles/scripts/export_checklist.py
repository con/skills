#!/usr/bin/env python3
"""Export reviewed per-item judgments to STAMPED checklist UI format 3."""
import argparse
import base64
import json
from pathlib import Path
from urllib.parse import urlencode

VALUES = {"demonstrated": "yes", "not_demonstrated": "no", "partial": None, "unknown": None, "not_applicable": None}

def export(checklist, answers):
    version = checklist["checklist_version"]
    if answers.get("checklist_version") != version:
        raise ValueError("Checklist and answer versions differ")
    ids = [item["id"] for group in checklist["data"] for entry in group["entries"] for item in entry["items"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Checklist contains duplicate stable IDs")
    items = answers.get("items")
    if not isinstance(items, dict) or set(items) != set(ids):
        raise ValueError("Answers must contain every checklist ID exactly once and no extra IDs")
    responses = {}
    for item_id in ids:
        item = items[item_id]
        status = item.get("status")
        reason = item.get("reason")
        if status not in VALUES or not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"Invalid judgment or missing reason: {item_id}")
        if VALUES[status] is None:
            reason = f"{status}: {reason}"
        # The JS UI counts UTF-16 code units, not Python Unicode code points.
        if len(reason.encode("utf-16-le")) // 2 > 250:
            raise ValueError(f"Reason exceeds UI limit; retain full evidence separately: {item_id}")
        responses[item_id] = {"value": VALUES[status], "reason": reason}
    return {"format": 3, "checklist_version": version, "responses": responses}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checklist", required=True, type=Path)
    parser.add_argument("--answers", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--url-output", type=Path)
    args = parser.parse_args()
    try:
        payload = export(json.loads(args.checklist.read_text()), json.loads(args.answers.read_text()))
    except (ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    if args.url_output:
        body = {"checklist_version": payload["checklist_version"], "responses": payload["responses"]}
        encoded = base64.b64encode(json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()).decode()
        params = {"checklist": payload["checklist_version"], "responses_version": payload["checklist_version"], "format": "3", "responses": encoded}
        args.url_output.write_text("https://checklist.stamped-principles.org/?" + urlencode(params) + "\n")

if __name__ == "__main__":
    main()
