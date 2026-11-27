---
name: ts-practices
description: TypeScript and JavaScript practices — the house's preferences (one as-const list for a growing string-literal union, no effects at module scope, one module system without import cycles, no casts that hide a known type, no floating promises, supported Node.js lines and compiler), public surface and deprecation, false positives, and verification, with the review tools and detailed checks in references/review.md. Framework guides build on it (ts-vue-practices for Vue 3, ts-vuetify-practices for Vuetify 3). Use when writing, changing, or reviewing TypeScript or JavaScript, including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# TypeScript and JavaScript practices

The house's practices for TypeScript and JavaScript code, for three kinds
of work: writing or changing it, reviewing a pull request, and the
code-quality reviews. Read `general-practices` first: it says how to weigh
these preferences against the project's own rules and your own judgment,
and defines the marks and categories used here.
[references/review.md](references/review.md) holds what a review needs
beyond them: the tools with their **static** / **consent** marks, the
detailed checks with their categories and pitfalls, currency sources, and
verification commands.

It is written for frontends built with Vite, small Node scripts, and
JavaScript or TypeScript GitHub Actions. What a framework adds lives in
its own guide, read together with this one: `ts-vue-practices` for Vue 3,
and `ts-vuetify-practices` for Vuetify 3 on top of it. Other frameworks
and runtimes (React, Angular, Svelte, server frameworks, Deno, Bun) and
monorepo tools are left out: check their conventions before reporting
there.

## Recognize

`*.ts`, `*.tsx`, `*.mts`, `*.cts`, `*.js`, `*.jsx`, `*.mjs`, `*.cjs`, and
the `<script>` blocks of `*.vue` components (`ts-vue-practices` covers the
rest of a component). Out of scope unless the
project edits them by hand: `node_modules/`, build output (`dist/`,
`build/`, `coverage/`), minified or vendored bundles, and generated
clients and types (OpenAPI code generation, `*.d.ts` files a build emits).

## Project rules

Read `package.json`, the lock file, every `tsconfig*.json`, and the lint,
test, and bundler configurations, as text: many are code. `engines.node`,
the tsconfig `target` and `lib`, and `browserslist` bound what may be
proposed; `strict`, `verbatimModuleSyntax`, and `erasableSyntaxOnly` (no
`enum`, run-time `namespace`, or parameter properties) change what is
idiomatic.

## Preferences

- **Closed sets**: a long or growing string-literal union becomes one
  `as const` list with a derived type,
  `const MODES = ["fast", "slow"] as const;` and
  `type Mode = (typeof MODES)[number];` (`z.enum(MODES)` where validated);
  `enum` only where the project uses enums and `erasableSyntaxOnly` is off.
- **One source of truth**: a value or shape used in several modules is
  exported once; a type restating a schema is inferred or generated from
  it (`z.infer<typeof schema>`).
- **Effects at the edges**: no network calls, `process.env` reads,
  listeners, or timers at module scope; moving one changes when it runs,
  so trace its importers.
- **Modules**: no import cycles (barrel `index.ts` files often cause
  them); one module system per package, matching its `"type"`. Converting
  `require` to `import` hoists evaluation and makes the file strict.
- **Types**: no `any`, `as`, or `!` hiding a type the code knows; one
  hiding a real mismatch needs verification. No `@ts-ignore`,
  `@ts-expect-error`, or `eslint-disable` without a reason.
- **Bindings and equality**: `const` unless reassigned, never `var`
  (switching to `let` changes hoisting and scope), and `===`; replacing
  `==` keeps behavior only where both sides always share a type.
- **Promises**: awaited, handled, or deliberately `void`; dropping
  `async` from a function that never awaits turns rejections into
  synchronous throws.
- **Dependencies**: each import declared, none unused, no
  `devDependencies` in shipped code, and no `@types/*` for a library that
  ships its own types.
- **Runtimes and compiler**: no end-of-life Node.js line supported or
  tested, the current LTS line among them, and a `target` no older than
  the oldest runtime; ES2022 or later turns on `useDefineForClassFields`
  unless the tsconfig sets it.

## Public surface and deprecation

- **Internals**: once `package.json` sets `exports`, a path it does not
  list cannot be imported from the package, and a module member that is
  not exported is private; in a library, adding to `exports` or exporting
  a member widens the API.
- **Deprecating** an export, option, or prop: keep it working and mark it
  `/** @deprecated Use … instead. */`; editors strike its uses through,
  and `@typescript-eslint/no-deprecated` (typed linting, consent) reports
  them. Where callers are not type-checked, also warn once at run time.
- **Breaking changes**: the Public surface step under Verification in
  [references/review.md](references/review.md) lists them.

## Not findings

Exports reached from outside the source tree (`package.json` `exports`,
`main`, `types`, `bin`, a library's published API), files found by
convention (routes, `*.config.*`, test globs, workers, `import.meta.glob`,
modules an HTML page loads),
scripts the package manager runs by name, side-effect imports,
`declare module` / `declare global`, and ambient `*.d.ts` files. The full
list is in [references/review.md](references/review.md).

## Verification

Install with the package manager the lock file names, lock frozen, then
run the project's own `lint`, `typecheck`, `test`, and `build` scripts
before and after a change; the build catches broken imports a type check
misses. Run tools by path (`node_modules/.bin/tsc`), not `npx`, which
installs what it lacks. The review's commands are in
[references/review.md](references/review.md).
