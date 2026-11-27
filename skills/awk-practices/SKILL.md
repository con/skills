---
name: awk-practices
description: AWK practices for awk in shell scripts, Makefiles, CI steps, and container recipes, under gawk, mawk, the one-true-awk, and BusyBox awk — the house's preferences (portable awk unless every caller runs gawk, values passed with -v or ENVIRON rather than spliced into the program, one lookup array for a closed set, locals as extra parameters, explicit string or numeric comparison, quoted values in commands built from data), public surface and deprecation, false positives, and verification, with the review tools and detailed checks in references/review.md. Use when writing, changing, or reviewing awk programs, including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# AWK practices

The house's practices for awk programs, for three kinds of work: writing
or changing it, reviewing a pull request, and the code-quality reviews.
Read `general-practices` first: it says how to weigh these preferences
against the project's own rules and your own judgment, and defines the
marks and categories used here.
[references/review.md](references/review.md) holds what a review needs
beyond them: the tools with their **static** / **consent** marks, the
detailed checks with their categories and pitfalls, currency sources, and
verification commands.

It is written for awk one-liners and short programs in shell scripts,
Makefiles, GitHub Actions steps, and container recipes, and the
occasional `.awk` file, that process text and logs under gawk, mawk
(Debian and Ubuntu containers), the one-true-awk (macOS), and BusyBox
awk (Alpine). gawk's less common extensions appear only where they bear
on safety or portability: check the gawk manual before reporting on a
program built around them.

## Recognize

`*.awk` and `*.gawk` files, and scripts without an extension whose shebang
runs an awk (`#!/usr/bin/awk -f`, `#!/usr/bin/env -S gawk -f`, and the
broken `env` forms under Preferences). Also programs embedded elsewhere, even
in a repository with no awk file: the program operand of an `awk`, `gawk`,
`mawk`, `nawk`, or `$(AWK)` command in shell scripts, Makefile recipes,
`run:` steps of GitHub Actions workflows and composite actions,
Dockerfile `RUN` lines, and the `%post`, `%test`, and `%runscript`
sections of Singularity/Apptainer recipes. Out of scope: generated
programs, and templates a build fills in.

`shell-practices` reviews the command around an embedded
program; this guide reviews the program text against the awk the command
names, and how values reach it: `-v`, operands, `ENVIRON`, or text the
shell splices in.

## Project rules

Find which awks run each program: its shebang, the command every caller
uses (scripts, Makefiles, CI and its images, documentation), and the
options and environment they set (`--posix`, `--csv`, `AWKPATH`, the
locale). A program every caller runs with gawk may use gawk; one run as
`awk` may use only what every target implements.

## Preferences

- **Portable unless every caller runs gawk**: plain `awk` is mawk in
  Debian and Ubuntu images but gawk on GitHub's Ubuntu runners, so CI
  that tests only gawk tests none of the others; mawk and the one-true-awk
  silently take gawk's `IGNORECASE` or `FPAT` as ordinary variables.
- **Shebangs**: `#!/usr/bin/awk -f` or `#!/usr/bin/env -S gawk -f` (not
  with BusyBox's `env`); `#!/usr/bin/env gawk -f` fails on Linux.
- **Values as data**: shell values reach the program by `-v`, a `name=…`
  operand, or `ENVIRON`, never spliced in (`awk "/$pat/"`), where a
  crafted value runs `system()`.
- **A closed set is one lookup array**: three or more
  `$3 == "red" || …` become an array filled once in `BEGIN`, tested with
  `$3 in COLORS` (not `COLORS[$3]`, which adds the key), and shared
  through one `-f` file or `-v` value.
- **Copies become one file**: a one-liner or function copied between
  programs becomes a `.awk` file run with `-f`, keeping each copy's `-F`,
  `-v`, locale, and awk.
- **Locals as extra parameters** (`function f(line,    n, i)`): any other
  variable a function uses is global and can clobber the caller's.
- **Say string or number**: fields, `getline` input, `split()` pieces,
  and `-v` and `ENVIRON` values compare as numbers when they look
  numeric; `x + 0` or `x ""` states the intent.
- **`FS = ","` is not CSV**: quoted commas split, and `--csv` is only in
  gawk 5.3+ and the one-true-awk's second edition.
- **Commands built from data** go to `sh -c`: prefer awk's own functions
  to `system()` and command pipes, else quote each value
  (`gsub(/'/, "'\"'\"'", s)`, then `"'" s "'"`).
- **Literal formats, checked reads**: `printf "%s", x`, not `printf x`
  (`%` in data stops mawk and the one-true-awk), and `getline` compared
  with `> 0`, since it returns -1 when a file cannot be opened.

## Public surface and deprecation

- A program's `-v` variables, the input fields and separators it
  expects, and its output format are what callers and downstream steps
  depend on; changing any of them is `NV`. To retire a variable, keep
  accepting it and print a warning to standard error
  (`print "…" > "/dev/stderr"`, a file Linux and macOS provide).

## Not findings

gawk features in a program every caller runs with gawk; idioms such as
`!seen[$0]++`, `NR == FNR { …; next }` (unless the first file can be
empty), `$1 = $1`, and counters that start unassigned (`count[$1]++`);
variables set from outside (`-v`, `ENVIRON`) or assigned for their effect
(`FS`, `OFS`); functions other programs load; and templates such as
`*.awk.in`. The full list is in [references/review.md](references/review.md).

## Verification

Run the project's own tests; else run each program, before and after, on
the same inputs under each awk it must support, and compare outputs, files
written, and exit statuses (add empty input, `0.0`, `%`, and non-ASCII
text). The review's commands are in
[references/review.md](references/review.md).
