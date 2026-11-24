---
name: code-quality-review-haskell
description: Haskell guide for review-repo-code-quality and review-org-code-quality — where a Cabal or Stack project states its rules, its review tools and which need execution consent, Haskell checks such as a closed set of strings that becomes a sum type deriving Enum and Bounded, partial functions, String and Text, orphan instances, and laziness, currency (GHC releases, GHC2024, Stackage, CI actions), false positives, and verification commands. Not invoked directly. Use when a review skill tells you to read it, or when asked what those reviews check for Haskell.
allowed-tools: Read
user-invocable: false
---

# Haskell guide for the code-quality reviews

`review-repo-code-quality` holds the review procedure, the report layout,
and the architecture principles that apply to every language; this guide
adds what holds for Haskell only. It is not a review on its own: a review
starts from `review-repo-code-quality`, which reads this guide in Step 1
for every repository with Haskell code in scope, and
`review-org-code-quality` uses its **static** tools before its depth
reviews. The category prefixes (`ARC`, `DC`, `DUP`, `CON`, `CL`, `NV`) and
the **static** / **consent** marks are defined in
`review-repo-code-quality`.

## Recognize

`*.hs`, `*.lhs`, `*.hs-boot`, and `*.hsc` files, with every `*.cabal`,
`package.yaml`, `cabal.project*`, and `stack.yaml`, and scripts without an
extension whose shebang runs `runghc`, `runhaskell`, `stack`, or `cabal`.
Out of scope: build output (`dist-newstyle/`, `.stack-work/`), vendored
packages, modules Alex and Happy generate from `*.x` and `*.y` grammars
(review the grammars), and Cabal's `Paths_<package>` and
`PackageInfo_<package>` modules, which a build generates. A `.cabal` file
that says `This file has been generated from package.yaml by hpack` is
generated too: changes go into `package.yaml`.

## Project rules

Read each `.cabal` file (`cabal-version`, `tested-with`, `build-type`, and per
component `default-language`, `default-extensions`, `ghc-options`,
`build-depends` with their bounds, `exposed-modules` against `other-modules`,
`common` stanzas, `flag`s), and whichever of these exist: `package.yaml`;
`cabal.project`, `cabal.project.local`, and `cabal.project.freeze`
(`with-compiler`, `constraints`, `allow-newer`, `source-repository-package`);
`stack.yaml` (`snapshot`, or its deprecated synonym `resolver`; `extra-deps`)
and `stack.yaml.lock`; `.hlint.yaml`; `fourmolu.yaml` and `.ormolu` (fixities
and re-exports); `weeder.toml`; `.stan.toml`; the task runner; and
`.pre-commit-config.yaml`. Source files state rules too: `LANGUAGE` and
`OPTIONS_GHC` pragmas (a file-level `-Wno-x-partial` is a decision), `HLINT
ignore` comments and `ANN` pragmas, and `ORMOLU_DISABLE` regions. `Setup.hs`
(`build-type: Custom`), `SetupHooks.hs` (`build-type: Hooks`), and `.ghci`
(GHCi, and so `cabal repl`, runs its commands) are code: read them as text.

The oldest compiler the project supports bounds what may be proposed: the
lowest `tested-with` entry, the oldest compiler in CI, Stack's snapshot
compiler, and the `base` lower bound (base 4.18 ships with GHC 9.6, 4.19
with 9.8, 4.20 with 9.10, 4.21 with 9.12, 4.22 with 9.14). `GHC2021` needs
GHC 9.2 and `GHC2024` 9.10; `-Wx-partial` exists from 9.8; the strict
`readFile'`, `getContents'`, and `hGetContents'` need base 4.15; the
Prelude exports `foldl'` from base 4.20. `common` stanzas need
`cabal-version: 2.2`, and `build-type: Hooks` 3.14.

## Tools

