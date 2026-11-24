---
name: code-quality-review-shell
version: 0.1.0
description: Shell guide for the code-quality review skills — which POSIX sh and Bash scripts a review covers (including shell embedded in CI workflows, Makefiles, and Dockerfiles), which tools sweep them (shellcheck, shfmt, and actionlint, static when run without the project's configuration), shell checks such as strict mode, quoting, Bash features under /bin/sh, and snippets copied between scripts and workflows, false positives such as sourced libraries and scripts run from outside the repository, and the commands that verify a change. review-repo-code-quality reads it for shell code, and review-org-code-quality uses its static tools. Use when a review skill tells you to read it, or when asked for a code-quality review of shell scripts (then run review-repo-code-quality, which loads this guide).
allowed-tools: Read, Skill
user-invocable: true
---

# Shell guide for the code-quality reviews

`review-repo-code-quality` holds the review procedure, the report layout,
and the architecture principles that apply to every language; this guide
adds what holds for shell scripts only. That skill reads it in Step 1 for
every repository with shell code in scope, and `review-org-code-quality`
uses its **static** tools in Phase 2. The category prefixes (`ARC`, `DC`,
`DUP`, `CON`, `CL`, `NV`) and the **static** / **consent** marks are
defined in `review-repo-code-quality`.

## When invoked directly

This guide is not a review on its own. Asked for a code-quality review of
shell scripts, or for this guide by name, run `review-repo-code-quality`
(with `Skill`, or by reading `../review-repo-code-quality/SKILL.md`); its
Step 1 loads this guide. Limit that review to the shell code only when
the user asked for that; otherwise it covers every language in the
repository, each with its own guide. If `review-repo-code-quality` is not
installed, stop and ask the user to install it; do not review from this
guide alone.

## Recognize

`*.sh`, `*.bash`, and `*.bats` files, and scripts without an extension
whose shebang runs `sh`, `bash`, `dash`, or `ksh`. Also shell embedded
elsewhere: `run:` steps in GitHub Actions workflows, `script:` sections in
GitLab CI, Makefile recipes, Dockerfile `RUN` lines, and `package.json`
scripts. Zsh and fish scripts are not covered: shellcheck does not
support them.

## Project rules

Read `.shellcheckrc` (disabled checks, `shell=`, `source-path=`),
`.editorconfig` (shfmt takes its indentation from there), the shebangs
themselves, which decide each script's dialect, the CI steps and
`.pre-commit-config.yaml` hooks that run shellcheck or shfmt (and their
flags), and the Bats test layout if there is one.

The oldest shell the scripts must run on bounds what may be proposed:
`/bin/sh` is dash on Debian and Ubuntu and BusyBox ash on Alpine, and
macOS ships Bash 3.2, which has no associative arrays, no `mapfile`, and
no `${var,,}`.

## Tools

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Lint: idioms, bugs, portability | `shellcheck` | static with `--norc` | `shellcheck --norc --severity=style --format=gcc <files>`; list the files a script sources alongside it, and add `--enable=all` to see the optional checks |
| Shell in GitHub Actions `run:` steps | `actionlint`, your empty configuration | static | `actionlint -config-file <scratch>/actionlint.yaml -shellcheck "$(command -v shellcheck)" -oneline <workflow files>` |
| Formatting | `shfmt` | static with explicit flags (any formatting flag makes it ignore `.editorconfig`) | `shfmt -d -i <indent from .editorconfig> <files>` prints the diff; never `-w` |
| Dead code | none dedicated | static | list function definitions (`grep -nE '^[[:space:]]*(function[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*[[:space:]]*\(\)'`) and search for their callers; list scripts and search for what runs them; shellcheck `SC2034` flags unused variables |
| Complexity | none dedicated | static | script and function length (`wc -l`), nesting depth by reading |
| Tests | `bats` | consent | see Verification |

With `--norc`, shellcheck ignores the project's disabled checks: read
`.shellcheckrc` and the inline `# shellcheck disable=` comments and drop
those hits.

## Checks

Each check names the category it usually lands in. A fix that would
change behavior goes under `NV` instead, with the change spelled out.

- **One source of truth** (`ARC`): versions, paths, URLs, and tool flags
  hard-coded in several scripts or workflow steps; read them from one
  file, or from the project's own metadata.
- **Copied snippets** (`DUP`): the same install, retry, or
  version-detection block in several scripts or workflow `run:` steps
  becomes one script, a sourced function, or a composite action.
- **Scripts that outgrew shell** (`ARC`): long scripts with data
  structures, parsing, or JSON handling are clearer and testable in the
  project's main language. A rewrite is `NV` when other people or
  systems run the script.
- **Legacy syntax** (`CL`): backticks (`SC2006`), `$[ ]` arithmetic
  (`SC2007`), `expr` for arithmetic (`SC2003`), `echo $(cmd)` (`SC2005`).
- **Strict mode** (`NV`): scripts without `set -e`, `set -u`, or
  `set -o pipefail` where the project's other scripts use them. Adding
  them changes which failures stop the script; name the commands that
  would then abort.
- **Quoting** (`NV` unless the value can never contain whitespace or glob
  characters): unquoted expansions (`SC2086`, `SC2046`), and loops over
  `$(ls …)` or `$(find …)` output (`SC2045`, `SC2044`).
- **Dialect** (`NV`): Bash features in a `#!/bin/sh` script (`[[ ]]`,
  arrays, `function`, `source`, `$'…'`; shellcheck's `SC3xxx` checks).
  Either the shebang changes to Bash, which changes the interpreter, or
  the syntax becomes POSIX.
- **Unchecked `cd`** (`SC2164`), and temporary files created without
  `mktemp` or removed without a `trap` (`NV`).
- **Executable bit and shebang** (`CL`): a script with a shebang that is
  not executable, or run as `bash script.sh` despite one. Changing how it
  is invoked is `NV`.

## Not findings

What looks dead or wrong in shell but is not. List the ones you checked
under "Not changed (deliberately)".

- Functions called indirectly: through a variable (`"$cmd" "$@"`
  dispatch), from a `trap`, as completion functions (`complete -F`), or by
  the scripts and interactive shells that `source` the file. A library
  file has no callers of its own.
- Scripts run from outside the repository: commands the documentation
  gives users, cron jobs and systemd units, container `ENTRYPOINT`s, git
  hooks (`.githooks/`, `.husky/`), and CI in other repositories.
- Variables set for a script that sources this one, or exported for child
  processes (`SC2034` reports them as unused).
- Deliberate word splitting, such as `$opts` holding several flags, marked
  with `# shellcheck disable=SC2086` and a reason.
- Syntax specific to a shell, in a script whose shebang asks for that
  shell.

## Verification

- **Static, after any edit**: `bash -n <file>` (or `sh -n` for POSIX
  scripts) parses without running anything; rerun the static shellcheck
  command and compare its hits with the earlier run.
- **Baseline and after each group** (consent, in the throwaway checkout):
  the project's Bats suite (`bats test/`), or the workflow step, Makefile
  target, or `package.json` script that runs the script.
- **Scripts with effects** (consent): run the script before and after the
  change, in a scratch directory on the same inputs (`bash -x` traces each
  command), and compare outputs and the files written.
