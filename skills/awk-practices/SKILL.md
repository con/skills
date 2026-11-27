---
name: awk-practices
description: AWK practices — the POSIX awk and gawk programs it covers (including programs embedded in shell scripts, Makefiles, and CI steps) and their portability to mawk, BusyBox awk, and the one-true-awk, its review tools and which need execution consent, awk checks such as a lookup array for a closed set of values, gawk features under a POSIX shebang, string and numeric comparison, and commands built from data, currency (gawk 5.4, POSIX.1-2024), false positives, and verification commands. Use when writing, changing, or reviewing awk programs, including in a pull-request review or a code-quality review (review-repo-code-quality and review-org-code-quality read it).
allowed-tools: Read
user-invocable: false
---

# AWK practices

What holds for awk programs only, for three kinds of work: writing or
changing it, reviewing a pull request, and the code-quality reviews
(`review-repo-code-quality` reads this guide in Step 1;
`review-org-code-quality` runs its **static** tools). When writing code,
follow Project rules and Checks and leave Not findings alone; when
reviewing, report against them. The procedure, the architecture
principles, the category prefixes (`ARC`, `DC`, `DUP`, `CON`, `CL`, `NV`),
and the **static** / **consent** marks on the Tools are defined in
`review-repo-code-quality`.

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
broken `env` forms under Checks). Also programs embedded elsewhere, even
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

Find which awks run each program; they bound what may be proposed.

- The shebang, and the command every caller uses (scripts, Makefiles, CI,
  documentation). Plain `awk` differs by system: Debian's and Ubuntu's
  container images have only mawk, but an installed gawk takes over
  `awk`, and GitHub's Ubuntu runners include gawk. Alpine's `awk` is
  BusyBox's; macOS has the one-true-awk (Apple's latest published source,
  awk-40, is its version 20200816, older than the second edition, which
  added `--csv` and UTF-8 in September 2023).
- What the project states: the README, a package dependency on gawk, the
  gawk options callers pass (`--posix`, `--csv`), the CI images and any
  step installing an awk, and the environment callers set: `AWKPATH` and
  `AWKLIBPATH` (where `@include` and `@load` look), the locale, and
  `GAWK_GNU_MATCHERS`. A program every caller runs with gawk may use
  gawk; one run as `awk` may use only what every target implements.

## Tools

With `--pretty-print` gawk parses and prints a program and runs nothing:
no `BEGIN` or `END` rule, `system()`, or command pipe ran, and an `@load`
extension was not even opened. Its lint is **static** without `--profile`,
which runs the program, or `--debug`, which loads extensions and runs the
commands in a `./.gawkrc` (one holding `run` ran the program; gawk reads
no other configuration); with output files named, as the defaults
(`awkprof.out`, `awkvars.out`) land in the working directory; and without
`POSIXLY_CORRECT`, which turns on `--posix`, or `GAWK_PERSIST_FILE`, which
makes even a parse-only run write its heap file. Includes: a name without
a `/` is looked up in each `AWKPATH` directory (also with `.awk`
appended), and in the working directory only when `AWKPATH` is unset or
empty or lists `.` or an empty entry; a name with a `/` opens relative to
the working directory. So set `AWKPATH` as the callers do, absolute, with
their working directory for `.`, and link the first directory of each name
with a `/` into the scratch directory (`ln -s <checkout>/lib <scratch>`).