Building runs the repository's code (Template Haskell splices and
quasi-quoters, `{-# OPTIONS_GHC -F -pgmF <program> #-}` preprocessors such as
hspec-discover, `Setup.hs` under `build-type: Custom`), and Stack also runs
Hpack, which rewrites the `.cabal` file, and installs GHC unless given
`--no-install-ghc`; in tests even `ghc -fno-code` ran a splice and a `-pgmF`
preprocessor. Every `cabal` or `stack` build, repl, test, or haddock run, HLS,
and the tools that read a build's HIE files (weeder, stan) need consent. Build
in the throwaway checkout with `--builddir=<scratch>/dist`, which left it
clean (Stack writes `.stack-work/` there).

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Idiom drift, partial functions | `hlint`, your hint file | static with `--hint` | `hlint --hint=<scratch>/hlint.yaml -X<extension> … <files>` from the scratch directory, `<files>` being the tracked `*.hs` and `*.lhs` files as absolute paths (`review-repo-code-quality` Step 1), with `-X` for each `default-extensions` entry hlint leaves off, `--cpp-include=<checkout>/<dir>` for each `include-dirs` entry (a missing `#include` only warns), and the `-X` and `--cpp-*` `arguments` of the project's `.hlint.yaml` (below) |
| Idiom drift | `hlint`, the project's `.hlint.yaml` | consent | the CI step's invocation, else `hlint .` from the checkout |
| Formatting | `ormolu` | static with `--no-cabal --no-dot-ormolu` | `ormolu --mode check --no-cabal --no-dot-ormolu -o -X<language> -o -X<extension> … -p <package> … -f '<fixity>' … -r '<re-export>' … <files>` from the scratch directory on the tracked `*.hs` files (it does not parse `*.lhs`), giving it what those flags stop it reading: the `default-language` and each `default-extensions` entry as `-o -X…`, each `build-depends` package as `-p` (for its operators' fixities), and each line of `.ormolu` as `-f` (a fixity) or `-r` (a re-export). Without them, files the project's own run accepted failed: no `-o -XGHC2021` gave ``Found `qualified' in postpositive position``, no `-p containers` another layout of a `Data.Sequence` operator chain. It prints a diff and exits 100 (123 through `xargs`) for files it would change; `--no-dot-ormolu` and `-r` need ormolu 0.7: on 0.5 and 0.6 (Ubuntu 24.04) drop them, as `--no-cabal` alone skips `.ormolu` there |
| Formatting | `fourmolu`, your configuration | static with `--config` and `--no-cabal` | `fourmolu --mode check --config <scratch>/fourmolu.yaml --no-cabal -o -X<language> … -p <package> … <files>` likewise (fourmolu reads no `.ormolu`), the file holding the settings you read from the project's `fourmolu.yaml`, `fixities` and `reexports` included (`{}` gives the defaults; an empty file is rejected); where it sets `import-grouping`, add `--local-modules <module>` once per module of the package, or local imports lose their group |
| Dead code within a module or component | GHC warnings | consent | `cabal build all --enable-tests --enable-benchmarks --builddir=<scratch>/dist-w --ghc-options='-Wall -Wunused-packages -Wredundant-constraints -Wmissing-export-lists -Wpartial-fields'` (add `-Wincomplete-record-selectors` on GHC 9.10 and 9.12), for `-Wunused-top-binds`, `-Wunused-imports`, and `-Wunused-packages`, into a fresh directory each time: cabal-install 3.14 counts a change of warning flags alone as no change, and a rebuild into a used directory said `Up to date` and printed no warning |
| Dead code across modules | `weeder` | consent | after a build with `--ghc-options=-fwrite-ide-info`, `weeder --config <weeder.toml> --hie-directory <scratch>/dist` (below); exit status 228 means weeds were found, and weeder 2.11 also reports each configured root that matches nothing (`no declaration matches roots entry "^Paths_"` in a package without one, `"^Main\\.main$"` for a library alone): drop those roots |
| Partial functions, anti-patterns | `stan` | consent | `stan --hiedir=<scratch>/dist -s --hide-solution` from the checkout; it reads the package's `.cabal` file there, and `.stan.toml` unless given `--no-default` |
| Packaging | `cabal check` | static on a copy | `cabal check` in the package's directory in a copy of all the package's tracked files, made with the `review-repo-code-quality` Step 1 recipe into `<scratch>/pkg-copy` instead of `<scratch>/copy`, with `<scope>` the package's directory: the review's scope may leave out files the `.cabal` file names (without the `test/golden/` an `extra-source-files` pattern named, cabal-install 3.14.2.0 warned `[glob-missing-dir]`). It reads the `.cabal` file and the files that names, ignores `cabal.project`, and runs nothing; where only `package.yaml` is tracked, it stops with `No cabal file found`: say so in Method & limits |
| Module graph | `graphmod` | static with `--no-cabal` | `graphmod --no-cabal -q <files>` from the scratch directory prints DOT (`--no-cluster` drops the directory clusters); without `--no-cabal` it reads the first `.cabal` file in the working directory |
| Module graph | `import` lines, read as text | static | the grep below; `exposed-modules` tells public modules from internal ones |
| Complexity | none dedicated | static | lizard has no Haskell reader (1.26.1): module length (`wc -l`), long definitions and deep nesting by reading |
| Tests | the project's runner | consent | see Verification |

The hint file and the import search:

```yaml
# <scratch>/hlint.yaml: hlint's built-in hints apply as well; these
# restrictions report every use of these names, partial or not (Not findings)
- functions:
  - {name: [head, tail, init, last, fromJust, read, "!!", foldl, foldr1, foldl1, maximum, minimum, toEnum], within: []}
```

```sh
# imports; a {-# SOURCE #-} import marks a cycle broken by an .hs-boot file
grep -nE '^(>[[:space:]]*)?import[[:space:]]' <files>
```

hlint reads `.hlint.yaml` from the working directory, its parents, and the
home directory, and none once `--hint` names a file (its source; a traced
run opened nothing in the checkout but the sources and their `#include`s).
Read the project's as text, drop the hits its `ignore` entries turn off,
and pass its `-X` and `--cpp-*` `arguments` yourself; `HLINT ignore`
comments and `ANN` pragmas still apply. hlint reads no `.cabal` file and
leaves `QuasiQuotes`, `OverloadedRecordDot`, `Arrows`, `RecursiveDo`,
`UnboxedTuples`, and a few more off (code needing one may fail with
`Error: Parse error`). Its CPP pass knows no macros, Cabal's
`MIN_VERSION_*` included, so it checks one branch of each `#if`. Its
"Reduce duplication" hint is compiled out (3.10, issue 1150), so hlint
finds no clones.

ormolu and fourmolu look for configuration from each input file, so from
the scratch directory both still read the checkout's `.cabal` file (and
ormolu its `.ormolu`, fourmolu its `fourmolu.yaml`) until given the flags
above. Use the formatter version the project pins: releases change the
output.

