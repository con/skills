#!/usr/bin/env python3
"""Validate structure and evidence references; this cannot grade scientific truth.

Runtime dependency: Python 3.9+ and jsonschema>=4,<5.
"""
import argparse
import json
from pathlib import Path
import sys

def semantic_errors(record):
    errors = []
    criteria = list(record["science"])
    for entries in record["research_object"].values():
        criteria.extend(entries)
    ids = [criterion["id"] for criterion in criteria]
    if len(ids) != len(set(ids)):
        errors.append("Criterion IDs must be unique across science and research-object dimensions")
    for criterion in criteria:
        observations = criterion["observations"]
        observation_ids = [item["id"] for item in observations]
        if len(observation_ids) != len(set(observation_ids)):
            errors.append(f"{criterion['id']}: repeated observation ID")
        actual = {item["activity"] for item in observations}
        required = set(criterion["required_activities"])
        if not required <= actual:
            errors.append(f"{criterion['id']}: required activities lack observations, even not_attempted ones")
        if criterion["judgment"] == "demonstrated":
            established = {item["activity"] for item in observations if item["status"] == "completed" and item["evidence"]}
            if not required <= established:
                errors.append(f"{criterion['id']}: demonstrated requires completed evidence for every required activity")
        if criterion["judgment"] == "not_demonstrated" and not any(item["status"] == "completed" and item["evidence"] for item in observations):
            errors.append(f"{criterion['id']}: observed unmet judgment requires completed evidence; use unknown for missing evidence")
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment", type=Path)
    args = parser.parse_args()
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        parser.error("Install declared dependency jsonschema>=4,<5 in the chosen environment")
    schema = json.loads((Path(__file__).resolve().parents[1] / "references" / "research-assessment.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    record = json.loads(args.assessment.read_text())
    errors = [str(error.message) for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record)]
    if not errors:
        errors.extend(semantic_errors(record))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Assessment structure and evidence bookkeeping are valid; judgments still require review.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
