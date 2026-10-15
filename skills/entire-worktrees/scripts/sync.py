#!/usr/bin/env python3
"""Reuse approved Codex hook hashes for an identical Entire worktree config."""

from __future__ import annotations

import argparse
import json
import tomllib
import re
from pathlib import Path


BLOCK_RE = re.compile(
    r'^\[hooks\.state\."(?P<path>.+?):(?P<event>[^:]+):(?P<index>\d+):(?P<subindex>\d+)"\]\n'
    r'trusted_hash = "(?P<hash>[^"]+)"\n?',
    re.MULTILINE,
)


def config_path() -> Path:
    codex_home = Path.home() / ".codex"
    return Path(__import__("os").environ.get("CODEX_HOME", str(codex_home))) / "config.toml"


def hook_path(worktree: Path) -> Path:
    path = worktree / ".codex" / "hooks.json"
    if not path.is_file():
        raise SystemExit(f"missing hook file: {path}")
    return path


def approved_blocks(text: str) -> list[re.Match[str]]:
    return list(BLOCK_RE.finditer(text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--source", type=Path, help="Approved byte-identical hook file")
    parser.add_argument("--dry-run", action="store_true", help="Inspect without changing trust")
    args = parser.parse_args()

    worktree = args.worktree.expanduser().resolve()
    target = hook_path(worktree)
    cfg = config_path()
    if not cfg.is_file():
        raise SystemExit(f"missing Codex config: {cfg}")

    text = cfg.read_text()
    parsed = tomllib.loads(text)
    project = parsed.get("projects", {}).get(str(worktree), {})
    trust = project.get("trust_level")
    if trust not in (None, "trusted"):
        raise SystemExit("project is explicitly untrusted; review it in Codex first")
    if str(worktree) in parsed.get("projects", {}) and trust is None:
        raise SystemExit("existing project entry needs native Codex trust review")
    matches = approved_blocks(text)
    target_bytes = target.read_bytes()
    target_key = str(target)
    existing = {m.group("path"): m for m in matches}

    source_paths = sorted({m.group("path") for m in matches if Path(m.group("path")).is_file()})
    if args.source:
        source_paths = [str(args.source.expanduser().resolve())]
    # Every configured hook needs an approval; a partial source is insufficient.
    hooks = json.loads(target_bytes).get("hooks", {})
    expected = set()
    for event, groups in hooks.items():
        event_key = re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()
        for index, group in enumerate(groups):
            for subindex, hook in enumerate(group.get("hooks", [])):
                if hook.get("disabled"):
                    raise SystemExit("disabled hook requires native review")
                expected.add(f"{event_key}:{index}:{subindex}")
    if not expected:
        raise SystemExit("empty hook configuration")
    def approvals(path):
        return {f'{m.group("event")}:{m.group("index")}:{m.group("subindex")}': m
                for m in matches if m.group("path") == str(path)}
    source = next((Path(path) for path in source_paths
                   if Path(path).is_file() and Path(path).read_bytes() == target_bytes
                   and expected <= approvals(path).keys()), None)
    if source is None:
        raise SystemExit("no approved hook file with identical bytes; manual /hooks review is required")

    source_matches = [m for suffix, m in approvals(source).items() if suffix in expected]
    if not source_matches:
        raise SystemExit(f"approved source has no trust records: {source}")

    additions: list[str] = []
    states = parsed.get("hooks", {}).get("state", {})
    for match in source_matches:
        suffix = f'{match.group("event")}:{match.group("index")}:{match.group("subindex")}'
        key = f"{target_key}:{suffix}"
        if states.get(key, {}).get("disabled") or states.get(f"{source}:{suffix}", {}).get("disabled"):
            raise SystemExit(f"disabled hook needs native review: {suffix}")
        old = existing.get(target_key)
        if old is not None:
            same = [m for m in matches if m.group("path") == target_key and f'{m.group("event")}:{m.group("index")}:{m.group("subindex")}' == suffix]
            if same and same[0].group("hash") == match.group("hash"):
                continue
            if same:
                raise SystemExit(f"existing trust hash differs for {key}; manual review required")
        additions.append(
            f'[hooks.state."{key}"]\ntrusted_hash = "{match.group("hash")}"\n'
        )

    project_trust_added = trust != "trusted"
    if project_trust_added:
        additions.append(
            f'[projects.{json.dumps(str(worktree))}]\ntrust_level = "trusted"\n'
        )
    if additions and not args.dry_run:
        if cfg.read_text() != text:
            raise SystemExit("Codex config changed; rerun after inspecting it")
        with cfg.open("a") as handle:
            handle.write("\n" + "\n".join(additions))
    print(f"worktree={worktree}")
    print(f"dry_run={args.dry_run}")
    print(f"source={source}")
    print(f"trust_records_added={len(additions) - int(project_trust_added)}")
    print(f"project_trust_added={project_trust_added}")
    print("Trust records only: apply through Codex's native controls as needed, "
          "then verify capture, GitHub sync, and hosted ingestion separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
