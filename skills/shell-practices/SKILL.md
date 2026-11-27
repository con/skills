---
name: shell-practices
description: Shell practices for Bash and POSIX sh in project scripts and in CI workflows, Makefiles, Dockerfiles, and Singularity/Apptainer recipes — the house's preferences (POSIX syntax under /bin/sh, strict mode, quoted expansions, one list for a closed set of values, one script for copied snippets, mktemp and trap, shellcheck and shfmt), public surface and deprecation, false positives, and verification, with the review tools and detailed checks in references/review.md. Use when writing, changing, or reviewing shell scripts or embedded shell, including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# Shell practices

The house's practices for shell scripts, for three kinds of work: writing
or changing it, reviewing a pull request, and the code-quality reviews.
Read `general-practices` first: it says how to weigh these preferences
against the project's own rules and your own judgment, and defines the
marks and categories used here.
[references/review.md](references/review.md) holds what a review needs
beyond them: the tools with their **static** / **consent** marks, the
detailed checks with their categories and pitfalls, currency sources, and
verification commands.

It is written for Bash and POSIX sh in research software: helper,
release, test, and data-processing scripts, and the shell in GitHub
Actions workflows, Makefiles, Dockerfiles, and Singularity/Apptainer
recipes, run on Linux CI and on contributors' macOS machines. Other
shells (zsh, ksh, fish) and CI systems other than GitHub Actions are left
out: check their conventions before reporting there.

## Recognize

`*.sh`, `*.bash`, and `*.bats` files, and scripts without an extension
whose shebang runs `sh`, `bash`, or `dash`. Also shell embedded
elsewhere, which counts even in a repository with no script file: `run:`
steps in GitHub Actions workflows and composite actions (`action.yml` or
`action.yaml` with `using: composite`), Makefile recipes, Dockerfile `RUN`
lines, and the `%post`, `%test`, and `%runscript` sections of
Singularity/Apptainer recipes.

Awk programs embedded in shell belong to `awk-practices`; this
guide reviews the command around each one.

## Project rules

Read the shebangs, which decide each script's dialect, `.shellcheckrc`,
`.editorconfig` (shfmt reads its options there), and the CI steps and
pre-commit hooks that run the linters. The oldest shell the scripts must run
on bounds what may be proposed: `/bin/sh` is dash on Debian and Ubuntu and
BusyBox ash on Alpine, and macOS ships Bash 3.2, without associative arrays,
`mapfile`, or `${var,,}`.

## Preferences

- **Dialect**: Bash features (`[[ ]]`, arrays, `source`) in a `#!/bin/sh`
  script become POSIX, or the shebang changes to Bash (`NV`). A script with a
  shebang is executable, not run as `bash script.sh`.
- **Strict mode**: `set -e`, `set -u`, and `set -o pipefail` where the
  project's other scripts use them; adding them changes which failures stop
  the script. In a `#!/bin/sh` script `pipefail` is a dialect change, since
  dash rejects it and exits, unless every `/bin/sh` the script must run on
  supports it.
- **Quoting**: expansions are quoted; an empty unquoted one disappears, while
  `"$var"` passes an empty argument. Deliberate word splitting carries
  `# shellcheck disable=SC2086` and a reason.
- **One source of truth**: the values that `case` patterns, `usage()` text,
  and workflow `choice` options repeat become one list (a variable or array in
  a sourced file) that both the validation and the usage text read; versions,
  paths, URLs, and tool flags are defined once.
- **Copied snippets**: an install or retry block repeated across scripts or
  `run:` steps becomes one script, a sourced function, or a composite action,
  run under each copy's options (`shell: bash` adds `-o pipefail` to the
  default `bash -e`).
- **Current syntax**: `grep -E` and `grep -F`, not `egrep` and `fgrep`;
  `command -v`, not `which`; backticks rewritten as `shfmt -d` does. Replacing
  `expr` or `echo "$(cmd)"` can change behavior (references/review.md, Legacy
  syntax).
- **Directories and temporary files**: every `cd` is checked, and temporary
  files come from `mktemp` and are removed by a `trap`.
- **Scripts that outgrew shell**: long ones with data structures, parsing, or
  JSON handling are clearer and testable in the project's main language.
- **Lint, format, and test**: shellcheck, shfmt, hadolint for Dockerfiles,
  actionlint for workflows, and Bats, with CI and pre-commit pins near their
  latest releases.

## Public surface and deprecation

- **Interface**: a script's options, arguments, the environment
  variables it reads, its exit statuses, and the output other scripts or
  CI parse are its interface, as are the functions of a library that
  other scripts source. To retire an option or variable, keep accepting
  it, print a one-line warning naming the replacement to standard error
  (`echo "--old is deprecated; use --new" >&2`), and keep it in the usage
  text until it is removed. Changing any of these is `NV`.

## Not findings

Functions called indirectly (through a variable, a `trap`, `complete -F`, or a
sourcing script), Bats hooks such as `setup` and `teardown`, scripts run from
outside the repository (documented commands, cron jobs, container
`ENTRYPOINT`s, git hooks), and variables that `SC2034` calls unused but a
sourcing script or `${!name}` reads. The full list is in
[references/review.md](references/review.md).

## Verification

Check each changed file with `bash -n` (`sh -n` for POSIX scripts), which runs
nothing, and with shellcheck where installed, comparing its hits before and
after. Run the project's own tests before and after a change (its Bats suite,
or the workflow step or Makefile target that runs the script), and for a
script with effects compare outputs, exit statuses, and files written on the
same inputs. The review's commands are in
[references/review.md](references/review.md).
