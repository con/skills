---
name: shell-practices
description: Shell practices — the POSIX sh and Bash it covers (including shell embedded in CI workflows, Makefiles, and Dockerfiles), its static review tools, shell checks such as strict mode, quoting, Bash features under /bin/sh, and snippets copied between workflow steps, false positives, and verification commands. Use when writing, changing, or reviewing shell scripts or embedded shell, including in a pull-request review or a code-quality review (review-repo-code-quality and review-org-code-quality read it).
allowed-tools: Read
user-invocable: false
---

# Shell practices

What holds for shell scripts only, for three kinds of work: writing or
changing it, reviewing a pull request, and the code-quality reviews
(`review-repo-code-quality` reads this guide in Step 1;
`review-org-code-quality` runs its **static** tools). When writing code,
follow Project rules and Checks and leave Not findings alone; when
reviewing, report against them. The procedure, the architecture
principles, the category prefixes (`ARC`, `DC`, `DUP`, `CON`, `CL`, `NV`),
and the **static** / **consent** marks on the Tools are defined in
`review-repo-code-quality`.

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

Read `.shellcheckrc` (disabled checks, `shell=`, `source-path=`),
`.editorconfig` (shfmt reads its formatting options from there, and its
`ignore = true` sections say what a shfmt directory walk would skip), the
shebangs themselves, which decide each script's dialect, the CI steps and
`.pre-commit-config.yaml` hooks that run shellcheck, shfmt, or hadolint
(and their flags), `.hadolint.yaml`, and the Bats test layout if there is
one.

The oldest shell the scripts must run on bounds what may be proposed:
`/bin/sh` is dash on Debian and Ubuntu and BusyBox ash on Alpine, and
macOS ships Bash 3.2, which has no associative arrays, no `mapfile`, and
no `${var,,}`.

