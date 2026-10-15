#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Run the STAMPED probes over a checked-out research object.

    run_probes.py <path> [-o probes.json] [--response response.json]
                  [--only NAME ...] [--skip NAME ...] [--check-remote]
                  [--kind dataset|component|study|skill]

Writes the per-probe results, and optionally a response JSON (the format in
``stamped-conventions/references/response-format.md``) in which every item a
probe speaks to carries that probe's verdict and every other item is left
``not-checked`` for the assessing session to judge.

The probes never modify the object.  Nothing here replaces the judgement items:
a response straight out of this script is a draft, not an assessment.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from probes import REGISTRY, Object  # noqa: E402

# Worse first: when two probes answer the same item, the worse verdict wins and
# both reasons are kept.
SEVERITY = {"unmet": 0, "partial": 1, "not-checked": 2, "not-applicable": 3, "met": 4}

# A probe over a big object can collect tens of thousands of paths.  The
# report has to stay readable and committable, so lists in `details` are
# capped and the cap is stated rather than hidden.
DETAIL_CAP = 50


def cap_details(details: dict | None) -> dict:
    # A probe may carry no details at all; crashing on that turned one such
    # probe into "probe failed to run", which drops its item from the report
    # without failing anything.
    if not details:
        return {}
    out: dict = {}
    for key, value in details.items():
        if isinstance(value, list) and len(value) > DETAIL_CAP:
            out[key] = value[:DETAIL_CAP]
            out[f"{key}_total"] = len(value)
            out[f"{key}_truncated_at"] = DETAIL_CAP
        else:
            out[key] = value
    return out


def _conventions_dir(start: pathlib.Path) -> pathlib.Path | None:
    for base in (start, *start.parents):
        candidate = base.parent / "stamped-conventions"
        if (candidate / "checklist" / "lock.json").exists():
            return candidate
        candidate = base / "stamped-conventions"
        if (candidate / "checklist" / "lock.json").exists():
            return candidate
    return None


def _load_checklist(conventions: pathlib.Path):
    sys.path.insert(0, str(conventions / "scripts"))
    from encode_response import STATUS_VALUE, Checklist, template  # noqa: PLC0415

    return Checklist(), template, STATUS_VALUE


def run(obj: Object, names: list[str], check_remote: bool, allow: tuple[str, ...] = ()) -> list[dict]:
    results = []
    for name in names:
        probe = REGISTRY[name]
        try:
            if name in {"subdatasets-resolvable", "env-spec-tracked"}:
                result = probe(obj, check_remote=check_remote)
            elif name == "no-abs-paths":
                result = probe(obj, allow=allow)
            else:
                result = probe(obj)
            payload = result.asdict()
            payload["details"] = cap_details(payload["details"])
            results.append(payload)
        except Exception as exc:  # a collector failure is not an object defect
            results.append(
                {
                    "probe": name,
                    "status": "not-checked",
                    "items": [],
                    "reason": f"probe failed to run: {type(exc).__name__}: {exc}"[:250],
                    "evidence": [],
                    "details": {"collector_failure": True},
                }
            )
    return results


def merge_into_response(results: list[dict], obj: Object, checklist, template, status_value: dict,
                        kind: str | None) -> dict:
    response = template(checklist)
    answered: dict[str, dict] = {}
    for result in results:
        if result["details"].get("collector_failure"):
            continue
        for item_id in result["items"]:
            if item_id not in checklist.by_id:
                continue
            status = result.get("item_status", {}).get(item_id, result["status"])
            previous = answered.get(item_id)
            if previous is None or SEVERITY[status] < SEVERITY[previous[1]]:
                answered[item_id] = (result, status)

    for item_id, (result, status) in answered.items():
        response["responses"][item_id] = {
            # Always derived from the status, never set by hand.
            "value": status_value[status],
            "reason": result.get("item_reason", {}).get(item_id, result["reason"]),
            "status": status,
            "evidence": result["evidence"],
            "source": "probe:" + result["probe"],
            "flags": [],
        }
    for item_id, answer in response["responses"].items():
        if answer["source"] == "judgement":
            answer["reason"] = "No probe covers this item; a reading of the object is required."
        answer.setdefault("flags", [])

    extras = [
        {
            "key": result["probe"],
            "status": result["status"],
            "reason": result["reason"],
            "evidence": result["evidence"],
        }
        for result in results
        if not result["items"] and not result["details"].get("collector_failure")
    ]
    response["extra_items"] = extras
    # The app truncates a reason at 250 characters and `validate` refuses a
    # longer one, so a draft that carries one makes the run trim it by hand. A
    # probe reason that does not fit is clipped here, where the limit is known.
    for answer in response["responses"].values():
        reason = answer.get("reason") or ""
        if len(reason) > 250:
            answer["reason"] = reason[:249] + "…"
    response["object"] = {
        "url": (obj.git("config", "--get", "remote.origin.url").strip() or None),
        "commit": obj.head,
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "kind": kind,
    }
    response["assessor"] = {
        # The skill, not the script that drafted the response: three runs had
        # to correct this by hand, and one reported the draft as "not
        # stamp-ready". The version comes from the SKILL.md next to this
        # script, so it cannot drift from what shipped.
        "skill": "assess-alignment-with-stamped-principles",
        "version": _skill_version(),
        "harness": None,          # the run fills these two: a script cannot
        "model": None,            # know which harness or model is reading it
        # UTC, because the host's local "today" and the session's idea of today
        # have disagreed by a day, and the report is named after this date.
        "date": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        "drafted_by": "scripts/run_probes.py",
    }
    response["scope"] = "Probe sweep only; judgement items are left not-checked."
    return response