```sh
# every tracked regular file in <scope> (review-repo-code-quality Step 1) named *.awk or *.gawk or with an awk shebang (a symlink to /dev/zero hangs gawk)
git -C <checkout> ls-files -z --format='%(objectmode) <checkout>/%(path)' -- <scope> |
  gawk 'BEGIN { RS = ORS = "\0" } sub(/^100(644|755) /, "")' |
  xargs -0 -r env -u POSIXLY_CORRECT -u GAWK_PERSIST_FILE LC_ALL=C gawk 'BEGINFILE { if (ERRNO != "") {
    print FILENAME ": " ERRNO > "/dev/stderr"; nextfile } } FNR == 1 { if (FILENAME ~ /\.g?awk$/ ||
    /^#!.*[\/ ]([gmn]?awk|original-awk)( |$)/) printf "%s\0", FILENAME; nextfile }' \
  > <scratch>/awk.list
# the lint row from the scratch directory, one program per run (-t names it)
xargs -0 -r -t -n 1 env -u POSIXLY_CORRECT -u GAWK_PERSIST_FILE AWKPATH=<dirs> \
  gawk --lint --pretty-print=/dev/null -f < <scratch>/awk.list
```

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Syntax, gawk-only features, unused and undefined functions | `gawk --lint`, parse only | static | the `xargs` command above, plus one run per composition the callers use (`-f lib.awk -f main.awk`), since several `-f` files make one program; after `cannot open source file` (an include not found) nothing further is checked. It reports gawk-only built-ins and keywords (`is a gawk extension`), functions `defined but never called directly` and `called but never defined`, and parameters that shadow a global (`shadows global variable`, a sign of accidental globals), but not gawk-only variables or `\|&`: the variable search below finds those. gawk 5.1.1 to 5.2.2 (Ubuntu 24.04 ships 5.2.1) print all of it, then end a program that has a binary `+` with `fatal: internal error: … Op_lint_plus`: ignore that line |
| Globals: accidental, misspelled, write-only | `gawk --dump-variables`, parse only | static | the same command with `gawk --pretty-print=/dev/null --dump-variables=/dev/stdout -f`: every global the program names, gawk's own with their defaults and the program's each an `untyped variable`, since nothing ran |
| Portability to POSIX awk and the one-true-awk | `gawk --posix --lint`, `gawk --traditional --lint`, parse only | static | the lint command with `--posix` or `--traditional` added: each stops at the first syntax it rejects (`--posix` also at `**` and `func`), and once parsing completes, gawk's built-ins appear as `called but never defined`. Both take `BEGINFILE` and gawk's variables as ordinary names, and before 5.4 `--posix` refuses `length(array)` only when it runs |
| Portability to mawk | `mawk -W dump` | static | `xargs -0 -r -t -n 1 mawk -W dump -f < <scratch>/awk.list > /dev/null` compiles each program, prints a listing, and exits without running it; it rejects `@include`, arrays of arrays, `**`, and `func`, and reports calls to functions mawk lacks (`function gensub never defined`). Like gawk's two modes, it takes `BEGINFILE` and gawk's variables as ordinary names |
| Portability to BusyBox awk and the one-true-awk | the implementation itself | consent | neither has a parse-only mode, and both report an undefined function only when the call runs: run the test inputs under them (Verification) |
| Embedded programs | `shfmt --to-json`, `jq` | static from the scratch directory (shfmt reads `.editorconfig` from the working directory up, even for standard input) | the extraction below (bash), then the rows above on the copies. It takes the program operand, or `-e` text, of an awk command (`awk`, `$AWK`, a path ending in `gawk`), also behind wrappers (`env`, `xargs`, `find … -exec`, `busybox`) and options such as `-F'\t'`, when it is one single-quoted word; it skips programs in double quotes, built from several quoted pieces (`'it'\''s'`), after a long option whose value is the next word (`--field-separator :`, `--assign x=1`), or fed through a heredoc: read those by hand. Copy Makefile recipes (`$$` turned back into `$`, `$(AWK)` written as `awk`), workflow and composite-action `run:` steps (each `${{ … }}` replaced by a placeholder), Dockerfile `RUN` lines, and Singularity/Apptainer `%post`, `%test`, and `%runscript` sections into a scratch `.sh` file first |
| Duplication | jscpd's `awk` format | static | the `analyze-duplicates` run reads only `*.awk` files as awk, and at its minimums it missed every copy of a five-line function (jscpd 5.4.3); add an awk-only run from the scratch directory, `xargs -0 -r -t <jscpd> --min-tokens 20 --min-lines 3 --formats-exts 'awk:awk,gawk' --formats-names 'awk:<names of the scripts without an extension>' --reporters console < <scratch>/awk.list` (one run, as `-t` shows), which found them all, read neither the project's `.jscpd.json` nor its `.gitignore`, and wrote nothing; one-liners need the search below |
| Import graph | `grep` | static | the include search below: `@include`, `@nsinclude`, `@load`, and `@namespace` lines, and the `-f` and `-i` files in each caller's command |
| Dead code | the lint row on each composition, then `grep` | static | a function a program never calls is a candidate until the definition search finds no caller anywhere (see Not findings); write-only globals from the globals row; rules after an unconditional `next` |
| Branches the tests never reach | `gawk --profile` | consent | `gawk --profile=<scratch>/prof.out -f <program> <inputs>`: statements and functions printed without a count did not run |
| Run-time lint | `gawk --lint`, running the program | consent | `gawk --lint -f <program> <inputs>` on the test inputs: `reference to uninitialized variable`, invalid `substr` indexes, and gawk-only settings as they are assigned (`IGNORECASE`, `FPAT`, a multi-character `RS`) |
| Complexity | none dedicated | static | function and rule length from the definition search, nesting by reading; lizard has no awk reader (it skips `.awk` files, and its C reader, given one by name, can lose functions) |
| Tests | the project's runner | consent | see Verification |

