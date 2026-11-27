---
name: rust-practices
description: Rust practices — where a crate or Cargo workspace states its rules, its review tools and which need execution consent, Rust checks such as a set of values matched as strings that becomes one enum, panics and error types in library code, and feature combinations, currency (editions, rust-version, lazy_static, archived actions-rs actions, RustSec advisories), false positives, and verification commands. Use when writing, changing, or reviewing Rust code, including in a pull-request review or a code-quality review (review-repo-code-quality and review-org-code-quality read it).
allowed-tools: Read
user-invocable: false
---

# Rust practices

What holds for Rust code only, for three kinds of work: writing or
changing it, reviewing a pull request, and the code-quality reviews
(`review-repo-code-quality` reads this guide in Step 1;
`review-org-code-quality` runs its **static** tools). When writing code,
follow Project rules and Checks and leave Not findings alone; when
reviewing, report against them. The procedure, the architecture
principles, the category prefixes (`ARC`, `DC`, `DUP`, `CON`, `CL`, `NV`),
and the **static** / **consent** marks on the Tools are defined in
`review-repo-code-quality`.

It is written for command-line tools and small async services (tokio, an
HTTP framework such as axum, S3 or WebDAV access) in single crates or
small workspaces, tested with `cargo test`. Embedded and `no_std` code,
WebAssembly, FFI-heavy crates, GUI and game code, and procedural-macro
authoring are left out: check their conventions before reporting there.

## Recognize

`*.rs` files, with every `Cargo.toml`, `Cargo.lock`, and
`rust-toolchain.toml` (or the older `rust-toolchain`). Out of scope:
`target/`, `vendor/` (from `cargo vendor`), and generated files, such as
those with an `@generated` marker near the top
(`git -C <checkout> grep -lE '@generated' -- '*.rs'` lists them). Code a
build script writes to `OUT_DIR` is not in the checkout: review the
script instead.

## Project rules

Read each `Cargo.toml` — `[package]` (`edition`, `rust-version`,
`publish`), `[workspace]` (`members`, `resolver`), the `[workspace.*]`
tables members inherit, `[lints]` (a member applies `[workspace.lints]`
only with `[lints] workspace = true`), `[features]`, every dependency
table, `[profile.*]`, `[patch]`, and the `metadata` tables
tools read — then `rust-toolchain.toml`, `.cargo/config.toml`
(`build.rustflags` such as `-D warnings`, `[alias]`, `[env]`, runners),
`clippy.toml` and `rustfmt.toml` (or their dot-prefixed names),
`deny.toml`, `.cargo/audit.toml`, the attributes atop each `lib.rs` and
`main.rs` (`#![forbid(unsafe_code)]`, `#![deny(…)]`), the `RUSTFLAGS`
and cargo flags CI passes, and task runners (`justfile`,
`Makefile.toml`, an `xtask` crate). `build.rs`, procedural-macro
crates, and `xtask` are code: read them as text.