weeder needs a configuration file: the project's `weeder.toml`, or yours:

```toml
# <scratch>/weeder.toml
roots = ["^Main\\.main$", "^Paths_"]
root-modules = ["^Pkg\\.Api$"]  # each exposed module of a library others can use
type-class-roots = true         # false also lists instances with no use seen
```

Its defaults (weeder 2.11.0) root only `Main.main` and the `Paths_`
modules, and no exposed module (`root-modules = []`), so a library's
exports show up as weeds; with the settings above a planted sample showed
only its dead code. HIE files are specific to the GHC that wrote them
(weeder exits 2 on a mismatch): build weeder and stan with that GHC (a
fetch: ask first, as Step 1 says).

## Checks

**Closed sets and constants**

- **A closed set compared as strings becomes a sum type** (`ARC`; `CON`
  when it stays inside one module). Strings compared in guard chains or
  `case` literals and listed again for validation, option parsing, or help
  text drift apart. Recommend one type,
  `data Mode = Fast | Medium | Slow deriving (Eq, Ord, Show, Enum, Bounded)`,
  parsed once where values enter, rendered by one function, and matched by
  `case` elsewhere, where `-Wincomplete-patterns` (in `-Wall`) reports each
  missed constructor; `[minBound .. maxBound]` lists every value for
  validation, help, and a round-trip test. A safe first step (`CON`,
  changing no type or output) is one list of the accepted strings that
  validation, help, and comparisons share. Pitfalls of the type:
  - Derived `Show` and `Read`, and aeson's `Generic`-derived instances
    (2.2.5.1 and 2.3.3.0), use constructor names: they write `"Fast"` and
    reject `"fast"`. Where text crosses a boundary (command line, files,
    JSON, a database, logs), keep the old spelling in explicit render and
    parse functions or aeson `Options`; derived instances there are `NV`.
  - Derived `Enum` and `Ord` follow declaration order, so inserting or
    reordering constructors changes persisted `fromEnum` values, `Map` key
    order, and sorted output: append. `succ` past the last constructor and
    an out-of-range `toEnum` throw.
  - An exported `String` parameter turned into the type is an API change
    (`NV` in a library) unless a `String` wrapper stays.
