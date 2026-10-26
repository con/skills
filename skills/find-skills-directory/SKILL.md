---
name: find-skills-directory
description: Find the absolute directory of an installed skill by name, across the Claude Code and agent skill roots. Use when another skill needs its bundled scripts or files and must locate them without hard-coding an install path.
allowed-tools: Bash
user-invocable: false
version: 0.1.0
---

# Find Skills Directory

Given a skill name, print the absolute path of its directory.

## Usage

Replace `NAME` with the skill's directory name:

```bash
find -L ~/.claude/skills ./.claude/skills ~/.agents/skills ./.agents/skills \
  -maxdepth 2 -type d -name NAME 2>/dev/null | head -1 | xargs -r realpath
```

- Prints one absolute path, or nothing if the skill is not installed in those roots.
- If nothing prints, say so and stop. Do not guess a path.
- Use the printed path as the value of `SKILL_DIR` for the calling skill.
