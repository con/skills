#!/usr/bin/env python3
"""Prove source packaging and metadata-only consumer restoration with real APM."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

import yaml

ROOT = Path(__file__).resolve().parent.parent


def run(*args: str, cwd: Path, ok: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=cwd, text=True, check=False)
    if ok:
        result.check_returncode()
    return result


def check_content(consumer: Path, package: Path, names: list[str]) -> None:
    deployed = consumer / ".agents/skills"
    actual = sorted(p.name for p in deployed.iterdir() if p.is_dir())
    assert actual == sorted(names), (actual, names)
    for name in names:
        for source in (package / "skills" / name).rglob("*"):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            destination = (
                deployed / name / source.relative_to(package / "skills" / name)
            )
            assert destination.is_file(), f"missing resource: {destination}"
            # APM may normalize Markdown links; non-Markdown resources are exact.
            if source.suffix != ".md":
                assert destination.read_bytes() == source.read_bytes(), destination
    ignored = run(
        "git", "check-ignore", "apm_modules/", ".agents/skills/", cwd=consumer
    )
    assert ignored.returncode == 0
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=consumer, text=True
    )
    assert not untracked.strip(), f"unexpected untracked files: {untracked}"
    run("git", "diff", "--exit-code", cwd=consumer)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", help="Published Git package#full-SHA; default: local snapshot"
    )
    args = parser.parse_args()
    if args.source and not re.fullmatch(r".+#[0-9a-f]{40}", args.source):
        parser.error("--source must name a Git package and full lowercase commit SHA")
    manifest = yaml.safe_load((ROOT / "apm.yml").read_text())
    assert manifest["includes"] == ["skills"]
    names = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
    assert names, "empty skill collection"
    with tempfile.TemporaryDirectory(prefix="con-skills-apm-") as directory:
        base = Path(directory)
        package = base / "package"
        package.mkdir()
        shutil.copy2(ROOT / "apm.yml", package / "apm.yml")
        for name in names:
            shutil.copytree(
                ROOT / "skills" / name,
                package / "skills" / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
            )
        source = args.source or "../package"
        # Both complete collection and selective installation must survive replay.
        for selection in (names, ["install-apm-skills", "author-apm-skills"]):
            consumer = base / ("all" if selection == names else "selected")
            consumer.mkdir()
            dep = (
                {
                    "git": source.rsplit("#", 1)[0],
                    "ref": source.rsplit("#", 1)[1],
                    "skills": selection,
                }
                if args.source
                else {"path": source, "skills": selection}
            )
            (consumer / "apm.yml").write_text(
                yaml.safe_dump(
                    {
                        "name": "con-skills-consumer",
                        "version": "0.0.0",
                        "targets": ["agent-skills"],
                        "dependencies": {"apm": [dep]},
                    },
                    sort_keys=False,
                )
            )
            (consumer / ".gitignore").write_text("/apm_modules/\n/.agents/skills/\n")
            (consumer / "AGENTS.md").write_text(
                "Run apm install --frozen before work. Reusable skill copies are generated.\n"
            )
            run("git", "init", "--quiet", cwd=consumer)
            # Fixtures intentionally have no organization policy or credentials.
            run("apm", "install", "--no-policy", cwd=consumer)
            run(
                "git",
                "add",
                "apm.yml",
                "apm.lock.yaml",
                ".gitignore",
                "AGENTS.md",
                cwd=consumer,
            )
            check_content(consumer, package, selection)
            run("apm", "audit", "--ci", "--no-policy", cwd=consumer)
            metadata = {
                name: (consumer / name).read_bytes()
                for name in ("apm.yml", "apm.lock.yaml", ".gitignore", "AGENTS.md")
            }
            # A fresh checkout has only metadata: reconstruct that state, without a commit.
            fresh = base / (consumer.name + "-fresh")
            fresh.mkdir()
            for name, data in metadata.items():
                (fresh / name).write_bytes(data)
            run("git", "init", "--quiet", cwd=fresh)
            run("git", "add", ".", cwd=fresh)
            run("apm", "install", "--frozen", "--no-policy", cwd=fresh)
            check_content(fresh, package, selection)
            assert all(
                (fresh / name).read_bytes() == data for name, data in metadata.items()
            )
            run("apm", "audit", "--ci", "--no-policy", cwd=fresh)
            if args.source:
                lock = yaml.safe_load((fresh / "apm.lock.yaml").read_text())
                expected = args.source.rsplit("#", 1)[1]
                assert any(
                    d.get("resolved_commit") == expected for d in lock["dependencies"]
                )
            # Integrity checking must notice a changed deployed instruction.
            with (fresh / ".agents/skills" / selection[0] / "SKILL.md").open(
                "a"
            ) as out:
                out.write("\nUnexpected local change.\n")
            print("Expecting audit failure for intentionally modified fixture:", flush=True)
            result = run("apm", "audit", "--ci", "--no-policy", cwd=fresh, ok=False)
            assert result.returncode != 0, "audit accepted modified deployed skill"
        print("APM package, selection, metadata-only replay, and tamper checks passed.")


if __name__ == "__main__":
    main()
