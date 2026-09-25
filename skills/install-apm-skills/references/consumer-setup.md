# Consumer setup template

Adapt the command to the existing environment manager; keep one authoritative setup task and reuse it in documentation and CI.
Pin the APM CLI itself as a setup/development dependency.
The tested CON package uses `apm-cli==0.31.0`.
Do not upgrade an existing pin without checking compatibility.

For a Pixi project, add `apm-cli = "==0.31.0"` under `[pypi-dependencies]`, update `pixi.lock`, and add a task equivalent to:

```toml
[tasks]
setup-skills = "apm install --frozen"
```

Do not replace an existing `[tasks]` table.
A clean checkout can then use `pixi run --locked setup-skills`.
For uv, tox, or another manager, use its existing locked setup convention instead.

## AGENTS.md note

Replace SETUP_COMMAND with the real runnable project command:

> Reusable skills are APM dependencies.
> Run `SETUP_COMMAND` before starting
> work; it restores the versions in `apm.lock.yaml`.
> Installed skill files are
> generated and Git-ignored.
> Develop reusable skills in their dedicated source
> repository (normally `con/skills`), then update this project's APM pin and
> lock.
> Do not edit or commit deployed skill copies.
> If setup fails, report it
> rather than claiming the missing skills were loaded.

## README/development setup note

Document the environment prerequisite, exact setup command, and that it needs network access on first installation (and appropriate credentials for private sources).
State where skills appear and how to update a dependency deliberately.
Fresh-clone setup must not depend on a preinstalled skill or Workshop checkout.

## Git ignores

An example for a single external skill; use actual lockfile deployment paths:

```gitignore
/apm_modules/
/.agents/skills/example-skill/
```

Include target-specific deployed paths when selected.
Keep the manifest, lock, setup/environment files, and instructions tracked.
Use `git check-ignore` and `git ls-files` to verify both sides of this boundary.