The extraction, one script at a time, and the searches (`<files>` is the
program list plus the copies, padded so lint line numbers match):

```sh
shfmt --to-json < <script> | jq -j '.. | objects | select(.Type? == "CallExpr") | .Args as $a
  | first(range($a | length) as $k | select($k == 0 or ($a[0].Parts[0].Value // "" | IN("command",
      "env", "exec", "find", "busybox", "xargs", "nice", "nohup", "sudo", "time", "timeout")))
    | select($a[$k].Parts[0] | if .Type == "DblQuoted" then .Parts[0] else . end
      | .Value // .Param.Value // "" | test("(^|/)([gmn]?awk|original-awk)$|^AWK$")) | $k) as $k
  | first(range($k + 1; $a | length) as $i | select($a[$i].Parts[0].Value // "" | test("^-.") | not)
    | select($a[$i - 1].Parts | length == 1 and (.[0].Value | IN("-F", "-v", "-f", "-W", "-i", "-l")) | not) | $i) as $p
  | select([$a[$k + 1:$p][] | .Parts[0].Value // ""] | any(test("^(-f|--file)")) | not)
  | $a[$p] | select((.Parts | length) == 1 and .Parts[0].Type == "SglQuoted")
  | "\(.Pos.Line).\(.Pos.Col)\u0000\(("\n" * (.Pos.Line - 1)) // "")\(.Parts[0].Value)\n\u0000"' |
while IFS= read -r -d '' pos && IFS= read -r -d '' prog; do printf '%s' "$prog" > "<scratch>/<name>.$pos.awk"; done
# function definitions (gawk namespaces included); then search everywhere for each name
grep -nE '^[[:space:]]*func(tion)?[[:space:]]+[A-Za-z_][A-Za-z0-9_:]*[[:space:]]*\(' <files>
# includes and extensions, and the -f / -i files that callers name
grep -nE '^[[:space:]]*@(include|nsinclude|load|namespace)[[:space:]]' <files>
git -C <checkout> grep -nE '(awk|AWK)\)?[^|;&]*[[:space:]](-f|-i|--file|--include)[[:space:]=]?[^[:space:]-]' -- <scope>
# gawk-only variables and two-way pipes
grep -nE '\b(IGNORECASE|FPAT|FIELDWIDTHS|PROCINFO|RT|BINMODE|ERRNO|ARGIND|LINT|TEXTDOMAIN|SYMTAB|FUNCTAB|PREC|ROUNDMODE)\b|\|&' <files>
# closed sets: three or more == "..." joined by ||, or != "..." joined by &&
grep -nE -e '(==[[:space:]]*"[^"]*"[[:space:]]*\|\|[^|]*){2,}==[[:space:]]*"' -e '(!=[[:space:]]*"[^"]*"[[:space:]]*&&[^&]*){2,}!=[[:space:]]*"' <files>
# commands run from the program, getline, and printf formats that are not literals
grep -nE '\bsystem[[:space:]]*\(|\bgetline\b|\bprintf?\b([^"#|]|"([^"\\]|\\.)*")*\|[^|]|\bprintf[[:space:]]*\(?[[:space:]]*[^"([:space:]]' <files>
grep -nE '[*+?}]\?' <files>   # regexes that POSIX.1-2024 shortest-match operators reinterpret
# one-line programs repeated across scripts, Makefiles, and workflows ($$ read as $)
git -C <checkout> grep -IhoiE "\b[gmn]?awk\b([[:space:]]+-[Fv][[:space:]]*'[^']*'|[^'|;&])*'[^']+'" -- <scope> |
  sed -E "s/.*'([^']+)'\$/\1/; s/\\$\\$/\$/g; s/[[:space:]]+/ /g" | sort | uniq -c | sort -rn
```