The oldest Rust the project supports — `rust-version`, else the oldest
toolchain CI tests — bounds what may be proposed: `let … else` needs
1.65, `async fn` in traits 1.75, `LazyLock` 1.80, and `let` chains 1.88,
in the 2024 edition only
(https://github.com/rust-lang/rust/blob/main/RELEASES.md). Clippy holds
its suggestions to `rust-version`, and `incompatible_msrv` reports
standard-library items newer than it.

## Tools

Anything that compiles — `cargo check`, `build`, `clippy`, `test`,
`cargo-udeps`, `cargo-hack`, `cargo-semver-checks` — runs the build
scripts and procedural macros of the workspace and its dependencies, and
any `cargo` command started in the checkout reads its `.cargo/config.toml`,
whose `build.rustc-wrapper`, runners, and `[alias]` entries name programs
to run (an alias named `fmt` replaces `cargo fmt`). In testing, even
`cargo metadata` ran a configured `rustc-wrapper`, downloaded every
dependency, and wrote a missing `Cargo.lock` (`--no-deps` did none of
these). The rustup proxies take the toolchain from a `rust-toolchain.toml`
in the working directory or a parent, downloading a `channel` that is not
installed and running the binaries a `path` names. So all of these need
consent: run them in the throwaway checkout with `RUSTUP_AUTO_INSTALL=0`
(rustup 1.28.1 or later; a review installs no toolchain), with
`CARGO_TARGET_DIR=<scratch>/target` (builds otherwise write `target/` into
the checkout), and with `--locked` where the command takes it
(`cargo fmt` and cargo-semver-checks 0.51.0 reject it), which fails
where no `Cargo.lock` is committed: run `cargo generate-lockfile` there
first, and say so in Method & limits. Run the static tools from the
scratch directory, where the proxies find no toolchain file of the
checkout, on `<files>`: the scope's tracked `*.rs` files as absolute
paths (`review-repo-code-quality` Step 1), and `<manifests>`, its
`Cargo.toml` files likewise.

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Formatting, and a parse check | `rustfmt`, your configuration | static with `--config-path` | `rustfmt --check --edition <edition> --config-path <scratch>/rustfmt.toml <files>`, one run per edition the crates use (without `--edition`, rustfmt parses as 2015, where `async fn` is an error); `<scratch>/rustfmt.toml` is empty or holds the stable options you copy from the project's file; without `--config-path` rustfmt reads the `rustfmt.toml` or `.rustfmt.toml` nearest each file, and without `--check` it rewrites the files |
| Complexity | `lizard` | static | `lizard -l rust -w <files>` (warns above 15 CCN; `-C` sets it); lizard 1.26.1 counts every `?`, boolean operator, and `match` arm after the first, so many `?` or a flat `match` over an enum score high without being hard to read |
| Dead code: items | rustc's `dead_code` and `unused_*` lints | consent | `cargo check --workspace --all-targets --all-features --locked --message-format short`, then once per feature set CI builds (`--no-default-features`, …) |
| Dead code: what `#[allow]` hides | rustc's `--force-warn` | consent | the clippy command below with `--force-warn dead_code` after `--`: an `#[allow(dead_code)]` with no warning under it is stale |
| Dead code: dependencies | `cargo-machete`, on the copy | static | see below; cargo-machete 0.10.1 checks `[dependencies]` only |
| Dead code: dependencies | Cargo's own lints (Cargo 1.100 or later) | consent | the `cargo check` above warns `cargo::unused_dependencies` (never for `[dev-dependencies]`), `unused_workspace_dependencies`, and `missing_lints_inheritance` in each package whose `rust-version` is unset or 1.79 or later |
| Dead code: dependencies | `cargo-udeps` | consent: needs a nightly toolchain | `cargo +nightly udeps --workspace --all-targets --locked`; it also checks `[dev-dependencies]`, and reports crates used only in doc tests as unused |
| Idiom drift | `cargo clippy`, the project's configuration plus lints | consent | `cargo clippy --workspace --all-targets --all-features --locked --message-format short -- -W clippy::pedantic -W clippy::cargo -W clippy::unwrap_used -W clippy::expect_used -W clippy::panic -W clippy::indexing_slicing -W clippy::wildcard_enum_match_arm -W clippy::undocumented_unsafe_blocks -W clippy::allow_attributes_without_reason -W unreachable_pub` |
| Module graph | `mod` and `use` lines, read as text | static | the searches below |
| Crate graph, duplicate versions | `cargo tree` | consent | `cargo tree --workspace --duplicates --locked`; `-i <crate>` shows what pulls a crate in; both cover only the host platform unless given `--target all` |
| Crate graph, duplicate versions | the manifests and `Cargo.lock`, read as text | static | the greps below |
| Vulnerabilities, unmaintained crates | `cargo-audit` | static from the scratch directory | `cargo audit --file <checkout>/Cargo.lock --db <scratch>/advisory-db` (exit status 2 where no `Cargo.lock` is committed); run from the checkout it would apply the ignore list in `.cargo/audit.toml`; it fetches the RustSec database from GitHub (record its last commit date, `git -C <scratch>/advisory-db log -1 --format=%cd`, in Method & limits) and the crates.io index (`--no-yanked` skips the yanked-crate check); in an org review, share one `--db` directory; its findings are security-sensitive (conventions §2) |
| Advisories, licenses, bans | `cargo-deny`, the project's `deny.toml` | consent: runs `cargo metadata` | `cargo deny --locked check` (cargo-deny 0.22.0 takes the flag before the subcommand and rejects `check --locked`) |
| Feature combinations | `cargo-hack` | consent | `cargo hack check --workspace --each-feature --locked`, or `--feature-powerset` (`--depth 2` bounds it); not `--no-dev-deps`, which rewrites `Cargo.toml` while it runs |
| Tests | `cargo test` | consent | see Verification |

cargo-machete and the searches:

```sh
# cargo-machete always applies `ignored` and `renamed` from [package.metadata.cargo-machete] and
# [workspace.metadata.cargo-machete]: rename them in the review-repo-code-quality Step 1 copy, and
# run it there, never with --fix or --with-metadata
find <scratch>/copy -name Cargo.toml -type f -print0 | xargs -0 -r sed -i.bak 's/cargo-machete/cargo-machete-off/g'
cargo-machete --no-ignore <scratch>/copy
# mod declarations; whole use declarations (rustfmt splits long ones); paths written in code
grep -nE '^[[:space:]]*(pub(\([^)]*\))?[[:space:]]+)?mod[[:space:]]+[A-Za-z_][A-Za-z0-9_]*' <files>
awk '/^[[:space:]]*(pub(\([^)]*\))?[[:space:]]+)?use[[:space:]]/ {u = 1} u {print FILENAME ":" FNR ":" $0} /;/ {u = 0}' <files>
grep -nE '\b(crate|super|self)::' <files>
# path dependencies between the workspace's crates (a [lib] or [[bin]] path = line matches too); crates locked in several versions
grep -nE '\bpath[[:space:]]*=' <manifests>
grep '^name = ' <checkout>/Cargo.lock | sort | uniq -d
# closed sets: match arms on string literals, and comparisons with them
grep -nE '^[[:space:]]*"[^"]*"([[:space:]]*\|[[:space:]]*"[^"]*")*[[:space:]]*(if[[:space:]].*)?=>' <files>
grep -nE '[=!]=[[:space:]]*"[^"]*"' <files>
```

Without `--no-ignore`, cargo-machete skips each crate whose directory
`.gitignore` or `.ignore` lists; on the copy, check the crates `renamed`
lists by hand. rustfmt also checks the modules a file declares
(`mod name;`), tracked or not, so a diff can appear twice;
`#[rustfmt::skip]` applies.

## Checks

**Closed sets and constants**

- **A set of values matched as strings becomes one enum** (`ARC`; `CON`
  when it stays inside one module). The same literals in `match` arms,
  `==` chains, command-line value lists, and validation code (the
  closed-set greps above) drift: one place accepts `"normal"`, another
  lets it fall through `_ =>`. Define one `enum` with `FromStr` and
  `Display` (a `match` each way, or strum's derives where the project
  uses strum), with serde's derives and `clap::ValueEnum` where values
  are serialized or parsed from the command line, and match it without a
  `_` arm inside the crate (`clippy::wildcard_enum_match_arm`), so a new
  variant fails to compile wherever it is not handled. Before rating the
  change **High**, check each place a value crosses a boundary: in
  testing, serde wrote the variant name (`"Fast"`) unless `rename_all`
  or `rename` restores the string, and strum's `EnumString` rejected
  `"fast"` unless told otherwise; `ValueEnum` listed `SlowAndSteady` in
  `--help` as `slow-and-steady`; `{:?}` printed `Fast` where it had
  printed `"fast"`; and a value a `_ =>` arm used to absorb now fails to
  parse. In a library, a public function that takes `&str` can keep its
  signature and parse into the enum inside (`CON`); taking the enum is an
  API change (`NV`), and so is adding `#[non_exhaustive]` later, so a
  public enum that may grow gets it when it is introduced. Where variants
  are stored as numbers (implicit discriminants count up in declaration
  order), append new ones, never reorder.
- **The same literal in several places** (`ARC` across modules or
  crates; `CON` inside one module): one `const`.

**Modules, visibility, and manifests**

- **Module cycles** (`ARC`), which rustc accepts: find them in what the
  `use` and path searches print, and name the move that breaks each.
- **`pub` wider than needed** (`CL` where no other crate can reach the
  item; `NV` for a library's public API): `unreachable_pub` lists `pub`
  items in private modules, and an unused `pub fn` at a binary's root
  drew no `dead_code` warning in testing, which `pub(crate)` fixes.
- **Settings repeated in every member** (`CON`): versions, `edition`,
  `rust-version`, and lint levels copied into each manifest or crate
  root move to `[workspace.package]`, `[workspace.dependencies]`, and
  `[workspace.lints]` (1.74); check that each member's features and lint
  output stay the same (`cargo tree -e features`, `cargo clippy`;
  consent).
- **Inert settings** (`DC`; in testing, with Cargo 1.100): `[profile.*]`
  and `[patch]` in a member manifest (Cargo warns that it ignores them);
  `[workspace.lints]` a member does not inherit and
  `[workspace.dependencies]` no member uses (Cargo's lints above); a
  `clippy.toml` `msrv` equal to `rust-version` (one that differs is not
  inert: clippy uses it in place of `rust-version`, with a warning, so
  changing it is `NV`); ignore entries in `deny.toml` that match no
  locked crate (`cargo deny check` warns `advisory-not-detected`); and
  `cfg(feature = "…")` names that neither `[features]` nor an optional
  dependency declares (`unexpected_cfgs`). A virtual workspace without
  `resolver` gets resolver 1, with a warning, even when its members use
  the 2021 or 2024 edition; setting it changes which features are
  unified (`NV`).

**Errors, panics, and unsafe code** (usually `NV`: behavior changes)

- `unwrap()`, `expect()`, `panic!`, and indexing on values a caller
  controls, in library code (`clippy::unwrap_used`, `expect_used`,
  `panic`, `indexing_slicing`): returning a `Result` changes the
  signature. A `# Panics` doc section (`clippy::missing_panics_doc`) is
  `CL`; so is `expect("why it holds")` for `unwrap()` on an invariant,
  unless a `#[should_panic(expected = …)]` test matches the message.
- Public functions of a library that return `anyhow::Error`,
  `Box<dyn Error>`, or `String` errors leave callers nothing to match: a
  typed error enum (with `thiserror` where the project uses it) is an
  API change. Hand-written `Display`, `Error`, and `From` impls repeated
  across error types become derives (`CON`) only if the messages and
  `source()` stay the same: in testing, a thiserror `#[from]` field
  became the `source()`, which `anyhow`'s `{:#}` then printed too.
- Errors dropped with `let _ =` or `.ok()` where a caller would want
  them; `std::process::exit` in library code.
- `unsafe` blocks without a `// SAFETY:` comment
  (`clippy::undocumented_unsafe_blocks`; adding one is `CL`), and
  `unsafe` code that a safe standard API now covers. Where the project
  forbids unsafe code (`#![forbid(unsafe_code)]`, or
  `unsafe_code = "forbid"` under `[lints.rust]`), a crate without the
  rule is project-rule drift.

**Features and dependencies**

- Feature combinations that fail to build, and features that are not
  additive (`cargo hack check --each-feature`) — `NV`. An empty feature
  no `cfg` reads is `DC` in a binary, public API in a library (`NV`).
- A `[dependencies]` entry only tests, examples, or benchmarks use moves
  to `[dev-dependencies]` (`DC`; `NV` when another dependency needs a
  feature it turns on).

**Idioms** (`CL`; clippy finds most — group its hits by lint)

- `#[allow(…)]` without a reason (`allow_attributes_without_reason`), and
  allowances nothing triggers any more (`DC`; the `--force-warn` row):
  `#[expect(…)]` (1.81) warns once its lint stops firing;
- an item only tests use, outside `#[cfg(test)]`: move it in;
- copies of a function per type that generics or a `macro_rules!` can
  merge (`CON`), identical branches (`DUP`; `clippy::match_same_arms`,
  pedantic, and `if_same_then_else`), and test functions that differ
  only in their data (`DUP`; one test over a table of cases);
- `String`, `Vec<T>`, or `&Vec<T>` parameters where `&str` or `&[T]`
  would do (`clippy::ptr_arg`, `needless_pass_by_value`) — an API change
  in a library (`NV`).

**Currency** (reported as `review-repo-code-quality` Step 2 says; read the
live sources each item names)

- **Rust releases.** A stable release ships every six weeks, and only
  the newest gets fixes (https://www.rust-lang.org/policies/security;
  https://github.com/rust-lang/rust/blob/main/RELEASES.md). Report CI
  that never builds the newest stable, a `rust-version` no CI job
  builds, and a `rust-toolchain.toml` far behind; for raising
  `rust-version`, list what it would unlock.
- **Editions.** The 2024 edition (Rust 1.85, 2025-02-20) implies
  `resolver = "3"`, which prefers dependency versions that support
  `rust-version`. For a crate on an older edition, list what
  `cargo fix --edition` (consent; it rewrites files) would change, from
  https://doc.rust-lang.org/edition-guide/ — `NV`. Manifest spellings
  2024 rejects (`dev_dependencies`, `default_features`, and the like)
  have equivalents in every edition: renaming them is `CL`, as is
  renaming `.cargo/config`, which Cargo warns is deprecated, to
  `.cargo/config.toml`.
- **`lazy_static` and `once_cell`.** `std::sync::LazyLock` (1.80) and
  `OnceLock` (1.70) replace them; lazy_static's README says it "will no
  longer be updated". `clippy::non_std_lazy_statics` (pedantic) lists
  both once `rust-version` is 1.80 or later. Code that calls
  once_cell's `get_or_try_init` keeps once_cell: std's version
  (`once_cell_try`) was still unstable in 1.100.
- **CI.** The `actions-rs` actions (`toolchain`, `cargo`,
  `clippy-check`, `audit-check`) were archived on 2023-10-13 and declare
  the `node12` runtime: `rustup` and `cargo` commands in `run:` steps
  replace them (GitHub's runner images ship rustup,
  https://github.com/actions/runner-images).
- **Advisories.** The RustSec database (https://rustsec.org/advisories/)
  records vulnerable, unmaintained, and unsound crates; the static
  `cargo audit` reports vulnerabilities as errors, and the rest, with
  yanked versions it looks up in the crates.io index, as warnings, which
  deserve a line too (`atty`, unmaintained per RUSTSEC-2024-0375).

## Not findings

- Items used only under `#[cfg(test)]`, a feature, or a target OS or
  architecture, or only by another target (tests, examples, benchmarks,
  binaries): rustc reports them as dead in the builds that leave their
  callers out. Analyze with the feature sets and targets CI builds.
- A library's `pub` items that code outside the repository can reach (a
  crate published to a registry or used as a git dependency), and
  `#[doc(hidden)] pub` items its own macros reach: having no caller
  inside the repository does not make them dead; removing one is `NV`.
  In a crate only this workspace uses (`publish = false`, no outside
  dependents), a `pub` item nothing in the workspace uses is dead
  (`DC`); rustc does not report it.
- `unwrap()`, `expect()`, `panic!`, and indexing in tests, `#[cfg(test)]`
  modules, examples, benchmarks, and build scripts: the clippy command
  lints every target, but the Errors check covers library code only.
- Build-script outputs: code pulled in with
  `include!(concat!(env!("OUT_DIR"), …))`, and code behind a `cfg` or
  variable the script sets (`cargo:rustc-cfg`, `cargo:rustc-env`).
- Items reached by name: `#[no_mangle]` functions, a `#[global_allocator]`
  static, and registrations through `inventory` or `ctor`.
- Trait implementations whose methods no caller names (`Drop`, `From`,
  `Display`, operators), and fields read only by a derived `Debug`:
  rustc reports such a field as never read, but removing it changes the
  `Debug` output (`NV`).
- `let _guard = lock();`, which holds the value to the end of the scope
  (`let _ = lock();` drops it at once), and `_`-prefixed parameters a
  trait or callback signature requires.
- Dependencies `cargo-machete` reports that the build uses: through
  generated code, another crate's macros, a library whose name differs
  from its package's (`[lib] name`; the `renamed` table maps it), or only
  to turn on a feature another dependency needs.
- Generated code: change the generator, not its output.

## Verification

- **Baseline and after each group** (consent, in the throwaway checkout,
  with the environment from Tools): the project's entry point (the CI
  steps, `just`, `cargo xtask`, `cargo make`), else
  `cargo build --workspace --all-targets --locked`,
  `cargo test --workspace --locked`, `cargo fmt --all --check`, and
  `cargo clippy --workspace --all-targets --locked`, with the features
  and `RUSTFLAGS` CI uses; record passed, failed, and ignored counts.
  `cargo test --all-targets` runs no doc tests: add `cargo test --doc`.
- **Static, after any edit**: the static `rustfmt --check` command on
  the changed files shows no new diff and no parse error.
- **Feature sets and the minimum version** (consent):
  `cargo hack check --workspace --each-feature --locked`, and
  `cargo hack check --rust-version --workspace --locked`, which installs
  that toolchain itself (`rustup toolchain add`) when it is missing:
  check `rustup toolchain list` first, and skip the check when it is not
  installed.
- **Public API** (consent):
  `cargo semver-checks -p <crate> --baseline-rev <ref>` lists breaking
  changes against a git revision (by default, against crates.io).
- **Enum migrations**: capture what crosses each boundary — serialized
  output, `Display` and `Debug` text, `--help`, sort orders — on the same
  inputs before and after; the bytes must match.