- **The same literal in several modules** (`ARC`; `CON` inside one
  module): one top-level constant, or a constructor of the type above.
- **Type synonyms for distinct things** (`ARC`; `NV` if exported):
  `type UserId = Int` mixes with any `Int`, where a `newtype` with
  `deriving newtype` instances keeps the output and catches mix-ups.

**Modules and structure**

- **Missing export lists** (`-Wmissing-export-lists`; `NV` in a library
  other packages can depend on, where the list removes names from its API,
  `CL` elsewhere): every helper is exported, and from a library's
  `exposed-modules` becomes API. Adding the list lets `-Wunused-top-binds`
  report what nothing uses. Test-only internals belong in an `Internal`
  module or a private sublibrary (`visibility: private`).
- **Import cycles** (`ARC`): GHC compiles one only through an `.hs-boot`
  file and a `{-# SOURCE #-}` import; name it and the move that removes it.
- **Orphan instances** (`ARC`; `-Worphans`, in `-Wall`): defined with
  neither the class nor the type. GHC suggests the class's or the type's
  module (within one package) or a `newtype`; moving one changes which
  imports bring it into scope (`NV` in a library).
- **Effects at the edges** (`ARC`): global state through `unsafePerformIO`
  and `NOINLINE`, environment reads deep in the core, `IO` threaded through
  logic that needs none, and grab-bag `Utils` modules everything imports.

**Partiality and errors** (`NV`: a fix changes what failing input does)

- **Partial functions**: `head`, `tail`, `init`, `last`, `!!`, `fromJust`,
  `read`, and `maximum`, `minimum`, `foldr1`, `foldl1` on lists that may be
  empty; `toEnum`, `succ`, `pred` at a range's ends. GHC warns only for
  `head` and `tail` (`-Wx-partial`, on by default from 9.8); the hint file
  and stan list the rest. `NonEmpty`, `listToMaybe`, and `readMaybe` handle
  the failing case; `CL` only where the call site already rules it out.
- **Incomplete patterns and partial fields**: `-Wincomplete-patterns`,
  `-Wincomplete-uni-patterns`, `-Wincomplete-record-updates` (in `-Wall`),
  `-Wpartial-fields`, and `-Wincomplete-record-selectors` (from GHC 9.10;
  `-Wall` has it only from 9.14, though the 9.10 and 9.12 docs list it).
- **`error` and `undefined` in library code**, and catch-alls on
  `SomeException`, which base's documentation warns also catch
  `UserInterrupt` (Control-C) and `ThreadKilled`.

**Strictness, text, and I/O**

- **Lazy accumulators** (`CL` where the step forces the accumulator anyway,
  as `(+)` on `Int` does; else `NV`, since forcing earlier can raise an
  error laziness skipped): `foldl` (hlint suggests `sum` for
  `foldl (+) 0`), `modifyIORef` (base warns that it piles up thunks), a
  lazy `Data.Map` updated in a loop, accumulator fields without bangs.
- **Lazy I/O** (`NV`): `readFile`, `getContents`, `hGetContents`, and
  `interact` hold the handle until the text is consumed; reading a file and
  writing it back failed with `resource busy (file is locked)` (GHC
  9.12.4). The strict `readFile'` family or a strict `ByteString` read
  replaces them, and moves when errors and memory use happen.
