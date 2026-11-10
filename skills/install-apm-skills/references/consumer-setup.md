# Project setup

Add `apm install --frozen` to the project's existing setup task.
Document the runnable command and any environment prerequisite; setup must work before the skill is loaded.
Reuse that command in agent guidance and CI rather than duplicating setup logic.

Suggested agent guidance (replace SETUP_COMMAND):

> Run `SETUP_COMMAND` to restore skills from `apm.lock.yaml` before starting work.
> Installed copies are generated and ignored; edit their upstream source and update the dependency instead.
> Report setup failures rather than claiming missing skills were loaded.

Track `apm.yml`, `apm.lock.yaml`, and setup files.
For a project with only generated `.agents/` content:

```gitignore
/apm_modules/
/.agents/
```

If `.agents/` also contains project-owned files, ignore only APM's deployed skill directories instead.
Use the lock's actual paths for other targets and verify ignores with `git check-ignore`.
