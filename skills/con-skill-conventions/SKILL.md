---
name: con-skill-conventions
description: Shared conventions that skills in this collection follow at run time, such as respecting the target project's pull request template and contribution guide. Not invoked directly. Use when a skill tells you to read it.
allowed-tools: Read
user-invocable: false
---

# con/skills conventions

This skill's payload is [`conventions.md`](conventions.md).
Skills that need it declare it as a dependency in their `apm.yml` (`apm: [{path: ../con-skill-conventions}]`), so APM installs it beside them, and read `../con-skill-conventions/conventions.md` relative to their own directory.
If that file is not installed, the calling skill stops and asks the user to install `con-skill-conventions`; it does not proceed from memory.
