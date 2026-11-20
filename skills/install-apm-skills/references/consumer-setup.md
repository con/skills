# Project setup

Add `apm install --frozen` to the project's existing setup task.
Document the runnable command and any environment prerequisite; setup must work before the skill is loaded.
Reuse that command in agent guidance and CI rather than duplicating setup logic.

Suggested agent guidance (replace SETUP_COMMAND):

> Run `SETUP_COMMAND` to restore skills from `apm.lock.yaml` before starting work.
> Installed copies are generated and ignored; edit their upstream source and update the dependency instead.
> Report setup failures rather than claiming missing skills were loaded.

Track `apm.yml`, `apm.lock.yaml`, and setup files.
For a collection whose skills are packages of their own (each `skills/<name>/` has an `apm.yml`, as in `con/skills`), list one dependency per skill so the lock records each skill's version:

```yaml
dependencies:
  apm:
    - git: con/skills
      path: skills/setup-chromatic
      ref: 0123456789abcdef0123456789abcdef01234567  # full SHA, a setup-chromatic--vX.Y.Z tag, or ^X.Y.Z
```

`apm deps list` then shows the skill under its own name and version, and a pull request moving the pin shows which skill changed.

For a project with only generated `.agents/` content:

```gitignore
/apm_modules/
/.agents/
```

If `.agents/` also contains project-owned files, ignore only APM's deployed skill directories instead.
Use the lock's actual paths for other targets and verify ignores with `git check-ignore`.
