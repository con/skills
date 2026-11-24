---
name: code-quality-review-ts
version: 0.1.0
description: TypeScript and JavaScript guide for the code-quality review skills — where a Node or browser project states its rules, which tools sweep it (each marked static or needing execution consent, since ESLint, knip and similar configurations are code), checks such as a long or growing string-literal union that belongs in one as-const list, false positives such as package exports and file-system routes, and the commands that verify a change. review-repo-code-quality reads it for TypeScript and JavaScript code, and review-org-code-quality uses its static tools. Use when a review skill tells you to read it, or when asked for a code-quality review of TypeScript or JavaScript code (then run review-repo-code-quality, which loads this guide).
allowed-tools: Read, Skill
user-invocable: true
---

# TypeScript and JavaScript guide for the code-quality reviews

`review-repo-code-quality` holds the review procedure, the report layout,
and the architecture principles that apply to every language; this guide
adds what holds for TypeScript and JavaScript only. That skill reads it in
Step 1 for every repository with such code in scope, and
`review-org-code-quality` uses its **static** tools in Phase 2. The
category prefixes (`ARC`, `DC`, `DUP`, `CON`, `CL`, `NV`) and the
**static** / **consent** marks are defined in `review-repo-code-quality`.

## When invoked directly

This guide is not a review on its own. Asked for a TypeScript or
JavaScript code-quality review, or for this guide by name, run
`review-repo-code-quality` (with `Skill`, or by reading
`../review-repo-code-quality/SKILL.md`); its Step 1 loads this guide.
Limit that review to the TypeScript and JavaScript code only when the
user asked for that; otherwise it covers every language in the
repository, each with its own guide. If `review-repo-code-quality` is not
installed, stop and ask the user to install it; do not review from this
guide alone.

## Recognize

`*.ts`, `*.tsx`, `*.mts`, `*.cts`, `*.js`, `*.jsx`, `*.mjs`, `*.cjs`, and
the `<script>` blocks of `*.vue` and `*.svelte` components. Out of scope
unless the project edits them by hand: `node_modules/`, build output
(`dist/`, `build/`, `.next/`, `coverage/`), minified or vendored bundles,
and generated clients and types (OpenAPI or GraphQL code generation,
`*.d.ts` files a build emits).

## Project rules

Read `package.json` (`engines`, `type`, `main` / `module` / `exports` /
`types` / `bin`, `scripts`, `workspaces`, and how dependencies split
between `dependencies`, `devDependencies`, and `peerDependencies`), the
lock file, which names the package manager (`package-lock.json`,
`pnpm-lock.yaml`, `yarn.lock`, `bun.lock`), every `tsconfig*.json`, and
whichever of these exist: ESLint (`eslint.config.*`, or the older
`.eslintrc*`), Prettier (`.prettierrc*`, `prettier.config.*`), Biome
(`biome.json`, `biome.jsonc`), oxlint (`.oxlintrc.json`), knip
(`knip.json`, `knip.config.*`), dependency-cruiser
(`.dependency-cruiser.*`), test runners (`vitest.config.*`,
`jest.config.*`, `playwright.config.*`), bundlers (`vite.config.*`,
`webpack.config.*`, `rollup.config.*`, `next.config.*`), `.nvmrc` /
`.node-version`, and monorepo files (`pnpm-workspace.yaml`, `turbo.json`,
`nx.json`). Many of these are JavaScript or TypeScript: read them as
text. Running a tool loads them, which executes them.

The supported runtimes bound what may be proposed: `engines.node`, the
tsconfig `target` and `lib`, and the browsers the build targets
(`browserslist`). Note the tsconfig flags that change what is idiomatic:
`strict`, `noUnusedLocals`, `noUnusedParameters`, `verbatimModuleSyntax`,
and `erasableSyntaxOnly` (no `enum`, no `namespace` with run-time code, no
parameter properties, so that the code runs with its types stripped).

## Tools