## Tools

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Lint: idioms, bugs, portability | `shellcheck` | static with `--norc` | `shellcheck --norc -P SCRIPTDIR -P <absolute path of the repository root> --severity=style --format=gcc <files>`, with the files each script sources listed alongside it (`SCRIPTDIR` resolves `. "$(dirname "$0")/lib.sh"`, the repository root resolves `. scripts/lib.sh`; shellcheck still reads only the listed files); pass each `source-path=` from `.shellcheckrc` as a further `-P`, made absolute against the repository root; add `--enable=all` to see the optional checks |
| Shell in GitHub Actions `run:` steps | `actionlint`, your empty configuration | static | from the scratch directory, `actionlint -config-file <scratch>/actionlint.yaml -shellcheck <absolute path of the shellcheck the lint row ran> -oneline -verbose <checkout>/.github/workflows/*.y*ml`; the repository's own `.github/actionlint.yaml` is parsed but not applied, and if it is malformed the run stops with exit status 3: then lint copies, and note that the local-action and reusable-workflow checks did not run |
| Shell in Dockerfile `RUN` lines | `hadolint`, your configuration | static | `hadolint --config <scratch>/hadolint.yaml <Dockerfiles>`, the file holding `ignored: []` (an empty one is rejected) |
| Other embedded shell | `shellcheck` on extracted copies | static | copy composite-action `run:` steps (actionlint does not lint action files; replace each `${{ … }}` with a placeholder such as `_`, as actionlint does, or shellcheck reports `SC2296` for them), Makefile recipes (with `$$` turned back into `$`), and Singularity/Apptainer `%post`, `%test`, and `%runscript` sections into scratch files and run the static shellcheck command with `--shell=sh` (or `bash` where the runner, the step's `shell:`, a `%post -c`, or the section's `#!` line uses it); or read them by hand and say so in Method & limits |
| Formatting | `shfmt` | static on an explicit file list with explicit flags (any formatting flag makes it skip the formatting properties of `.editorconfig`, but a directory walk still skips files an `ignore = true` section matches) | `shfmt -d <flags> <files>`, listing the files (never a directory), prints the diff; never `-w`; `<flags>` translates the shfmt properties that apply to each file, merged from every matching section (including `[*]` and shfmt's `[[shell]]` / `[[bash]]`) of every `.editorconfig` up to the one with `root = true`: `indent_style = space` to `-i <indent_size, or 8>`, any other `indent_style` to `-i 0`, `binary_next_line` to `-bn`, `switch_case_indent` to `-ci`, `space_redirects` to `-sr`, `keep_padding` to `-kp`, `function_next_line` to `-fn`, `simplify` to `-s`, `minify` to `-mn`, `shell_variant` to `-ln`; run files with different properties separately, or copy the flags the project's CI or pre-commit hook passes |
| Source and call graph | `grep` | static | the source grep below; search scripts, workflows, Makefiles, and Dockerfiles for what runs each script |
| Dead code | none dedicated | static | list function definitions with the function grep below and search for their callers; list scripts and search for what runs them; shellcheck `SC2034` flags unused variables |
| Complexity | none dedicated | static | script and function length (`wc -l`), nesting depth by reading |
| Tests | `bats` | consent | see Verification |

The two greps:

```sh
# files each script sources, guarded ones included ([ -f x ] && . x)
grep -rnE '(^|[;&|({]|\b(then|do|else))[[:space:]]*((command|builtin)[[:space:]]+)?(\.|source)[[:space:]]' <files>
# function definitions, including `function name {` and names like log::info
grep -nE '^[[:space:]]*(function[[:space:]]+[^[:space:](){]+|[A-Za-z_][A-Za-z0-9_:.-]*[[:space:]]*\(\))' <files>
```

With `--norc`, shellcheck ignores `.shellcheckrc` (its `disable=`,
`enable=`, `shell=`, `source-path=`, and `external-sources=`); inline
`# shellcheck` directives still apply. Do not pass its `shell=` as
`--shell=`: that overrides every shebang and hides the `SC3xxx` hits the
Dialect check needs; rerun only the files without a shebang (reported as
`SC2148`) with `--shell=<value>`.

actionlint skips every `run:` script without a word when its
`-shellcheck` path is empty or names no executable —
`"$(command -v shellcheck)"` is empty when shellcheck is not on `PATH` —
and its exit status then covers only its own checks. A
`Rule "shellcheck" was disabled` line in the `-verbose` output means this
sweep did not run: record it in Method & limits as not run, never as
clean.

## Checks

- **One source of truth** (`ARC`): versions, paths, URLs, and tool flags
  hard-coded in several scripts or workflow steps; read them from one
  file, or from the project's own metadata.
- **Closed sets** (`ARC`): allowed values repeated in `case` patterns,
  `usage()` text, and workflow `choice` options become one list (a
  variable or array in a sourced file) that both the validation and the
  usage text read. Changing which values are accepted is `NV`.
- **Copied snippets** (`DUP`): the same install, retry, or
  version-detection block in several scripts or workflow `run:` steps
  becomes one script, a sourced function, or a composite action. The
  merged code must run under the options each copy ran under. A workflow
  `run:` step runs under its own `shell:`, else the job's or the
  workflow's `defaults.run.shell`, else `bash -e {0}` on Linux and macOS
  runners (`sh -e {0}` where there is no bash), and `shell: bash` means
  `bash --noprofile --norc -eo pipefail {0}`. A composite action ignores
  those defaults: each of its `run:` steps names its `shell:`. A script
  run as `./x.sh` gets none of these options unless it sets them, and a
  sourced function runs under its caller's. If the copies ran under
  different options, the merge is `NV`: name the commands whose failure
  would then stop, or no longer stop, the step. Test runs exercise the
  success path, which looks the same either way, so compare the options
  themselves.
- **Scripts that outgrew shell** (`ARC`): long scripts with data
  structures, parsing, or JSON handling are clearer and testable in the
  project's main language. A rewrite is `NV` when other people or
  systems run the script.
- **Legacy syntax** (`CL`, except where noted): `$[ ]` arithmetic
  (`SC2007`), and backticks (`SC2006`) rewritten the way `shfmt -d`
  rewrites them, which removes one level of backslash escaping inside; a
  verbatim copy, which is what shellcheck's own fix does, changes `\\`,
  `\$`, and `\"` and breaks nested backticks. `echo $(cmd)` and
  `echo "$(cmd)"` (`SC2005`) are `NV`: dropping the `echo` keeps the
  command's own trailing newlines or their absence, stops dash's `echo`
  from interpreting backslashes, and returns the command's exit status
  where `echo` returned 0 (under `set -e` the script then stops). `expr`
  arithmetic (`SC2003`) is `NV` unless every operand is always a decimal
  integer with no leading zero that fits in 64 bits and nothing uses
  `expr`'s exit status: under `$(( ))`, `08` is an error that ends a dash
  script and `010` is 8, while `expr` exits 1 on a zero result, which
  stops a `set -e` script. `bash -n` and shellcheck cannot see these
  changes; run before and after on representative inputs.
- **Strict mode** (`NV`): scripts without `set -e`, `set -u`, or
  `set -o pipefail` where the project's other scripts use them. Adding
  them changes which failures stop the script; name the commands that
  would then abort. In a `#!/bin/sh` script, `set -o pipefail` is a
  dialect change (`SC3040`): dash rejects it and exits, so propose it
  only for Bash scripts, or where every `/bin/sh` the script must run on
  supports it.
- **Quoting** (`NV` unless the value is never empty and can never contain
  whitespace, glob characters, or a character the script puts in `IFS`):
  unquoted expansions (`SC2086`, `SC2046`), and loops over `$(ls …)` or
  `$(find …)` output (`SC2045`, `SC2044`). An empty unquoted expansion
  disappears while `"$var"` passes an empty argument (`rm "$verbose" f`
  fails when `verbose` is empty), and a glob that replaces `$(ls …)`
  stays literal when nothing matches. For a flag that is empty or one
  such word, `${var:+"$var"}` keeps the arguments as they were (`CL`),
  unless `set -u` is on and the variable can be unset: there `$var`
  aborts and `${var:+…}` does not.
- **Dialect** (`NV`): Bash features in a `#!/bin/sh` script (`[[ ]]`,
  arrays, `source`; shellcheck's `SC3xxx` checks). Either the shebang
  changes to Bash, which changes the interpreter, or the syntax becomes
  POSIX.
- **Unchecked `cd`** (`SC2164`), and temporary files created without
  `mktemp` or removed without a `trap` (`NV`).
- **Executable bit and shebang** (`CL`): a script with a shebang that is
  not executable, or run as `bash script.sh` despite one. Changing how it
  is invoked is `NV`.
- **Public surface and deprecation** (`NV` to change): a script's
  options, arguments, the environment variables it reads, its exit
  statuses, and the output other scripts or CI parse are its interface,
  as are the functions of a library that other scripts source. To retire
  an option or variable, keep accepting it, print a one-line warning
  naming the replacement to standard error
  (`echo "--old is deprecated; use --new" >&2`), and keep it in the
  usage text until it is removed.
- **Currency** (`CL`, or `NV` where behavior changes): obsolete commands —
  `egrep` and `fgrep` (obsolescent: upstream GNU grep 3.8 and later
  warns; use `grep -E` and `grep -F`), `which` (use `command -v`) — and
  shellcheck, shfmt, or hadolint versions pinned in CI or pre-commit far
  behind their latest releases, which miss newer checks. Compare the pins
  with https://github.com/koalaman/shellcheck/releases,
  https://github.com/mvdan/sh/releases, and
  https://github.com/hadolint/hadolint/releases.

## Not findings

- Functions called indirectly: through a variable (`"$cmd" "$@"`
  dispatch), from a `trap`, as completion functions (`complete -F`), or by
  the scripts and interactive shells that `source` the file. A library
  file has no callers of its own.
- Bats hooks, which the runner calls by name: `setup`, `teardown`,
  `setup_file`, `teardown_file`, `setup_suite`, `teardown_suite`.
- Scripts run from outside the repository: commands the documentation
  gives users, cron jobs and systemd units, container `ENTRYPOINT`s, git
  hooks (`.githooks/`), and CI in other repositories.
- Variables set for a script that sources this one, assigned under
  `set -a`, or read indirectly (`${!name}`, `eval`, `declare -n`):
  `SC2034` reports them as unused, and a search for the name finds no
  reader.
- Deliberate word splitting, such as `$opts` holding several flags, marked
  with `# shellcheck disable=SC2086` and a reason.
- Syntax specific to a shell, in a script whose shebang asks for that
  shell.

## Verification

- **Static, after any edit**: `bash -n <file>` (or `sh -n` for POSIX
  scripts) parses without running anything; rerun the static shellcheck
  command and compare its hits with the earlier run.
- **Baseline and after each group** (consent, in the throwaway checkout):
  the project's Bats suite (`bats test/`), or the workflow step or
  Makefile target that runs the script.
- **Scripts with effects** (consent): run the script before and after the
  change, in a scratch directory on the same inputs, traced with the
  interpreter and the options its shebang line names plus `-x` (`sh -ex`
  for `#!/bin/sh -e`, `sh -x` for `#!/bin/sh`, `bash -x` for Bash; plain
  `sh -x script` drops the shebang's options), and compare outputs, exit
  statuses, and the files written.
