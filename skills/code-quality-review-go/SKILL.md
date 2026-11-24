---
name: code-quality-review-go
version: 0.1.0
description: Go guide for the code-quality review skills — where a Go module states its rules, which tools sweep it (gofmt and gocyclo are static; vet, staticcheck, deadcode and golangci-lint need execution consent because they load and build the module), Go checks such as typed constants for closed sets, error wrapping and interface placement, false positives such as exported API, build tags and implicit interface methods, and the commands that verify a change. review-repo-code-quality reads it for Go code, and review-org-code-quality uses its static tools. Use when a review skill tells you to read it, or when asked for a code-quality review of Go code (then run review-repo-code-quality, which loads this guide).
allowed-tools: Read, Skill
user-invocable: true
---

# Go guide for the code-quality reviews

`review-repo-code-quality` holds the review procedure, the report layout,
and the architecture principles that apply to every language; this guide
adds what holds for Go only. That skill reads it in Step 1 for every
repository with Go code in scope, and `review-org-code-quality` uses its
**static** tools in Phase 2. The category prefixes (`ARC`, `DC`, `DUP`,
`CON`, `CL`, `NV`) and the **static** / **consent** marks are defined in
`review-repo-code-quality`.

## When invoked directly

This guide is not a review on its own. Asked for a Go code-quality
review, or for this guide by name, run `review-repo-code-quality` (with
`Skill`, or by reading `../review-repo-code-quality/SKILL.md`); its Step 1
loads this guide. Limit that review to the Go code only when the user
asked for that; otherwise it covers every language in the repository,
each with its own guide. If `review-repo-code-quality` is not installed,
stop and ask the user to install it; do not review from this guide alone.

## Recognize

`*.go` files, with `go.mod`, `go.sum`, and `go.work`. Out of scope:
generated files (a first line matching `// Code generated … DO NOT EDIT.`),
`vendor/`, and the fixtures in `testdata/`.

## Project rules

Read `go.mod` (the `module` path; the `go` line, which is the minimum
language version; `toolchain`; `require`, `replace`, `exclude`, `retract`;
`tool` directives), `go.work`, the golangci-lint configuration
(`.golangci.yml`, `.golangci.yaml`, `.golangci.toml`, `.golangci.json`;
version 2 files start with `version: "2"` and differ from version 1),
`staticcheck.conf`, the task runner (`Makefile`, `Taskfile.yml`,
`magefile.go`), `.goreleaser.yaml`, `//go:generate` lines, and build
constraints (`//go:build` lines, and `_<os>` / `_<arch>` file-name
suffixes). `magefile.go` is code: read it as text.

The `go` line bounds what may be proposed: generics need 1.18; the `min`
and `max` built-ins and the `slices`, `maps`, and `log/slog` packages
need 1.21; per-iteration loop variables and `range` over an integer need
1.22; range-over-func iterators need 1.23; `tool` directives need 1.24.

## Tools

Anything that loads packages — `go vet`, `go list`, `staticcheck`,
`deadcode`, `golangci-lint`, `govulncheck`, `go test` — fetches the
module's dependencies over the network and runs cgo preprocessing, and
the `go` command switches to, and if needed downloads, the toolchain that
`go.mod` asks for. All of them need consent. Run them from the checkout
with `GOFLAGS=-mod=readonly`, so that `go.mod` and `go.sum` stay
unchanged, and `GOTOOLCHAIN=local`, so that a newer `go` line fails
instead of downloading a toolchain (ask before allowing that download).

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Formatting and simplifications | `gofmt` | static | `gofmt -s -l <paths>` lists the files; `-d` prints the diff |
| Complexity | `gocyclo` | static | `gocyclo -over 15 <paths>`, or `-top 20` |
| Dead code: unused unexported code | `staticcheck` (`U1000`) | consent | `staticcheck -checks U1000 ./...` |
| Dead code: unreachable from `main` | `deadcode` | consent | `deadcode -test ./...` |
| Idiom drift | `go vet`, `staticcheck` | consent | `go vet ./...`; `staticcheck ./...` |
| Idiom drift | the project's golangci-lint, plus `unparam`, `dupl`, `goconst`, `gocognit`, `exhaustive`, `errorlint`, `copyloopvar`, `revive` | consent | the project's configuration with those linters enabled; the flags differ between golangci-lint versions 1 and 2 |
| Import graph | `go list` | consent | `go list -f '{{.ImportPath}}: {{join .Imports " "}}' ./...` |
| Modules | `go mod tidy -diff` (Go 1.23 or later) | consent | prints what `go mod tidy` would change, without writing |
| Vulnerabilities | `govulncheck` | consent | `govulncheck ./...`; its findings are security-sensitive (conventions §2) |
| Tests | `go test` | consent | see Verification |