ESLint, knip, dependency-cruiser, oxlint, and madge all load the
project's configuration by default, and that configuration is code or can
load code (ESLint and knip configurations are modules, oxlint
configurations can name JavaScript plugins, a madge `.madgerc` can point
at a webpack configuration it then executes). Run them with the project's
configuration only with consent; for static use, pass the flags in the
table and run from a scratch directory. Install the tools yourself,
pinned and outside the checkout; never run the copies in the project's
`node_modules` without consent.

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Dead code: files, exports, dependencies | `knip` | consent | `npx knip --reporter compact` from the installed checkout; add `--production` for shipped code only |
| Dead code: locals, parameters | `tsc` | consent | `npx tsc --noEmit --noUnusedLocals --noUnusedParameters -p <tsconfig>` |
| Idiom drift | the project's ESLint, plus `typescript-eslint` (`strict`, `stylistic`), `eslint-plugin-unicorn`, `eslint-plugin-sonarjs` | consent | the project's lint script with those configurations layered on |
| Idiom drift | `oxlint`, your configuration | static | `oxlint -c <scratch>/oxlintrc.json --disable-nested-config -D correctness -D suspicious -W pedantic -W style <paths>` |
| Idiom drift | `biome lint`, your configuration | static | `biome lint --config-path=<scratch>/biome.json --reporter=concise <paths>` |
| Import graph and cycles | `madge` | static from a scratch directory, so that it finds no `.madgerc` | `madge --circular --extensions ts,tsx,js,jsx --ts-config <checkout>/tsconfig.json <paths>` |
| Types | `tsc` | consent | `npx tsc --noEmit -p <tsconfig>` |
| Complexity | `lizard` | static | `lizard -l typescript -l tsx -l javascript -l vue -w <paths>` |
| Tests | the project's runner | consent | see Verification |

Without consent, read the project's ESLint, Biome, or oxlint rule
settings as text and drop the hits for rules it deliberately disables.

## Checks

Each check names the category it usually lands in. A fix that would
change behavior goes under `NV` instead, with the change spelled out.

**Closed sets and constants**

- **A long or growing string-literal union becomes one `as const` list**
  (`ARC`; `CON` when it stays inside one module). A union such as
  `"fast" | "slow" | …` repeated across signatures, or mirrored by a
  hand-written array, object, `switch`, or schema (`z.enum([...])`) for
  run-time checks and UI options, drifts. Define the values once and
  derive the rest: `export const MODES = ["fast", "slow"] as const;`,
  `export type Mode = (typeof MODES)[number];`, and `z.enum(MODES)` where
  values are validated. Reach for `enum` only where the project already
  uses enums and `erasableSyntaxOnly` is off: an `enum` adds a run-time
  object, a string enum does not accept plain strings (`"fast"` is not
  assignable to `Mode.Fast`), and a numeric enum serializes as numbers
  where the union serialized strings. Replacing a union with an `enum` in
  a public signature is an API change (`NV`).
- **The same magic value in several modules** (`CON`): one exported
  constant.
- **Hand-written types that restate a schema** (`ARC`): an interface
  mirroring a zod schema, a JSON Schema, or an OpenAPI or GraphQL type
  becomes `z.infer<typeof schema>` or the generated type.

**Modules and structure**

- **Import cycles** (`ARC`): from `madge --circular`. Barrel files
  (`index.ts` re-exporting a directory) are a common cause, and they can
  defeat tree-shaking.
- **Deep imports into another workspace package's internals** (`ARC`),
  bypassing its `exports`.
- **Effects at module scope** (`ARC`): network calls, `process.env` reads
  into constants, and listeners or timers registered on import.
- **Mixed module systems** (`CL`, or `ARC` across packages): `require` and
  `import` in one package without a reason, or a `"type"` that does not
  match the files' syntax.
- **Default and named exports** mixed against the project's own rule
  (`CL`).
- **One shape declared in several files** (`DUP`): export it once.

**Types and idioms**

