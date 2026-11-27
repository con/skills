---
name: haskell-practices
description: Haskell practices for large, long-lived applications built with cabal-install or Stack — the house's preferences (a closed set as a sum type deriving Enum and Bounded, newtypes, total functions, Text over String, strict accumulators and I/O, export lists and no orphan instances, a default-language in every component), public surface and deprecation, false positives, and verification, with the review tools and detailed checks in references/review.md. Use when writing, changing, or reviewing Haskell code, including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# Haskell practices

The house's practices for Haskell code, for three kinds of work: writing
or changing it, reviewing a pull request, and the code-quality reviews.
Read `general-practices` first: it says how to weigh these preferences
against the project's own rules and your own judgment, and defines the
marks and categories used here.
[references/review.md](references/review.md) holds what a review needs
beyond them: the tools with their **static** / **consent** marks, the
detailed checks with their categories and pitfalls, currency sources, and
verification commands.

It is written for one large, long-lived application built with cabal-install
(sometimes Stack), with a test suite, CPP for platform and feature flags,
and Template Haskell in places. Hackage publishing, Nix-based setups,
GHCJS, the JavaScript and WebAssembly backends, and Backpack are left out:
check their conventions before reporting there.

## Recognize

`*.hs`, `*.lhs`, `*.hs-boot`, and `*.hsc` files, with every `*.cabal`,
`package.yaml`, `cabal.project*`, and `stack.yaml`, and scripts without an
extension whose shebang runs `runghc`, `runhaskell`, `stack`, or `cabal`.
Out of scope: build output (`dist-newstyle/`, `.stack-work/`), vendored
packages, and Cabal's `Paths_<package>` and `PackageInfo_<package>` modules,
which a build generates. A `.cabal` file that says
`This file has been generated from package.yaml by hpack` is generated too:
changes go into `package.yaml`.

## Project rules

Read each `.cabal` file or `package.yaml` (`tested-with`, `default-language`,
`default-extensions`, `build-depends` bounds), `cabal.project*`, `stack.yaml`,
`.hlint.yaml`, the CI matrix, and `LANGUAGE` and `OPTIONS_GHC` pragmas. Each
component's `default-language` and the oldest supported compiler (lowest
`tested-with`, oldest in CI, `base` lower bound) bound what may be proposed:
no `GHC2024` before GHC 9.10, no strict `readFile'` before base 4.15.

## Preferences

- **Closed sets**: a closed set of strings becomes one sum type deriving
  `Enum` and `Bounded`, parsed once where values enter, rendered by one
  function, and matched by `case`, where `-Wincomplete-patterns` reports
  a missed constructor; `[minBound .. maxBound]` lists every value.
- **Derived instances**: `Show`, `Read`, and aeson's `Generic` instances
  use constructor names, and `Enum` and `Ord` follow declaration order:
  render and parse text that crosses a boundary explicitly, and append
  new constructors.
- **Newtypes**: a `newtype` with `deriving newtype` instances, not
  `type UserId = Int`, which mixes with any `Int`.
- **Total functions**: `NonEmpty`, `listToMaybe`, and `readMaybe` over
  `head`, `tail`, `!!`, `fromJust`, and `read`; no partial record fields,
  no `error` or `undefined` in library code, and no catch-all on
  `SomeException`, which also catches Control-C.
- **Text**: `Text` for text and `ByteString` for bytes, not `String`,
  converted at the edges with `encodeUtf8` and `decodeUtf8'`;
  `Data.ByteString.Char8.pack` keeps only each character's low eight bits.
- **Strictness**: `foldl'` and bangs on accumulator fields, not `foldl`,
  `modifyIORef`, or a lazy `Data.Map` updated in a loop, and the strict
  `readFile'` family over lazy I/O, which holds the handle until the text
  is consumed. Forcing earlier can raise an error laziness skipped.
- **Modules**: an export list on every module, test-only internals in an
  `Internal` module or a private sublibrary, no import cycles, no orphan
  instances, and no global state through `unsafePerformIO`.
- **Packages**: a `default-language` in every component (Cabal builds none
  as `Haskell98`; `GHC2024` for new code, though its `MonoLocalBinds` can
  break the build), shared settings in a `common` stanza, and upper bounds
  on `build-depends`.

## Public surface and deprecation

- **Internals**: names left out of export lists, and modules in
  `other-modules` rather than `exposed-modules`; a `….Internal` module a
  library exposes is documented as unstable.
- **Deprecating** an exported name or module: keep it and add
  `{-# DEPRECATED name "Use … instead" #-}` (for a module, after its
  name in the `module` line); GHC warns at each use (`-Wdeprecations`, on
  by default). Removal waits for a major version under the PVP (a change
  to `A.B` in `A.B.C`).
- **Breaking changes**: the Public API step under Verification in
  [references/review.md](references/review.md) lists them.

## Not findings

Exports of a library other packages depend on, instances used through
their class (`show`, aeson's generic encoding), names Template Haskell
creates (`makeLenses`), hspec-discover's `*Spec.hs` modules, CPP branches
for other compilers or platforms in the tested range, and `seq`, `$!`, or
bang patterns that look redundant. The full list is in
[references/review.md](references/review.md).

## Verification

Run the project's own entry point before and after a change (a CI step,
a Makefile target, else `cabal build all --enable-tests` and
`cabal test all`, or `stack test`), on the oldest and newest installed
`tested-with` compilers. A closed-set migration keeps the bytes at every
boundary. The review's commands are in
[references/review.md](references/review.md).