Without consent, the sweep is `gofmt`, `gocyclo`, jscpd, and plain
searches; say so in Method & limits.

## Checks

Each check names the category it usually lands in. A fix that would
change behavior goes under `NV` instead, with the change spelled out.

**Closed sets and constants**

- **A closed set spelled as untyped constants or repeated literals
  becomes a named type** (`ARC`; `CON` when it stays inside one package).
  Related string or integer constants without a type, or the same values
  written as literals across packages and in validating `switch`
  statements, become one type with typed constants
  (`type Mode string` with `const ( ModeFast Mode = "fast"; … )`), or an
  `iota` integer type with a `String` method that `stringer` generates;
  the `exhaustive` linter then checks every `switch` over it. Changing the
  type of an exported constant or parameter is an API change for
  importers (`NV` in a library), and adding `String`, `MarshalText`, or
  `MarshalJSON` changes formatting and encoding.
- **The same literal in several places** (`CON`; `goconst` finds them):
  one named constant.

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
- hand-written `contains`, `min`, `max`, sorting, and map-key helpers
  that `slices`, `maps`, and the built-ins replace (1.21 or later);
- functions copied once per type that generics can merge (1.18 or later)
  — `CON`;
- names against Go conventions: package-name stutter
  (`config.ConfigLoader`), `Get` prefixes on getters, `Id` for `ID`.
  Renaming an exported name is an API change (`NV` in a library);
- goroutines that nothing can stop or wait for (`NV`).

**Modules** (`DC`, `CON`)

- `replace` directives left in a module that others import, requirements
  that `go mod tidy -diff` would drop, and a `tools.go` file of blank
  imports kept after the `go` line allows `tool` directives.

## Not findings

What looks dead or wrong in Go but is not. List the ones you checked
under "Not changed (deliberately)".

- Exported identifiers in a module that others import: having no caller
  inside the repository does not make them dead. `deadcode` reports them
  and `U1000` does not; removing one is `NV`.
- Code behind build constraints (`//go:build`, `_linux.go`,
  `_windows.go`, an `integration` tag): analyze with the tags CI uses.
- Methods that satisfy an interface implicitly (`String`, `Error`,
  `MarshalJSON`, `ServeHTTP`, `sort.Interface`), functions passed as
  values, and struct fields used only through reflection (`encoding/json`
  tags, ORM mappings).
- `init` functions; blank imports kept for their side effects
  (`import _ "…"`: database drivers, `embed`, `net/http/pprof`);
  `//go:embed` variables; `//go:linkname` and cgo `//export` functions.
- `TestMain`, `Example…` functions (documentation, and tests when they
  carry an `// Output:` comment), helpers in `_test.go` files, and
  `testdata/`.
- Generated code: change the generator, not its output.

## Verification

- **Baseline and after each group** (consent, with the environment from
  Tools): the project's entry point (a Makefile target, the CI step),
  else `go build ./... && go vet ./... && go test ./...` with the flags
  and build tags CI uses (`-race`, `-tags integration`, …); `-count=1`
  skips the test cache.
- **Static, after any edit**: `gofmt -s -l` on the changed files prints
  nothing.
- **Modules** (consent): `go mod tidy -diff` prints nothing.
- **Public API** (consent): `gorelease -base=<last release>` or `apidiff`
  (both from `golang.org/x/exp/cmd`) lists incompatible changes.