## Checks

"Observed": seen in gawk 5.2.1/5.3.2/5.4.2, mawk 20240123/20260302, the
one-true-awk 20231127/20251225, and BusyBox 1.36.1/1.37.0/1.38.0, alike
unless a version is named.

**Dialect and portability** (against the targets from Project rules;
`NV`: each fix changes the interpreter or what it ran)

- **gawk features under a POSIX or mawk shebang**: what the lint rows and
  the variable search report. mawk and the one-true-awk take gawk's
  variables (`IGNORECASE`, `FPAT`, `PROCINFO["sorted_in"]`, `RT`) as
  ordinary ones, BusyBox honors only `IGNORECASE` and `RT` of these, and
  the program silently does something else. `strftime`, `systime`, and
  `mktime` work in mawk and BusyBox, not the one-true-awk (observed).
- **Broken shebangs** (a direct run fails today): `#!/usr/bin/env gawk -f`
  hands `gawk -f` to `env` as one name (exit 127 on Linux), and
  `#!/usr/bin/env gawk` makes gawk parse the script's path as its
  program. `env -S` fixes both, except with BusyBox's `env`; an absolute
  path needs no `-S`.
- **Implementation differences** a program may rely on (observed): a field
  `0x10` is 16 in BusyBox and mawk 20240123, 0 in gawk, the one-true-awk,
  and mawk 20260302; under a UTF-8 locale `length("é")` is 1 in gawk and
  the one-true-awk, 2 in mawk and BusyBox, and only the first two upcase
  it; `-Ft` is a tab in the one-true-awk, a `t` elsewhere.

**One source of truth**

- **A closed set spelled as a chain of comparisons becomes one lookup
  array** (`ARC` when the set appears in several programs or callers;
  `CON` within one). Three or more `$3 == "red" || $3 == "green" || …`
  (or `!=` joined by `&&`), repeated in a regex, usage text, or another
  program, drift apart. Fill an array once in `BEGIN` and test with `in`;
  programs share it through one `-f` file, or one `-v` value split alike:

  ```awk
  BEGIN { n = split("red green blue", t, " "); for (i = 1; i <= n; i++) COLORS[t[i]] = 1 }
  $3 in COLORS { print $1 }
  ```

  Pitfalls, each observed: without its third argument `split()` splits on
  `FS`; a field holding `1.0` equals `1` but is not `in` an array keyed
  `1` (the constant `1.0` is: it converts to `"1"`); `($1 + 0) in S`
  matches it, and sends non-numeric values to `0`; under `IGNORECASE`
  (gawk, BusyBox), `==` ignores case and `in` does not (use
  `$3 ~ /^(red|green|blue)$/` there); `S[$3]` used as a test adds `$3` to
  the array; and `for (k in S)` has no defined order.
- **The same literal in several programs** (`ARC`; `CON` within one):
  separators, formats, paths, and thresholds become one variable in a
  shared `-f` file's `BEGIN`, or one `-v` from the caller.
- **Copied programs** (`DUP`): one one-liner in several scripts, recipes,
  and workflow steps, or one function copied between programs, becomes a
  `.awk` file run with `-f`, a library callers load first
  (`-f lib.awk -f main.awk`), or a shell function, keeping each copy's
  `-F`, `-v`, locale, and awk; a function defined twice is an error in all
  four.

**Variables, records, and comparisons**

- **Accidental globals** (`CL` when nothing else reads the name, else
  `NV`): a variable a function uses without listing it as an extra
  parameter is global, so a loop counter shared with the caller clobbers
  the caller's. The globals row lists them; move each after the extra
  spaces of the parameter list (`function count_fields(line,    n, i)`).
- **Uninitialized and write-only variables**: an unassigned variable is
  both `0` and `""` (observed), so a misspelled name fails silently
  (`NV`; the run-time lint names it). A global assigned and never read is
  `DC`, unless its assignment runs a command (`"date" | getline now`).
