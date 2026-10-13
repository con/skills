#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""STAMPED checklist responses: read the items, validate, encode, decode.

The vendored checklist in ``../checklist/`` is the only item source, and this
script is the only writer of a checklist-app URL.  See
``../references/response-format.md`` for the response JSON and
``../references/verdicts.md`` for the statuses.

Subcommands
-----------
items      list the pinned items (id, level, principle codes, text)
validate   check a response JSON against the pin and the app's constraints
encode     response JSON -> checklist-app URL
decode     checklist-app URL -> response JSON (how a filled web form becomes
           reference answers for calibration)
template   emit a response JSON skeleton with every item not-checked

Exit codes: 0 ok, 1 validation failed, 2 usage.
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
CHECKLIST_DIR = HERE.parent / "checklist"
APP_URL = "https://checklist.stamped-principles.org/"
PERSISTENCE_FORMAT = 3
REASON_MAX = 250
# What `run_probes.py --response` writes for an item no probe covers. A finished
# response never still carries it: that is an unanswered item wearing the
# costume of an answer.
DRAFT_PLACEHOLDER = "No probe covers this item"

# status -> app value; see ../references/verdicts.md
STATUS_VALUE = {
    "met": "yes",
    "partial": "no",
    "unmet": "no",
    "not-checked": None,
    "not-applicable": None,
}
# A MUST item is never satisfied by `partial`.
MUST_SATISFYING = {"met"}


class Checklist:
    """The pinned items, read from the vendored JSON."""

    def __init__(self, path: pathlib.Path | None = None) -> None:
        self.lock = json.loads((CHECKLIST_DIR / "lock.json").read_text())
        self.path = path or CHECKLIST_DIR / self.lock["file"]
        data = json.loads(self.path.read_text())
        self.version = data["checklist_version"]
        self.schema_version = data.get("schema_version")
        self.principles_version = data.get("principles_version")
        self.items: list[dict] = []
        for level in data["data"]:
            for entry in level["entries"]:
                for item in entry["items"]:
                    self.items.append(
                        {
                            "id": item["id"],
                            "level": level["level"],
                            "principle_codes": list(entry["principle_codes"]),
                            "text": item["text"],
                        }
                    )
        self.by_id = {i["id"]: i for i in self.items}

    def level(self, item_id: str) -> str:
        return self.by_id[item_id]["level"]


