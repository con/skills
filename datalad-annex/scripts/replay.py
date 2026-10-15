#!/usr/bin/env python3
"""Explicit DataLad 1.7.1 compatibility for one Conventional-subject prefix."""

import argparse
from contextlib import contextmanager
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys

import datalad
from datalad.api import Dataset

SUPPORTED_VERSION = "1.7.1"
PREFIX = re.compile(
    r"\A[a-z][a-z0-9-]*(?:\([^\r\n()]+\))?!?: [^\r\n]+\n\n"
    r"(?=\[DATALAD RUNCMD\] )"
)


def git(dataset, *args):
    return subprocess.check_output(
        ["git", "-C", str(dataset), *args], text=True
    ).strip()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@contextmanager
def compatibility_parser():
    if datalad.__version__ != SUPPORTED_VERSION:
        raise RuntimeError(
            f"Adapter supports DataLad {SUPPORTED_VERSION}; found {datalad.__version__}"
        )
    module = importlib.import_module("datalad.local.rerun")
    original = module.get_run_info

    def parse(dataset, message):
        if PREFIX.match(message):
            message = PREFIX.sub("", message, count=1)
        elif "[DATALAD RUNCMD]" in message and not message.startswith("[DATALAD RUNCMD] "):
            raise ValueError("Unsupported run-message prefix; history was not changed")
        return original(dataset, message)

    module.get_run_info = parse
    try:
        yield original, parse
    finally:
        module.get_run_info = original


def execute(args, receipt):
    dataset = Path(args.dataset).resolve()
    revision = git(dataset, "rev-parse", "--verify", f"{args.revision}^{{commit}}")
    ds = Dataset(dataset)
    message = git(dataset, "show", "-s", "--format=%B", revision)
    receipt.update(
        dataset=str(dataset), revision=revision,
        datalad_version=datalad.__version__, python=sys.executable,
        message_sha256=hashlib.sha256(message.encode()).hexdigest(),
        qualification="explicit process-local compatibility, not native rerun",
    )
    manifest = dataset / "pixi.toml"
    lock = dataset / "pixi.lock"
    if not manifest.is_file() or not lock.is_file():
        raise RuntimeError("Recipient needs its root manifest and the recorded ignored lock")
    manifest_hash, lock_hash = sha256(manifest), sha256(lock)
    receipt.update(manifest_sha256=manifest_hash, lock_sha256=lock_hash)
    recorded_manifest = subprocess.check_output(
        ["git", "-C", str(dataset), "show", f"{revision}:pixi.toml"]
    )
    if hashlib.sha256(recorded_manifest).hexdigest() != manifest_hash:
        raise RuntimeError("Recorded revision manifest differs; supply that run's environment")
    onto = None
    if args.action == "rerun":
        onto = git(dataset, "rev-parse", "--verify", f"{args.onto}^{{commit}}")
        historical_manifest = subprocess.check_output(
            ["git", "-C", str(dataset), "show", f"{onto}:pixi.toml"]
        )
        if hashlib.sha256(historical_manifest).hexdigest() != manifest_hash:
            raise RuntimeError("Replay base manifest differs; supply that run's environment")
        receipt["onto"] = onto
    with compatibility_parser() as (native, parse):
        receipt["parser_file"] = inspect.getsourcefile(native)
        receipt["parser_sha256"] = sha256(receipt["parser_file"])
        receipt["native_recognized"] = native(ds, message)[1] is not None
        info = parse(ds, message)[1]
        if not info or info.get("exit") != 0:
            raise RuntimeError("Requested revision has no supported successful run record")
        receipt["recorded_command"] = info["cmd"]
        kwargs = dict(revision=revision, on_failure="ignore", result_renderer="disabled")
        if args.action == "discover":
            kwargs["report"] = True
        else:
            kwargs.update(onto=onto, branch=args.branch)
        results = list(ds.rerun(**kwargs))
        receipt["results"] = results
        errors = [r for r in results if r.get("status") in {"error", "impossible"}]
        if args.action == "discover":
            actual = [r for r in results if r.get("rerun_action") == "run"]
        else:
            actual = [r for r in results if r.get("action") == "run"
                      and r.get("status") == "ok" and r.get("exit_code") == 0]
        if errors or not actual:
            raise RuntimeError("No successful requested run result; inspect receipt")
    if sha256(manifest) != manifest_hash or sha256(lock) != lock_hash:
        raise RuntimeError("Replay changed its recorded environment inputs")
    receipt.update(ok=True, result_revision=git(dataset, "rev-parse", "HEAD"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("discover", "rerun"))
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--onto")
    parser.add_argument("--branch", default="codex/replayed")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "rerun" and not args.onto:
        parser.error("rerun requires --onto with the recorded pre-run commit")
    if args.receipt.exists():
        parser.error("receipt already exists; preserve it and choose a new path")
    receipt = {"action": args.action, "ok": False}
    try:
        execute(args, receipt)
    except Exception as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(receipt, default=str))
    return 0 if receipt["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