- **`String` for text** (`ARC`; `NV` for an exported signature): `pack` and
  `unpack` at every boundary; `Text` for text and `ByteString` for bytes,
  converted with `encodeUtf8` and `decodeUtf8'` at the edges.
  `Data.ByteString.Char8.pack` on text keeps the low eight bits of each
  character (`λ` became byte 187; stan `STAN-0203`): a bug, `NV`.

**Idioms** (`CL`; hlint finds most — group its hits by hint name)

- hlint hints without a `Note:` are equivalent rewrites (its README); a
  note of "Increases laziness", "Decreases laziness", "Removes error", or a
  restriction's "may break the code" marks a behavior change: `NV` unless
  the trace rules the difference out. Eta reduction can change behavior
  under `seq` and trip the monomorphism restriction: rebuild after it lands.
- `LANGUAGE` pragmas that `default-extensions` or the `default-language`
  already cover, or hlint's "Unused LANGUAGE pragma"; `-Wunused-imports`,
  except an import a newer `base` made redundant (`foldl'` from `Data.List`)
  while an older one is tested; `-Wredundant-constraints` (`NV` if exported).
- Suppressions that suppress nothing (`DC`): `-Wno-…` for a warning that no
  longer fires, `HLINT ignore` comments and `ignore` entries with no hit,
  and weeder roots it reports as matching nothing.

**Packages**

