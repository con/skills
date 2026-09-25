---
name: install-apm-skills
description: Install, update, or migrate reusable skills in a downstream project using APM, with pinned dependency metadata and Git-ignored deployed content. Use for any requested skill installation that APM can manage, including first-time setup. Does not author reusable skill source or install unrelated runtimes.
---

# Install reusable skills with APM

Keep reusable skill development in its dedicated source repository (normally `con/skills`).
Downstream Git tracks dependency intent, exact resolution, and setup instructions; downloaded skill content is disposable.
Use APM for any selected reusable skill it can install.
Discovery tools may search and preview, but must not create a second installation or lock in the consumer.

## Inspect and prepare

1. Inspect the project's agent guidance, dependency manager, setup tasks, Git status, existing APM state, and installed skills.
   Preserve unrelated changes.
2. Inspect the selected upstream package and intended revision.
   Prefer its source-owned `apm.yml`.
   If packaging is missing, add it in the dedicated source repository and verify it there before adopting it downstream.
   Do not create a consumer-local copy to develop or patch a reusable skill.
3. Add an exact, tested `apm-cli` version as a development/setup dependency using the project's existing dependency manager, and update its environment lock.
   Do not assume a global executable or require the Workshop.
   If there is no manager, use a small pinned setup requirements file and an isolated venv; document its creation.
   Avoid a new environment manager just for skills.
4. Select explicit APM targets matching the actual clients.
   `agent-skills` deploys to `.agents/skills/`; Claude uses `.claude/skills/`.
   Consult installed `apm install --help` for version-specific options.
   Do not auto-enable all targets or install MCP servers when only skills were requested.

## Install and keep the footprint small

Use the project environment for each command below.
Replace PACKAGE, REF, and SKILL with the verified package, preferably a full Git commit SHA, and selected skill name.
Multiple `--skill` arguments select a subset.

```console
apm install PACKAGE#REF --skill SKILL --target agent-skills --dry-run
apm install PACKAGE#REF --skill SKILL --target agent-skills
```

Inspect the preview before applying.
A requested installation authorizes the normal apply step.
Do not use `--force` to bypass collisions or scan findings.
Use `--no-policy` only when deliberately excluding organization-policy lookup, and explain that choice; do not silently weaken an existing policy.

- Track `apm.yml` and the generated `apm.lock.yaml`.
  Preserve unrelated manifest entries and persist the selected `targets:`.
  APM owns lock generation.
- Ignore `/apm_modules/` and every installed skill directory written by APM.
  Base ignores on actual deployment paths in the lock, not guessed names.
  Ignore all of `/.agents/skills/` only when it contains exclusively generated dependencies; otherwise list owned subdirectories individually.
  Apply the same rule to other targets.
  Never ignore whole `.github/` or `.claude/` trees.
- Never ignore canonical skill source in its dedicated repository.
  `.apm/` can contain source; it is not interchangeable with the `apm_modules/` cache.
- If generated copies were tracked, reconcile local edits with upstream first.
  After their content is safely represented by the chosen source revision, untrack only verified generated paths with `git rm --cached`, retaining the working files.
  Never discard unreviewed edits or untrack project-owned code.
- Add or update root `AGENTS.md` without replacing existing guidance.
  Add a short setup note to the existing README/development documentation and expose the restore command through the existing setup task. Use the template in [consumer-setup.md](references/consumer-setup.md).

## Restore, verify, and update

The setup task runs `apm install --frozen` through the pinned environment.
Bootstrap before starting the agent so native skill discovery sees the files; restart/reload an already running client if needed.
An AGENTS.md note alone is not an automatic loader.
Skills do not require compiling their full content into the tracked AGENTS.md.

Verify in a disposable consumer containing only tracked setup and dependency metadata: restore the environment, run the setup task, confirm selected skills and resources are present, then run `apm audit --ci`.
Confirm `git status` shows no generated skill files or unexpected manifest/lock changes. For a project with native skills, investigate ownership/drift failures rather than hiding all audit failures with a blanket bypass.
Do not delete the real project's installed directories merely to test restoration.

For updates, change only the requested dependency/ref/selection, let APM regenerate the lock, review source changes, and repeat frozen restoration and audit.
Preserve unrelated pins.
Normal downstream updates should change metadata (SHAs, hashes, and APM deployment records), not copied skill bodies.
Initial adoption also changes setup, ignores, and documentation; changing the selected skills can legitimately change deployment paths in the lock.

Report the canonical source/ref, selected skills, tracked setup files, ignored paths, and actual validation.
Committing or publishing follows the project's existing authorization and contribution rules.