def _skill_version() -> str | None:
    """The `version:` from the SKILL.md beside this script."""
    skill = pathlib.Path(__file__).resolve().parent.parent / "SKILL.md"
    try:
        for line in skill.read_text().splitlines()[:30]:
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip('"\'')
    except OSError:
        pass
    return None


def summarise(results: list[dict], checklist) -> str:
    lines = [f"{'probe':<24} {'status':<15} items"]
    for result in results:
        items = ", ".join(i.split(":")[-1] for i in result["items"]) or "(extra)"
        lines.append(f"{result['probe']:<24} {result['status']:<15} {items}")
    must = [i["id"] for i in checklist.items if i["level"] == "must"]
    covered = {i for r in results for i in r["items"] if i in must}
    lines.append("")
    lines.append(f"probes answer {len(covered)}/{len(must)} MUST items; the rest need judgement")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", type=pathlib.Path, help="checked-out object to probe")
    ap.add_argument("-o", "--output", type=pathlib.Path, help="write the probe results here")
    ap.add_argument("--response", type=pathlib.Path, help="also write a draft response JSON here")
    ap.add_argument("--only", nargs="+", choices=sorted(REGISTRY), help="run just these probes")
    ap.add_argument("--skip", nargs="+", choices=sorted(REGISTRY), default=[])
    ap.add_argument("--check-remote", action="store_true", help="contact submodule urls (network)")
    ap.add_argument("--allow", nargs="+", default=[], metavar="GLOB",
                    help="paths no-abs-paths may skip, for files that genuinely have to carry a host path")
    ap.add_argument("--kind", choices=["dataset", "component", "study", "skill"])
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    root = args.path.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    obj = Object(root)
    if not obj.is_git:
        print(f"error: {root} is not a git repository; STAMPED assessment needs committed state", file=sys.stderr)
        return 2
    if subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root), capture_output=True).returncode != 0:
        print(f"error: {root} has no commits", file=sys.stderr)
        return 2

    names = [n for n in (args.only or sorted(REGISTRY)) if n not in args.skip]
    results = run(obj, names, args.check_remote, tuple(args.allow))

    conventions = _conventions_dir(pathlib.Path(__file__).resolve().parent.parent)
    if conventions is None:
        print(
            "error: stamped-conventions is not installed next to this skill; "
            "install it rather than proceeding from memory",
            file=sys.stderr,
        )
        return 2
    checklist, template, status_value = _load_checklist(conventions)

    payload = {
        "object": {"path": str(root), "commit": obj.head, "is_datalad": obj.is_datalad},
        "checklist_version": checklist.version,
        "probes": results,
    }
    if args.output:
        args.output.write_text(json.dumps(payload, indent=2) + "\n")
    if args.response:
        response = merge_into_response(results, obj, checklist, template, status_value, args.kind)
        args.response.write_text(json.dumps(response, indent=2) + "\n")
    if not args.quiet:
        print(summarise(results, checklist))
        if args.output:
            print(f"\nwrote {args.output}")
        if args.response:
            print(f"wrote {args.response}")
    if not args.output and not args.response and args.quiet:
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