- `build-depends` no module of the component imports (`-Wunused-packages`;
  `DC`); `ghc-options`, `default-extensions`, and dependencies repeated in
  every component (`CON`: a `common` stanza, or Hpack's top-level fields).
- Missing upper bounds (`cabal check` lists them), `allow-newer`, and git
  pins in `source-repository-package` or `extra-deps` (`NV`).

**Currency** (reported as `review-repo-code-quality` Step 2 says; read the
live sources each item names rather than trusting its examples)

- **GHC versions.** Compare `tested-with`, the CI matrix, `base` bounds,
  `with-compiler`, and Stack's compiler with https://www.haskell.org/ghc/,
  each series' status
  (https://gitlab.haskell.org/ghc/ghc/-/wikis/GHC-status), and GHCup's
  tags (`ghcup list`, or
  https://raw.githubusercontent.com/haskell/ghcup-metadata/develop/ghcup-0.0.9.yaml).
  GHC 9.14 is the first long-term-support series, supported for two years
  or more; other majors come about every six months with shorter support
  (https://blog.haskell.org/ghc-lts-releases/, July 2025). Cabal ignores
  `tested-with`: report entries CI does not build, CI that builds no
  maintained series, and the newest release missing.
- **Language edition.** `Haskell2010`, or no `default-language`, which
  Cabal builds as `Haskell98` (cabal-install 3.14.2.0 passed `-XHaskell98`,
  and `cabal check` reports the omission as an error Hackage rejects; GHC
  9.2 to 9.14 on its own, as for a `runghc` script, uses `GHC2021`),
  against `GHC2024`, which GHC's user's guide recommends for new code; it
  needs GHC 9.10 across the tested range and adds `DataKinds`, `GADTs`,
  `LambdaCase`, `MonoLocalBinds`, and four more to `GHC2021`.
  `MonoLocalBinds` stops generalising local bindings without signatures,
  which can break the build (`NV`).
- **Cabal.** `cabal-version` too low for the fields used (`cabal check`),
  `build-type: Custom` where `Simple` or `Hooks` would do (Cabal's guide
  recommends `Hooks`), and the specification versions at
  https://github.com/haskell/cabal/blob/master/doc/file-format-changelog.rst;
  raising `cabal-version` raises the cabal-install every builder needs
  (`NV`).
- **Stackage.** `snapshot` (or `resolver`) against https://www.stackage.org/
  (files: https://github.com/commercialhaskell/stackage-snapshots).
- **Deprecations.** From the scratch directory,
  `curl -sS -H 'Accept: application/json' https://hackage.haskell.org/package/<name>/deprecated`
  gives `is-deprecated` and `in-favour-of`; `.../preferred` lists
  deprecated versions. In code: `-Wdeprecations` (on by default) and
  `-Wcompat` (consent build).
- **CI.** `haskell/actions/setup`, `hlint-setup`, and `hlint-run` come
  from a repository archived on 2024-01-05: use the same names under
  `haskell-actions/`; `haskell-actions/run-ormolu` was archived on
  2026-08-20. A haskell-ci workflow names its generator in a `# version:`
  line and its job image in `container: image:`
  (`buildpack-deps:<Ubuntu codename>`; see
  https://ubuntu.com/about/release-cycle); compare tool pins with Hackage.

## Not findings

- Exports of a library other packages can depend on (one on Hackage, or
  one another repository uses): callers live in other packages; weeder
  lists them unless `root-modules` covers them. Removing one is `NV`. In a
  private sublibrary (`visibility: private`) or a library only this
  project uses, an export no component imports is dead (`DC`): leave its
  modules out of `root-modules`.
- Hint-file hits on total namesakes: the restrictions match names, not
  types, so they flag `Data.List.NonEmpty`'s `head`, `tail`, `init`, and
  `last` (hlint 3.10 flagged `NE.head` and `NE.tail`) and `maximum`,
  `minimum`, `foldr1`, or `foldl1` applied to a `NonEmpty`; check the type
  before calling a hit partial.
- Instances used through their class (`show`, aeson's generic encoding,
  `OverloadedStrings` literals): weeder with `type-class-roots = false`
  reports them, rooting only `IsString` and `IsList` instances by default.
- `Paths_<package>` and `PackageInfo_<package>`, generated by Cabal: weeder
  reported their unused functions, and stan a partial `last` in one.
- Names Template Haskell creates or reads: `makeLenses` lenses and the
  `_field` names behind them, `deriveJSON` instances, quasi-quoter output;
  weeder does not follow references inside splices (its README).
- Test and benchmark components: `main-is` modules, doctest's `>>>`
  examples, and hspec-discover's `*Spec.hs` files exporting `spec`, found
  through `{-# OPTIONS_GHC -F -pgmF hspec-discover #-}`.
- Bindings named with a leading `_`, which GHC's unused warnings skip
  (weeder still lists them).
- CPP branches for other compilers or platforms (`MIN_VERSION_base`,
  `__GLASGOW_HASKELL__`, `mingw32_HOST_OS`): dead locally, live in the
  tested range; only branches below the supported floor are `DC`.
- `seq`, `$!`, bang patterns, `evaluate`, and `force` that look redundant:
  they decide when evaluation happens and how much memory a run holds.
- `Setup.hs` under `build-type: Simple`, which Cabal ignores, and stan's
  "Infinite" hits on finite data (`STAN-0105` on `sum` over `Map.elems`).

## Verification

- **Baseline and after each group** (consent, throwaway checkout): the
  project's entry point (a CI step, a Makefile target), else `cabal build
  all --enable-tests --enable-benchmarks --builddir=<scratch>/dist` and
  `cabal test all --builddir=<scratch>/dist` (Stack: `stack build --test
  --no-run-tests --bench --no-run-benchmarks`, then `stack test`), with
  each installed `tested-with` compiler (`-w ghc-<version>`), at least the
  oldest and the newest; record the pass and fail counts.
- **Warnings** (consent): the warning build from Tools, into a fresh
  directory, before and after; only the targeted warnings may go away.
- **Static, after any edit**: the static hlint command on the changed files
  (a syntax error shows as `Error: Parse error`) and the formatter check.
- **Public API** (consent): `cabal haddock <library> --haddock-hoogle
  --builddir=<scratch>/api-before`, then `api-after`, and diff their
  `doc/html/<package>/<package>.txt` (exposed modules' exports and types).
- **Closed-set migrations**: what crosses each boundary (rendered text,
  JSON, help, files) must match byte for byte on the same inputs, and
  `parse (render m) == Just m` hold for each `m` in `[minBound .. maxBound]`.
- **Strictness changes**: outputs and `maximum residency` from `+RTS -s`
  (GHC 9.12.4 took it without `-rtsopts`), same input, before and after.
