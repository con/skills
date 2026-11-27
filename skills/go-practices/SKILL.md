---
name: go-practices
description: Go practices — where a Go module states its rules, its review tools and which need execution consent (anything that loads packages does), Go checks such as typed constants for closed sets, error wrapping, and interface placement, currency, false positives, and verification commands. Use when writing, changing, or reviewing Go code, including in a pull-request review or a code-quality review (review-repo-code-quality and review-org-code-quality read it).
allowed-tools: Read
user-invocable: false
---

# Go practices

What holds for Go code only, for three kinds of work: writing or changing
it, reviewing a pull request, and the code-quality reviews
(`review-repo-code-quality` reads this guide in Step 1;
`review-org-code-quality` runs its **static** tools). When writing code,
follow Project rules and Checks and leave Not findings alone; when
reviewing, report against them. The procedure, the architecture
principles, the category prefixes (`ARC`, `DC`, `DUP`, `CON`, `CL`, `NV`),
and the **static** / **consent** marks on the Tools are defined in
`review-repo-code-quality`.

It is written for single-module command-line tools, small services, and
data-transfer utilities, built with the standard toolchain and tested with
`go test`. Protobuf and gRPC code generation, Kubernetes controllers,
cgo-heavy code, and multi-module workspaces are left out: check their
conventions before reporting there.

## Recognize

`*.go` files, with every `go.mod`, `go.sum`, and `go.work`. Out of scope:
`vendor/`, `testdata/`, and generated files — those with a line matching
`^// Code generated .* DO NOT EDIT\.$` before the `package` clause
(`git -C <checkout> grep -lE '^// Code generated .* DO NOT EDIT\.$' -- '*.go'`
lists them).

## Project rules

Read each `go.mod` (the `module` path, the `go` line, `toolchain`,
`require`, `replace`, and `tool` directives), `go.work`, the golangci-lint
configuration (`.golangci.yml`, `.yaml`, `.toml`, or `.json`; version 2
files start with `version: "2"` and differ from version 1),
`staticcheck.conf`, the task runner (`Makefile`, `Taskfile.yml`,
`magefile.go`), `.goreleaser.yaml`, `//go:generate` lines, and build
constraints (`//go:build` lines, and `_<os>` / `_<arch>` file-name
suffixes). `magefile.go` is code: read it as text.

The `go` line bounds what may be proposed; each check below names the
version its fix needs.

## Tools

Anything that loads packages — `go vet`, `go list`, `staticcheck`,
`deadcode`, `golangci-lint`, `govulncheck`, `go test` — fetches the
module's dependencies over the network unless the module is vendored,
and runs cgo preprocessing; and the `go` command switches to, and if
needed downloads, the toolchain that `go.mod` asks for. All of them need
consent. Run them from the checkout with `GOTOOLCHAIN=local`, so that a
newer `go` line fails instead of downloading a toolchain (a review never
allows that download). Leave `-mod` at its default: `readonly` without
a `vendor/` directory (`go.mod` and `go.sum` are not written), and
`vendor` with one.

`./...` stops at a nested `go.mod`, even under a `go.work`: run each
command once per module that `git ls-files '*go.mod'` lists outside
`vendor/` and `testdata/`, and name the modules in Method & limits.

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Formatting and simplifications | `gofmt` | static | `gofmt -s -l <paths>` lists the files; `-d` prints the diff |
| Complexity | `gocyclo` | static | `gocyclo -over 15 <paths>`, or `-top 20` |
| Dead code: unused unexported code | `staticcheck` (`U1000`) | consent | `staticcheck -checks U1000 ./...` |
| Dead code: unreachable from `main` | `deadcode` | consent | `deadcode -test ./...` |
| Idiom drift | `go vet`, `staticcheck` | consent | `go vet ./...`; `staticcheck ./...` |
| Idiom drift | the project's golangci-lint, plus `unparam`, `dupl`, `goconst`, `gocognit`, `exhaustive`, `errorlint`, `copyloopvar`, `revive` | consent | the project's configuration with those linters enabled and the output filters lifted (`--max-issues-per-linter=0 --max-same-issues=0 --uniq-by-line=false`), and with `--new=false`, `--new-from-rev=`, `--new-from-merge-base=`, or `--new-from-patch=` where the configuration limits the run to recent changes |
| Import graph | `go list` | consent | `go list -f '{{.ImportPath}}: {{join .Imports " "}}' ./...` |
| Import graph | the `import` blocks and `go.mod`, read as text | static | `grep -n` the `import` blocks of each package's files, with the module path from `go.mod` to tell internal imports from external ones |
| Modules | `go mod tidy -diff` (Go 1.23 or later) | consent | prints what `go mod tidy` would change, without writing |
| Vulnerabilities | `govulncheck` | consent | `govulncheck ./...`; its findings are security-sensitive (conventions §2) |
| Tests | `go test` | consent | see Verification |

