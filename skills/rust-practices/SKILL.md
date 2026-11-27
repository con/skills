---
name: rust-practices
description: Rust practices for command-line tools and small async services in single crates or small workspaces — the house's preferences (one enum with FromStr and Display for a closed set, Result and typed errors over panics in library code, SAFETY comments, workspace inheritance, additive features, LazyLock over lazy_static, rustup over actions-rs in CI), public surface and deprecation, false positives, and verification, with the review tools and detailed checks in references/review.md. Use when writing, changing, or reviewing Rust code, including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# Rust practices

The house's practices for Rust code, for three kinds of work: writing or
changing it, reviewing a pull request, and the code-quality reviews. Read
`general-practices` first: it says how to weigh these preferences against
the project's own rules and your own judgment, and defines the marks and
categories used here. [references/review.md](references/review.md) holds
what a review needs beyond them: the tools with their **static** /
**consent** marks, the detailed checks with their categories and pitfalls,
currency sources, and verification commands.

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

Read each `Cargo.toml` (`[package]`, `[workspace]` and the
`[workspace.*]` tables, `[lints]`, `[features]`), `rust-toolchain.toml`,
`.cargo/config.toml`, `clippy.toml`, `rustfmt.toml`, the attributes atop
`lib.rs` and `main.rs`, and the flags CI passes. The oldest supported Rust
(`rust-version`, else the oldest toolchain CI tests) bounds what may be
proposed: `let … else` needs 1.65, `LazyLock` 1.80, and `let` chains 1.88
and the 2024 edition.

## Preferences

- **Closed sets**: values matched as strings become one `enum` with
  `FromStr` and `Display`, serde's derives and `clap::ValueEnum` where
  values cross a boundary, and no `_` arm inside the crate, so a new
  variant fails to compile where it is not handled.
- **Enum pitfalls**: serde writes the variant name (`"Fast"`) unless
  `rename_all` restores the string; a public enum that may grow gets
  `#[non_exhaustive]` when introduced, as adding it later is an API change.
- **Errors in library code**: a `Result`, not `unwrap()`, `panic!`, or
  indexing on values a caller controls; public functions return a typed
  error enum (`thiserror` where used), not `anyhow::Error` or `String`.
- **Unsafe code**: each `unsafe` block has a `// SAFETY:` comment; where
  the project forbids unsafe code, every crate carries the rule.
- **Workspaces**: versions, `edition`, `rust-version`, and lint levels
  are set once in the `[workspace.*]` tables members inherit; a virtual
  workspace without `resolver` gets resolver 1.
- **Features and dependencies**: features are additive and each builds on
  its own; a dependency only tests use belongs in `[dev-dependencies]`.
- **Standard library over legacy**: `std::sync::LazyLock` (1.80) and
  `OnceLock` (1.70), not `lazy_static` or `once_cell`, unless code calls
  once_cell's `get_or_try_init`.
- **Lint allowances**: `#[expect(…)]` (1.81), which warns once its lint
  stops firing, rather than `#[allow(…)]`, each with a reason.
- **Idioms**: `&str` and `&[T]` parameters, not `String` or `&Vec<T>`
  (an API change in a library); test-only items inside `#[cfg(test)]`;
  tests that differ only in their data as one test over a table of cases.
- **Toolchain and CI**: CI builds the newest stable and `rust-version`
  with `rustup` and `cargo` in `run:` steps, not the archived
  `actions-rs` actions.

## Public surface and deprecation

- **Internals**: private items, `pub(crate)`, and private modules
  (references/review.md, Modules, visibility, and manifests);
  `#[doc(hidden)]` marks an item that is public only for macros or tests.
- **Deprecating** a public item: keep it and add
  `#[deprecated(since = "1.4.0", note = "use g instead")]`; the
  `deprecated` lint then warns at every use, in other crates too.
  Removal waits for a SemVer-incompatible release (a new major version,
  or a new minor one before 1.0).
- **Breaking changes**: the Public API step under Verification in
  [references/review.md](references/review.md) lists them.

## Not findings

Items used only under `#[cfg(test)]`, a feature, or a target OS, which
rustc calls dead in builds that leave their callers out; a library's `pub`
items that code outside the repository can reach; `unwrap()` and `panic!`
in tests, examples, and build scripts; items reached by name
(`#[no_mangle]`, `inventory` registrations); fields read only by a
derived `Debug`; and `let _guard = lock();`, which holds the guard until
the scope ends. The full list is in
[references/review.md](references/review.md).

## Verification

Run the project's own entry point before and after a change (the CI
steps, `just`, `cargo xtask`), else `cargo test --workspace --locked`
with the features CI uses, then `cargo fmt --all --check` and
`cargo clippy`. An enum migration's serialized output and `Display` text
must match byte for byte. The review's commands are in
[references/review.md](references/review.md).