- **String or numeric comparison** (`NV` unless every input is traced):
  fields, `getline` input, `split()` pieces, `ARGV`, `ENVIRON`, and `-v`
  values compare as numbers when they look numeric, constants and string
  results as text (observed: `substr($1, 1) > 9` is false for `10`,
  `$1 == "10"` for `10.0`, and `!$1` is true for `0.0`); `x + 0` or `x ""`
  states the intent.
- **Field splitting** (`NV`): the default `FS = " "` splits on runs of
  blanks and trims; any other single character is literal (`-F.`,
  `-F'|'`), longer values are regexes. `FS = ","` breaks quoted CSV
  (`a,"b,c",d` gives 4 fields); `--csv` is in gawk 5.3+ and the
  one-true-awk's second edition, not mawk or BusyBox.
- **Records** (`NV`): assigning to a field or `NF` rebuilds `$0` with
  `OFS`; `RS = ""` and `RS = "\n\n"` split one input differently; a
  multi-character `RS` is a regex in all four, but only its first
  character counts under `gawk --posix` (and `--traditional` before 5.4).

**Input, output, and commands** (`NV` unless marked: these fixes change
behavior)

- **Values spliced into the program** by the shell (`awk "/$pat/"`): a `/`
  in the value is a syntax error in all four, and a crafted one ran
  `system()`. Pass it as `-v name=…` or a `name=…` operand, which turn
  `\t` into a tab, or in `ENVIRON`, which keeps it as is.
- **Commands built from data**: `system("echo " $4)`, and `cmd | getline`
  or `print | cmd` with `cmd` built from fields, hand them to `sh -c`, so
  a field such as `x; touch flag` runs `touch`. Prefer awk's own
  functions, or quote each value: `gsub(/'/, "'\"'\"'", s)`, then
  `"'" s "'"` (blocked it in all four), not the replacement `"'\\''"`,
  whose backslash BusyBox 1.37.0 and 1.38.0 drop (`a'b; touch flag; c'd`
  ran `touch`). Others' data makes it security-sensitive (conventions §2).
- **`printf` with data as its format**: only `%` matters (no awk
  interprets backslashes at run time): `100%` prints in gawk and BusyBox
  but stops mawk and the one-true-awk (observed); `printf "%s", x`
  changes only output holding `%`.
- **`getline` results**: 1, 0 at the end, -1 on error (a missing file, in
  all four), so `while (getline line < f)` never ends when `f` cannot be
  opened: compare with `> 0`. Only plain `getline` and `getline var`
  advance `NR` and `FNR` (gawk manual, Getline Summary; observed).
- **Unclosed pipes and files**: `cmd | getline` returns end of file when
  the command runs again until `close(cmd)`, but `close()` on a file
  written with `>` makes the next `>` truncate it (observed).
- **Dynamic regexes**: as a regex, `"a\.b"` is `a.b` in gawk (which warns
  `treated as plain`), the one-true-awk, and BusyBox, a literal dot in
  mawk; `/a\.b/` and `"a\\.b"` are a dot in all four. Data matched as a
  literal wants `index($0, pat)`, not `$0 ~ pat`.
- **Ambiguous redirections** (`CL`): `print "x" > "out" ".txt"`, which
  gawk's lint flags, writes `out.txt` in all four: parenthesize it.

**Public surface and deprecation**

- A program's `-v` variables, the input fields and separators it
  expects, and its output format are what callers and downstream steps
  depend on; changing any of them is `NV`. To retire a variable, keep
  accepting it and print a warning to standard error
  (`print "…" > "/dev/stderr"`, a file Linux and macOS provide).

**Currency** (reported as `review-repo-code-quality` Step 2 says; read the
live sources each item names)

