---
name: con-skill-conventions
description: "Shared conventions that skills in this collection follow at run time: respecting the target project's own configuration, settings, and contribution rules (pull request template, contribution guide) over the skill's defaults. Not invoked directly. Use when a skill tells you to read it."
allowed-tools: Read
user-invocable: false
---

# con/skills conventions

This skill's payload is [`conventions.md`](conventions.md).
Skills that need it declare it as a dependency in their `apm.yml` (`apm: [{path: ../con-skill-conventions}]`), so APM installs it beside them, and read `../con-skill-conventions/conventions.md` relative to their own directory.
If that file is not installed, the calling skill stops and asks the user to install `con-skill-conventions`; it does not proceed from memory.

Bump this skill's `apm.yml` version when a rule in `conventions.md` changes (see `AGENTS.md`, "Skill versions"); the skills that read it need no bump for that.
