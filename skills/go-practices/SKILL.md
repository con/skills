---
name: go-practices
description: Go practices for single-module command-line tools, small services, and data-transfer utilities — the house's preferences (typed constants for closed sets, errors wrapped with %w and checked with errors.Is and errors.As, interfaces declared by their consumer, no work in init, context.Context first, slices and maps over hand-written helpers, tidy modules), public surface and deprecation, false positives, and verification, with the review tools and detailed checks in references/review.md. Use when writing, changing, or reviewing Go code, including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# Go practices

The house's practices for Go code, for three kinds of work: writing or
changing it, reviewing a pull request, and the code-quality reviews. Read
`general-practices` first: it says how to weigh these preferences against
the project's own rules and your own judgment, and defines the marks and
categories used here. [references/review.md](references/review.md) holds
what a review needs beyond them: the tools with their **static** /
**consent** marks, the detailed checks with their categories and pitfalls,
currency sources, and verification commands.

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

Read each `go.mod` (the `go` line, `toolchain`, `replace`, and `tool`
directives), `go.work`, the golangci-lint configuration, the task runner
(`Makefile`, `Taskfile.yml`), and build constraints. The `go` line bounds
what may be proposed: generics from 1.18, `slices` and the built-in `min`
and `max` from 1.21, dropping `v := v` loop copies from 1.22,
`slices.Sorted(maps.Keys(m))` from 1.23, `tool` directives from 1.24.

## Preferences

- **Closed sets**: related untyped constants, or the same literals across
  packages, become one named type with typed constants
  (`type Mode string` with `const ( ModeFast Mode = "fast"; … )`), which
  `exhaustive` checks in every `switch`; a string set stays a string type.
- **A named type does not close the set**: `Mode("x")` gives any value, so
  validation stays where values enter. In an interface the value stays a
  `Mode`: comparisons with `map[string]any` values, `case string:`, and
  `v.(string)` change silently, so convert with `string(ModeFast)` there.
- **Errors**: wrapped with `%w` and checked with `errors.Is` /
  `errors.As`, not `==` or type assertions; no `panic` for a recoverable
  error in library code. A fix changes what callers' checks see.
- **Packages and interfaces**: no grab-bag `util` or `common` package;
  interfaces live with their consumer, not beside their only
  implementation; functions return concrete types.
- **`init` only registers**: reading the environment, file or network
  access, and global state belong in program setup in `main`.
- **Context and goroutines**: `context.Context` is the first parameter,
  not stored in a struct or replaced by `context.Background()` deep in a
  call chain; something can stop or wait for every goroutine.
- **Standard library over helpers**: `slices`, `maps`, the built-in `min`
  and `max`, and generics replace hand-written helpers, not always
  unchanged: the built-ins return NaN for a NaN operand, `slices.Sort` is
  not stable, and `slices.Sorted` returns nil for an empty map.
- **Names**: no package-name stutter (`config.ConfigLoader`), no `Get`
  prefix on getters, `ID` not `Id`; a rename also changes untagged
  `encoding/json` keys and breaks template references (`{{.Id}}`).
- **Modules**: `go mod tidy -diff` prints nothing, tools sit in `tool`
  directives rather than a `tools.go`, and a module others import has no
  `replace` directives: importers ignore them.
- **Go releases**: CI tests a supported release (one of the two newest),
  and a library keeps its `go` line as low as the code allows: raising it
  forces every importer to upgrade.

## Public surface and deprecation

- **Internals**: lowercase identifiers, and packages under `internal/`
  (references/review.md, Packages and structure).
- **Deprecating** an exported identifier: keep it, as a wrapper around
  its replacement if need be, and start a paragraph of its doc comment
  with `Deprecated: `, naming the replacement
  (https://go.dev/wiki/Deprecated); `staticcheck`'s `SA1019` (consent)
  reports uses. Removal waits for a new major version, which changes the
  module path (`/v2`).
- **Breaking changes**: the Public API step under Verification in
  [references/review.md](references/review.md) lists them.

## Not findings

Exported identifiers of a module that others import, even with no caller
in the repository; code behind build constraints (analyze with CI's
tags); methods that satisfy an interface implicitly (`String`, `Error`,
`MarshalJSON`); fields reached through reflection (`encoding/json` tags,
templates); blank imports for their side effects, `//go:embed` variables,
`init`, `TestMain`, and `Example…` functions. The full list is in
[references/review.md](references/review.md).

## Verification

Run the project's own entry point before and after a change (a `Makefile`
or `Taskfile.yml` target), else `go vet ./...` and `go test ./...` with
the build tags CI uses; after an edit, `gofmt -s -l` on the changed files
prints nothing. The review's commands are in
[references/review.md](references/review.md).