- `any`, `as` casts, and non-null assertions (`!`) that hide a type the
  code already knows (`@typescript-eslint/no-explicit-any`,
  `no-unnecessary-type-assertion`, `no-non-null-assertion`) — `CL`, or
  `NV` when the cast hides a real mismatch.
- `var` (`no-var`) and `let` that is never reassigned (`prefer-const`) —
  `CL`; `var` to `let` changes hoisting and scope, so check every use
  first.
- `==` and `!=` (`eqeqeq`) — `NV` unless both sides always have the same
  type.
- Promises: floating promises (`@typescript-eslint/no-floating-promises`),
  `async` functions that never `await` (`require-await`), and `.then`
  chains mixed with `await` in one function — `CL`; rejections nobody
  handles — `NV`.
- `@ts-ignore`, `@ts-expect-error`, and `eslint-disable` comments without
  a reason, or for rules the configuration no longer enables (`DC`).

**Dependencies and configuration**

- dependencies never imported, packages imported but not declared, and
  `devDependencies` imported by shipped code (`DC` or `NV`; knip reports
  all three);
- two libraries doing one job (two date libraries, two HTTP clients)
  (`CON`);
- `@types/*` packages for libraries that ship their own types (`DC`);
- several `tsconfig` files repeating options instead of using `extends`
  (`CON`);
- `package.json` scripts that repeat one another, or that nothing calls
  (`DUP`, `DC`).

**Currency** — check the live sources below on the day of the review and
cite them with the date. Moving a version floor or switching tools is
usually `NV`, a maintainer's decision.

- **Node.js versions.** Compare `engines.node`, `.nvmrc` /
  `.node-version`, and the CI matrix with the release schedule at
  https://nodejs.org/en/about/previous-releases: an end-of-life line
  still supported or tested, or the current LTS line missing.
- **Compiler and syntax.** A `typescript` dependency well behind the
  current release, tsconfig options the installed compiler reports as
  deprecated, and a `target` or `lib` older than every runtime the
  project supports, which makes the build down-level syntax for nothing.
- **Tool formats.** ESLint's `.eslintrc*` format, deprecated since
  ESLint 9 in favour of `eslint.config.*`, and dependencies the registry
  marks deprecated (the package manager warns on install).

## Not findings

What looks dead or wrong in TypeScript or JavaScript but is not. List the
ones you checked under "Not changed (deliberately)".

- Exports reached from outside the source tree: `package.json` `exports`,
  `main`, `module`, `types`, and `bin`, and the published API of a
  library. Having no caller inside the repository does not make them
  dead; removing one is `NV`.
- Files found by convention: framework routes (Next.js `app/` and
  `pages/`, Nuxt `pages/`, SvelteKit `+page.ts`, Remix and React Router
  route modules), configuration files that tools load (`*.config.*`),
  Storybook stories (`*.stories.*`), tests found by glob, service and web
  workers loaded by URL, and dynamic `import()` with a computed path.
- Registrations by decorator or dependency injection (Angular, NestJS),
  and Vue or Svelte components used only from templates.
- Side-effect imports (`import "./polyfills"`, stylesheet imports),
  declaration merging and module augmentation (`declare module`,
  `declare global`), and ambient `*.d.ts` files.
- knip hits in a workspace or entry point that its configuration does not
  describe: correct the analysis before reporting them.

## Verification

- **Install** (consent, in the throwaway checkout): the package manager
  the lock file names, with the lock frozen — `npm ci`,
  `pnpm install --frozen-lockfile`, `yarn install --immutable`.
- **Baseline and after each group** (consent): the project's own scripts —
  `lint`, `typecheck` (else `tsc --noEmit`), `test` (vitest, jest,
  playwright), and `build`, since bundling catches broken imports a type
  check can miss.
- **Static, after any edit**: the static oxlint or biome command above on
  the changed files.
- **Public surface** (consent): emit declarations before and after
  (`tsc --declaration --emitDeclarationOnly --outDir <scratch>`) and diff
  them, or compare the project's API Extractor report if it keeps one.