def _b64(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")  # standard alphabet, as btoa() produces


def validate(response: dict, cl: Checklist) -> list[str]:
    """Return a list of problems; empty means the response is usable."""
    problems: list[str] = []
    version = response.get("checklist_version")
    if version != cl.version:
        problems.append(f"checklist_version {version!r} != pinned {cl.version!r}")

    responses = response.get("responses")
    if not isinstance(responses, dict):
        return problems + ["'responses' missing or not an object"]

    unknown = sorted(set(responses) - set(cl.by_id))
    if unknown:
        problems.append(f"unknown item ids (the app rejects the whole load): {', '.join(unknown)}")
    missing = [i["id"] for i in cl.items if i["id"] not in responses]
    if missing:
        problems.append(f"{len(missing)} item(s) unanswered: {', '.join(missing)}")

    for item_id, answer in responses.items():
        where = f"{item_id}:"
        if not isinstance(answer, dict):
            problems.append(f"{where} answer is not an object")
            continue
        reason = answer.get("reason")
        if not isinstance(reason, str):
            problems.append(f"{where} 'reason' must be a string (the app rejects anything else)")
        elif len(reason) > REASON_MAX:
            problems.append(f"{where} reason is {len(reason)} chars; the app truncates at {REASON_MAX}")
        elif DRAFT_PLACEHOLDER in reason:
            problems.append(f"{where} still carries the probe draft's placeholder reason: this item was "
                            "never answered")
        status = answer.get("status")
        if status is None:
            problems.append(f"{where} no 'status' (see references/verdicts.md)")
        elif status not in STATUS_VALUE:
            problems.append(f"{where} unknown status {status!r}")
        else:
            expected = STATUS_VALUE[status]
            if "value" in answer and answer["value"] != expected:
                problems.append(f"{where} value {answer['value']!r} does not follow from status {status!r}")
            if status in {"met", "partial", "unmet"} and not answer.get("evidence"):
                problems.append(f"{where} status {status!r} needs at least one evidence entry")
            if status in {"partial", "unmet", "not-checked", "not-applicable"} and not (reason or "").strip():
                problems.append(f"{where} status {status!r} needs a reason")
            if item_id in cl.by_id and cl.level(item_id) == "must" and status == "partial":
                # Not an error in the file, but it must be reported as a MUST failure.
                pass
    return problems


def app_payload(response: dict, cl: Checklist) -> dict:
    """The format-3 core: exactly what the app reads, with the extras stripped."""
    responses = {}
    for item_id in (i["id"] for i in cl.items):
        answer = response.get("responses", {}).get(item_id)
        if answer is None:
            responses[item_id] = {"value": None, "reason": ""}
            continue
        status = answer.get("status")
        value = STATUS_VALUE.get(status, answer.get("value"))
        reason = answer.get("reason") or ""
        if len(reason) > REASON_MAX:
            print(f"warning: {item_id} reason truncated to {REASON_MAX} chars", file=sys.stderr)
            reason = reason[:REASON_MAX]
        responses[item_id] = {"value": value, "reason": reason}
    return {"checklist_version": cl.version, "responses": responses}


def encode(response: dict, cl: Checklist, base_url: str = APP_URL) -> str:
    params = [
        ("checklist", cl.version),
        ("responses_version", cl.version),
        ("cols", "auto"),
        ("sections", "off"),
        ("format", str(PERSISTENCE_FORMAT)),
        ("responses", _b64(app_payload(response, cl))),
    ]
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def decode(url: str, cl: Checklist) -> dict:
    """Checklist-app URL -> response JSON, with statuses inferred from values."""
    query = urllib.parse.urlparse(url).query or url
    params = urllib.parse.parse_qs(query)
    if "responses" not in params:
        raise ValueError("no 'responses' parameter in the URL")
    fmt = params.get("format", [str(PERSISTENCE_FORMAT)])[0]
    if fmt not in {"2", str(PERSISTENCE_FORMAT)}:
        raise ValueError(f"unsupported persistence format {fmt!r}")
    payload = json.loads(base64.b64decode(params["responses"][0]).decode("utf-8"))
    version = payload.get("checklist_version") or params.get("responses_version", [None])[0]
    inferred = {"yes": "met", "no": "unmet", None: "not-checked"}
    responses = {}
    for item_id, answer in payload.get("responses", {}).items():
        value = answer.get("value")
        responses[item_id] = {
            "value": value,
            "reason": answer.get("reason", ""),
            # `no` cannot be told apart from `partial` here, and a blank answer
            # cannot be told apart from not-applicable: a human reviewer narrows
            # these down, the decoder does not guess.
            "status": inferred.get(value, "not-checked"),
            "evidence": [],
            "source": "human:web-app",
        }
    return {
        "checklist_version": version,
        "responses": responses,
        "assessor": {"skill": "human", "harness": "checklist web app", "format": int(fmt)},
    }


def template(cl: Checklist) -> dict:
    return {
        "checklist_version": cl.version,
        "responses": {
            i["id"]: {
                "value": None,
                "reason": "not yet checked",
                "status": "not-checked",
                "evidence": [],
                "source": "judgement",
                "flags": [],
            }
            for i in cl.items
        },
        "schema_version": cl.schema_version,
        "principles_version": cl.principles_version,
        "checklist_source": {k: cl.lock["source"][k] for k in ("repo", "tag", "commit")},
        "extra_items": [],
        "object": {"url": None, "commit": None, "captured_at": None, "kind": None},
        "assessor": {"skill": None, "version": None, "harness": None, "model": None, "date": None,
                     "dependencies": []},
        "scope": None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_items = sub.add_parser("items", help="list the pinned items")
    p_items.add_argument("--level", choices=["must", "should", "may"])
    p_items.add_argument("--json", action="store_true")

    for name, helptext in (("validate", "check a response JSON"), ("encode", "response JSON -> URL")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("response", type=pathlib.Path)
        if name == "encode":
            p.add_argument("--base-url", default=APP_URL)
            p.add_argument("--allow-invalid", action="store_true", help="encode even if validation fails")

    p_decode = sub.add_parser("decode", help="URL -> response JSON")
    p_decode.add_argument("url")
    p_decode.add_argument("-o", "--output", type=pathlib.Path)

    p_tpl = sub.add_parser("template", help="emit an all-not-checked response JSON")
    p_tpl.add_argument("-o", "--output", type=pathlib.Path)

    args = ap.parse_args(argv)
    cl = Checklist()

    if args.cmd == "items":
        items = [i for i in cl.items if not args.level or i["level"] == args.level]
        if args.json:
            print(json.dumps(items, indent=2))
        else:
            for i in items:
                print(f"{i['id']}\t{i['level']}\t{','.join(i['principle_codes'])}\t{i['text']}")
        return 0

    if args.cmd == "template":
        out = json.dumps(template(cl), indent=2) + "\n"
        if args.output:
            args.output.write_text(out)
            print(f"wrote {args.output}")
        else:
            sys.stdout.write(out)
        return 0

    if args.cmd == "decode":
        response = decode(args.url, cl)
        problems = [p for p in validate(response, cl) if "evidence" not in p]
        for p in problems:
            print(f"note: {p}", file=sys.stderr)
        out = json.dumps(response, indent=2) + "\n"
        if args.output:
            args.output.write_text(out)
            print(f"wrote {args.output}")
        else:
            sys.stdout.write(out)
        return 0

    response = json.loads(args.response.read_text())
    problems = validate(response, cl)

    if args.cmd == "validate":
        if problems:
            for p in problems:
                print(f"error: {p}", file=sys.stderr)
            return 1
        print(f"ok: {len(response['responses'])} answers against checklist {cl.version}")
        return 0

    if problems and not args.allow_invalid:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        print("refusing to encode an invalid response; pass --allow-invalid to override", file=sys.stderr)
        return 1
    print(encode(response, cl, args.base_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