`gocyclo` skips `vendor/` and `testdata/` but not generated files, and
`gofmt -l` walks all three: drop their hits in out-of-scope files, or
pass gocyclo `-ignore`.

## Checks

**Closed sets and constants**

- **A closed set spelled as untyped constants or repeated literals
  becomes a named type** (`ARC`; `CON` when it stays inside one package).
  Related string or integer constants without a type, or the same values
  written as literals across packages and in validating `switch`
  statements, become one type with typed constants
  (`type Mode string` with `const ( ModeFast Mode = "fast"; … )`); the
  `exhaustive` linter then checks every `switch` over it. Pitfalls:
  - A Go named type does not close the set: `Mode("x")` and untyped
    constants give any value. Keep the validation where values enter
    (parsing, decoding, flags); removing it is `NV`.
  - Typing the constants changes the dynamic type of every value that
    reaches an interface: an untyped constant becomes a `string` there,
    a typed one stays a `Mode` (as do retyped fields and variables).
    Comparisons with interface values (`raw["mode"] == ModeFast` on a
    `map[string]any` from JSON or YAML), `case string:` in type
    switches, `v.(string)` (which then panics), `reflect.DeepEqual`
    (testify's `assert.Equal`), and `%T` change silently; `%v`, `%s`,
    and `encoding/json` do not. Convert with `string(ModeFast)` at each
    such place as part of the change, or rate it `NV`.
  - Keep a string set a string type. An `iota` integer type, with a
    `String` method from `stringer`, suits values that are never persisted
    or sent; turning a string set into one changes its JSON and flag form
    (`NV`). `iota` values depend on position: append new members at the
    end, never reorder, and reserve the zero value for an unknown member.
  - Changing the type of an exported constant or parameter is an API
    change for importers (`NV` in a library), and adding `String`,
    `MarshalText`, or `MarshalJSON` changes formatting and encoding.
- **The same literal in several places** (`ARC` across packages, found
  by searching; `CON` within one package, where `goconst`, which checks
  one package at a time, finds it): one named constant.

**Packages and structure**

- Grab-bag packages (`util`, `common`, `helpers`) that everything imports
  (`ARC`): split them by what the code is about.
- Packages that importers should not use, kept outside `internal/`
  (`ARC`): moving one under `internal/` is an API change for a library
  (`NV`) and free for a program.
- Interfaces declared next to their only implementation, or exported only
  so that tests can mock them (`ARC`): Go interfaces belong with the
  consumer that needs them; functions return concrete types.
- `init` functions that do more than register — read the environment,
  touch files or the network, set global state (`ARC`): move the work to
  program setup in `main`.
- `context.Context` not passed as the first parameter, stored in a struct,
  or replaced by `context.Background()` deep in a call chain (`ARC`; `NV`
  when the fix changes cancellation).
- In a library, `apidiff` lists which of these fixes break the API, and
  `init` work moved into a setup call changes behavior for every importer
  that does not call it: `NV` unless the old forms stay as deprecated
  wrappers, or `init` keeps calling the setup.

**Errors**

- `%v` where `%w` was meant, `==` on errors that may be wrapped, and type
  assertions on errors instead of `errors.Is` / `errors.As` (`errorlint`)
  — `NV`: the fix changes what callers' error checks see.
- the same `if err != nil { return fmt.Errorf(…) }` context repeated with
  drifting messages — `CL` only where no caller or test matches the text.
- `panic` for a recoverable error in library code (`NV`).

**Idioms** (`CL`)

- `gofmt -s` simplifications, and `v := v` copies that per-iteration loop
  variables made unnecessary once the `go` line is 1.22 or later
  (`copyloopvar`);
- hand-written `contains`, `min`, `max`, and sorting helpers that `slices`
  and the built-ins replace (1.21 or later), and map-key helpers that
  `slices.Sorted(maps.Keys(m))` or `slices.Collect(maps.Keys(m))` replace
  (1.23 or later). `CL` only where the result cannot change, else `NV`:
  the built-in `min` and `max` return NaN when any operand is NaN and
  order -0 below 0, which a hand-written comparison does not;
  `slices.Sort` and `slices.SortFunc` are not stable
  (`slices.SortStableFunc` replaces a stable sort); and `slices.Collect`
  and `slices.Sorted` return nil for an empty map where a helper built
  with `make` returned an empty slice (`encoding/json` then writes `null`,
  not `[]`);
- functions copied once per type that generics can merge (1.18 or later)
  — `CON`;
- names against Go conventions: package-name stutter
  (`config.ConfigLoader`), `Get` prefixes on getters, `Id` for `ID`.
  Renaming an exported name is an API change (`NV` in a library), and in
  any module a rename is `NV` when something reaches the name at run
  time: an untagged field in `encoding/json` or `gob` output (the key
  changes), a template reference such as `{{.Id}}` (it fails when the
  template runs, not at build time), a reflection-based configuration
  mapping, or an interface assertion on the method name; search for each
  before rating a rename `CL`;
- goroutines that nothing can stop or wait for (`NV`).

**Modules**

- requirements that `go mod tidy -diff` would drop, and a `tools.go` file
  of blank imports kept after the `go` line reaches 1.24, which allows
  `tool` directives (`DC`, `CON`);
- `replace` directives left in a module that others import (`NV`):
  importers ignore them, but removing one changes which code this
  repository's own builds and tests use.

**Currency** (reported as `review-repo-code-quality` Step 2 says; read the
live sources each item names)

- **Go releases.** Each major Go release is supported until there are two
  newer major releases (https://go.dev/doc/devel/release). Report CI that
  tests no supported release, and a `toolchain` line pinned to an
  unsupported one. In a library, keep the `go` line as low as the code
  allows: raising it forces every importer to upgrade.
- **Deprecated APIs.** `staticcheck` check `SA1019` (consent) reports uses
  of deprecated identifiers. For the standard library it reports only
  those deprecated as of the module's `go` line, such as `io/ioutil` once
  the line is 1.19 or later; below that, search for such imports directly
  (their `io` and `os` replacements need 1.16).
- **Tool formats.** A golangci-lint configuration still in the version 1
  format (`golangci-lint migrate` converts it).

## Not findings

- Exported identifiers in a module that others import: having no caller
  inside the repository does not make them dead. `deadcode` reports them
  and `U1000` does not; removing one is `NV`.
- Code behind build constraints (`//go:build`, `_linux.go`, an
  `integration` tag): analyze with the tags CI uses.
- Methods that satisfy an interface implicitly (`String`, `Error`,
  `MarshalJSON`, `ServeHTTP`), functions passed as values, and struct
  fields used only through reflection (`encoding/json` tags, templates).
- `init` functions; blank imports kept for their side effects
  (`import _ "…"`: database drivers, `embed`, `net/http/pprof`);
  `//go:embed` variables.
- `TestMain`, `Example…` functions, and helpers in `_test.go` files.

## Verification

- **Baseline and after each group** (consent, with the environment from
  Tools, once per module): the project's entry point, else
  `go build -o /dev/null ./... && go vet ./... && go test ./...` with the
  flags and build tags CI uses (`-race`, `-tags integration`, …);
  `-o /dev/null` keeps a single `main` package from writing its binary
  into the checkout, and `-count=1` skips the test cache.
- **Static, after any edit**: `gofmt -s -l` on the changed files prints
  nothing.
- **Modules** (consent): `go mod tidy -diff` prints nothing.
- **Public API** (consent): `gorelease -base=<last release>` or `apidiff`
  lists incompatible changes.