- **Implementations.** Compare the versions CI installs or its images
  ship, and any the project documents, with the newest releases of gawk
  (https://ftp.gnu.org/gnu/gawk/, NEWS), mawk
  (https://invisible-island.net/mawk/CHANGES.html), the one-true-awk
  (https://github.com/onetrueawk/awk/blob/master/FIXES), and BusyBox
  (https://busybox.net/). Ubuntu 24.04 ships gawk 5.2.1, 26.04 gawk 5.3.2.
  From 20241212 mawk reads hex, inf, and NaN as numbers only with
  `--posix`.
- **gawk 5.4** (NEWS, README_d/README.matchers): the default matcher is
  MinRX (`GAWK_GNU_MATCHERS` selects the old ones, which "will eventually
  be removed"), with POSIX.1-2024's shortest-match operators:
  `sub(/x+?/, "X")` on `axxxb` gives `aXxxb` in gawk 5.4.2, `Xaxxxb`
  (`x+?` read as `(x+)?`) in the others and with `GAWK_GNU_MATCHERS` set,
  so each hit of that search is `NV`.
- **POSIX.1-2024**
  (https://pubs.opengroup.org/onlinepubs/9799919799/utilities/awk.html)
  adds `length(array)` and the shortest-match operators, and is the first
  edition with `fflush()`, `nextfile`, and `delete` of a whole array.
- **CI** (beside Step 2's actions and runner labels): the image decides
  which awk runs (Project rules); testing only gawk while callers say
  `awk` tests none of the others.

## Not findings

- awk in documentation, fixtures, and expected output, and templates such
  as `*.awk.in` (their `@PREFIX@` placeholders do not parse): review the
  template or generator instead.
- gawk features in a program every caller runs with gawk, by a `gawk`
  shebang or command (a broken `env` shebang is still a finding).
- Idioms: `!seen[$0]++`, `NR == FNR { …; next }` (a finding only if the
  first file can be empty: then the second file's lines all go to that
  block, observed), `$1 = $1` (rebuilds `$0`), `{ keys[$1] }`,
  `split("", a)` (empties an array), `exit` in `BEGIN` (`END` still runs,
  observed), extra parameters as locals (`function f(a,    i, tmp)`), and
  counters and accumulators that start unassigned (`n++`, `sum += $2`,
  `count[$1]++`), which the run-time lint reports as
  `reference to uninitialized variable` or `element`: only a name that
  neither the program nor its callers (`-v`, operands) assign is a finding.
- Variables set from outside (`-v`, `name=value` operands, `ENVIRON`), and
  special variables assigned for their effect (`FS`, `OFS`, `RS`, `OFMT`;
  in gawk `IGNORECASE`, `PROCINFO["sorted_in"]`): they look write-only.
- Functions other programs load (linted alone, a library reports each
  `defined but never called directly`), functions gawk reaches by name
  (`@name()` calls, comparators for `PROCINFO["sorted_in"]` or `asort()`;
  lint flags these too), and an `@load` extension's
  (`called but never defined` under `--pretty-print`, which skips it).

## Verification

- **Static, after any edit**: the lint row on the changed programs and
  compositions reports nothing new and no `cannot open source file`, and
  `mawk -W dump` still exits 0 for a mawk target; after a layout or
  comment edit, one gawk's `--pretty-print=<file>` output of the old and
  new program differs only in comments.
- **Baseline and after each group** (consent, in the throwaway checkout):
  the project's own tests (Bats, a Makefile target, the CI step); else the
  old and new program on the same inputs under every target awk, with the
  callers' `-F` and `-v` (`gawk --posix` checks a portable program stays
  so): the fixtures plus empty input, an empty first file, blank fields,
  `0`, `0.0`, `0x10`, `1e3`, `%`, and non-ASCII text, in each locale used.
  Each runs as `prog.awk` in its own directory, so diagnostics match and
  the files it writes are compared too (`<inputs>` as absolute paths):

  ```sh
  for a in gawk "gawk --posix" mawk original-awk "busybox awk"; do
    for v in old new; do rm -rf "<scratch>/$v" && mkdir "<scratch>/$v" && cp "<$v program>" "<scratch>/$v/prog.awk" &&
      (cd "<scratch>/$v" && $a -f prog.awk <inputs> > stdout 2> stderr; echo "exit $?" > status); done
    diff -r -x prog.awk "<scratch>/old" "<scratch>/new" || echo "^ $a"
  done
  ```
- **Embedded programs** (consent): run the script, step, or recipe as the
  shell guide says, or the extracted program with its command's options;
  `gawk --lint` on the same inputs reports no new run-time warnings.
