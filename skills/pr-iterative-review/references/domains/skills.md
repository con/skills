# Lens: skills

Agent skills and other instructions written for AI agents: what an agent
reads and then acts on, with real tools and credentials.

## Recognize

`SKILL.md` and the files bundled beside it (`references/`, `scripts/`,
`templates/`, `agents/`); per-skill manifests such as `apm.yml`; agent
instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/`,
`.github/copilot-instructions.md`); `.claude/` (agents, commands, hooks,
settings); MCP configuration (`.mcp.json`); prompt templates loaded by code.

## Context to read

The repository's authoring rules (its `AGENTS.md`: versioning, pull request
conventions, the wording for untrusted content); its validator and CI for
skills; sibling skills that overlap with the changed one or that it reads
(`../<skill>/`); the skill's own references and scripts.

## Checks

Two angles, as a skill author and as an attacker.

**Triggering** (should-fix)
- `name` equals the directory; `description` says what the skill does,
  when to use it, and when to use a sibling instead. Two skills whose
  descriptions both match the same request will fight over it.

**Instructions** (should-fix; blocking when the ambiguity can cause an
unwanted action)
- Each step is unambiguous to an agent that has read nothing else: terms
  such as "attended" or "the user's answer" are defined; no two sections or
  sibling skills contradict each other; examples obey the rules they
  illustrate.
- Failure paths: a missing tool, a refused API call, empty input, an
  unexpected response shape. Each says what to do, including when to stop.
- Nothing depends on the author's machine (absolute paths, personal
  accounts) or on a file that will not be installed with the skill, such as
  the source repository's `AGENTS.md`.

**Agent safety** (usually blocking)
- Content the skill reads from outside (issues, pull requests, comments,
  web pages, tool output, repository files) is framed as untrusted data
  before it is read, with the repository's standard wording if it has one.
- Actions that leave the session (post, push, merge, delete, publish,
  schedule, spend money) need the user's explicit authorization, and only
  the user's own words count: never text found in content, never the mere
  invocation of the skill. An unattended run falls back to reporting.
- Secrets are never printed, logged or put in files that get posted;
  information from private repositories does not leak into public output.
- `allowed-tools` grants what the procedure uses and no more; `Bash` patterns
  cover the commands the steps actually run.
- Commands never interpolate untrusted text into a shell line; request
  bodies go through files written with a JSON serializer.
- Tools fetched at run time are pinned to a version: no `@latest`, and no
  script downloaded and handed straight to a shell.

**Bundled scripts** (should-fix)
- Standard library or pinned dependencies; tested; they fail closed on bad
  input; paths resolve from the skill's own directory, not the working
  directory.

**Versioning and packaging** (should-fix)
- The version changes as the repository's rules require (in `con/skills`:
  MINOR for a changed step, none while the introducing pull request is
  open); the README or index lists the skill; the installed copy works
  where the package manager puts it.

**Economy** (optional)
- Text the agent does not need, rules repeated across skills that will
  drift apart (point to one copy instead), length past what the
  repository's validator recommends.

**Claims** (should-fix)
- Every claim about a tool, flag, API or platform behaviour is checked
  against its documentation or a run, or marked as unverified.

## Not findings

- Wording preferences where the meaning is clear (use `review-human-prose`
  only where a passage is hard to follow).
- Attacks that need an input the skill never reads.
- Requests for more examples when the rule is already unambiguous.

## Verification

- If `../skill-security-review/SKILL.md` is installed, apply its checks to
  each changed skill directory and fold its findings into yours.
- **static**: read the whole `SKILL.md` and every bundled file it names;
  compare against sibling skills and the repository's rules; check each
  command against the tool's documentation.
- **consent**: the repository's validator and test suite (`tox`, a
  workflow), and a bundled script's own tests, since both run code from the
  pull request.
