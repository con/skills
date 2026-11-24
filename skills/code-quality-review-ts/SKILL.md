---
name: code-quality-review-ts
description: TypeScript and JavaScript guide for review-repo-code-quality and review-org-code-quality — where a project states its rules, its review tools and which need execution consent (ESLint and knip configurations are code), checks such as a long or growing string-literal union that becomes one as-const list, currency, false positives, and verification commands. Not invoked directly. Use when a review skill tells you to read it, or when asked what those reviews check for TypeScript or JavaScript.
allowed-tools: Read
user-invocable: false
---

# TypeScript and JavaScript guide for the code-quality reviews

`review-repo-code-quality` holds the review procedure, the report layout,
and the architecture principles that apply to every language; this guide
adds what holds for TypeScript and JavaScript only. It is not a review on
its own: a review starts from `review-repo-code-quality`, which reads this
guide in Step 1 for every repository with such code in scope, and
`review-org-code-quality` uses its **static** tools before its depth
reviews. The category prefixes (`ARC`, `DC`, `DUP`, `CON`, `CL`, `NV`) and
the **static** / **consent** marks are defined in
`review-repo-code-quality`.

## Recognize

`*.ts`, `*.tsx`, `*.mts`, `*.cts`, `*.js`, `*.jsx`, `*.mjs`, `*.cjs`, and
the `<script>` blocks of `*.vue` and `*.svelte` components. Out of scope
unless the project edits them by hand: `node_modules/`, build output
(`dist/`, `build/`, `.next/`, `coverage/`), minified or vendored bundles,
and generated clients and types (OpenAPI or GraphQL code generation,
`*.d.ts` files a build emits).

## Project rules

Read `package.json` (`engines`, `type`, `main` / `module` / `exports` /
`types` / `bin`, `scripts`, `workspaces`, `packageManager`, and how
dependencies split between `dependencies`, `devDependencies`, and
`peerDependencies`), the lock file, which names the package manager
(`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock` or the older `bun.lockb`), every
`tsconfig*.json` and `jsconfig.json`, and whichever of these exist:
ESLint (`eslint.config.*`, or the older `.eslintrc*`), Prettier
(`.prettierrc*`, `prettier.config.*`), Biome (`biome.json`,
`biome.jsonc`), oxlint (`.oxlintrc.json`, `oxlint.config.*`), knip (`knip.json`,
`knip.config.*`), dependency-cruiser (`.dependency-cruiser.*`), test
runners (`vitest.config.*`, `jest.config.*`, `playwright.config.*`),
bundlers (`vite.config.*`, `webpack.config.*`, `rollup.config.*`,
`next.config.*`), `.nvmrc` / `.node-version`, and monorepo files
(`pnpm-workspace.yaml`, `turbo.json`, `nx.json`). Many of these are
JavaScript or TypeScript: read them as text. Running a tool loads them,
which executes them.

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
at a webpack configuration it then executes, and an `oxlint.config.ts` is itself a module). Run them with the project's
configuration only with consent; for static use, pass the flags in the
table and run from a scratch directory outside the checkout (madge reads
`.madgerc` from the working directory and every parent). Run the
project's own copies by path from the `node_modules/.bin` of the package
that declares them (`<checkout>/node_modules/.bin/tsc …`; in a pnpm
workspace, `<checkout>/packages/<name>/node_modules/.bin/tsc …`), or as
`yarn <tool>` under Yarn Plug'n'Play, which has no `node_modules`. Do
not use `npx`: plain `npx` installs whatever it does not find without
asking (for `tsc`, an unrelated package), and `npx --no` still runs,
without notice, any copy in a parent directory's `node_modules/.bin`,
npm's global prefix, or its `_npx` cache, whatever the version. Ask
before fetching a tool the project does not install
(`review-repo-code-quality` Step 1); compare each project tool's
`--version` with the lock file. Given a directory, oxlint skips what
`.gitignore` lists even with `--no-ignore` (which turns off only
`.eslintignore`), and lizard skips it unless given `--no-gitignore`:
pass oxlint the tracked `*.ts`, `*.tsx`, … files as
`review-repo-code-quality` Step 1 shows.

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Dead code: files, exports, dependencies | `knip` | consent | `<checkout>/node_modules/.bin/knip --reporter compact` from the installed checkout; add `--production --strict` for shipped code only (`--strict` is what lists `devDependencies` that shipped code imports) |
| Dead code: locals, parameters | `tsc` | consent | `<checkout>/node_modules/.bin/tsc --noEmit --noUnusedLocals --noUnusedParameters -p <tsconfig>` |
| Idiom drift | the project's ESLint, plus `typescript-eslint` `strictTypeChecked` and `stylisticTypeChecked` (with `languageOptions.parserOptions.projectService: true`), `eslint-plugin-unicorn`, `eslint-plugin-sonarjs` | consent: typed linting needs the installed dependencies | the project's lint script with those configurations layered on |
| Idiom drift | `oxlint`, your configuration | static | `oxlint -c <scratch>/oxlintrc.json --disable-nested-config -D correctness -D suspicious -W pedantic -W no-var -W eqeqeq -W typescript/no-explicit-any -W typescript/no-non-null-assertion <paths>`; floating promises need `--type-aware`, which reads the project's types (consent) |
| Idiom drift | `biome lint`, your configuration | static | `biome lint --config-path=<scratch>/biome.json --reporter=concise <paths>` |
| Import graph and cycles | `madge`, your tsconfig | static | `madge --circular --extensions ts,tsx,mts,cts,js,jsx,mjs,cjs [--ts-config <scratch>/tsconfig.json] <paths>`, where your `tsconfig.json` holds only an absolute `baseUrl` and the `paths` entries inside the checkout that you read from the project's tsconfig and the files it extends; leave out `--ts-config` where the project maps no paths |
| Cycles through `.mts` / `.cts` files | `dependency-cruiser`, your configuration | static | `depcruise --config <scratch>/dc.json --output-type err <paths>`, with `dc.json` holding `{"forbidden": [{"name": "no-circular", "severity": "error", "from": {}, "to": {"circular": true}}]}`; madge reads no imports from those files |
| Types | `tsc` | consent | `<checkout>/node_modules/.bin/tsc --noEmit -p <tsconfig>` |
| Complexity | `lizard` | static | `lizard -l typescript -l tsx -l javascript -l vue -w <paths>`; it skips `.mts`, `.cts`, and `.svelte` files in a directory, and given one by name parses it with its C reader and reports wrong functions, so leave them out of a file list (say so in Method & limits) |
| Tests | the project's runner | consent | see Verification |

Check what each tsc run covers: `tsc --listFilesOnly -p <tsconfig>` must
list the sources. A solution-style root `tsconfig.json` (`"files": []`
with `references`) compiles nothing, so `tsc --noEmit` on it exits 0
having checked no file. Run each command with `-p` on every referenced
configuration instead. A configuration that itself has `references`
fails under `-p` (TS6305, or TS2307 where it imports the other package
through types that point at build output) until the projects it
references are built, so first run `tsc -b --verbose` in the throwaway
checkout: it checks every project in reference order and writes their
outputs and `.tsbuildinfo` files, but it writes nothing for a referenced
project with errors under `noEmitOnError`, and before TypeScript 5.6 it
skips every project that references one with errors; list the projects
left unchecked in Method & limits. Do not use `tsc -b --noEmit` there (it
fails with TS6310 and checks none of the referencing projects;
TypeScript 5.5 and earlier reject `--noEmit` with `-b` altogether). `tsc
-b` also rejects `--noUnusedLocals` and `--noUnusedParameters`, so the
dead-code sweep always runs per configuration with `-p`. For madge, build its
scratch tsconfig (see its row) from the configuration that holds
`paths`, rather than passing that configuration itself.

## Checks


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
- **The same magic value in several modules** (`ARC`; `CON` when it stays
  inside one module): one exported constant.
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
  into constants, and listeners or timers registered on import. Moving
  them into a function the entry point calls changes when they happen;
  trace every importer, tests included.
- **Mixed module systems** (`NV` unless every importer is traced; `ARC`
  across packages): `require` and `import` in one package without a
  reason, or a `"type"` that does not match the files' syntax. Converting
  moves a dependency's evaluation ahead of the module body (`import`
  declarations are hoisted) and makes the file strict, and a `"type"`
  change alters how Node and consumers load every `.js` file.
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
- Promises: a floating promise (`@typescript-eslint/no-floating-promises`)
  is `CL` when the fix marks it `void` deliberately, and `NV` when the fix
  awaits it or adds a handler. `async` functions that never `await`
  (`@typescript-eslint/require-await`) and `.then` chains mixed with
  `await` are `NV` unless every caller is traced: dropping `async` turns
  rejections into synchronous throws and returns a non-promise, and an
  `await` inside `try` catches rejections that a returned `.then` chain
  did not.
- `@ts-ignore`, `@ts-expect-error`, and `eslint-disable` comments without
  a reason, or for rules the configuration no longer enables (`DC`).

**Dependencies and configuration**

- dependencies never imported, packages imported but not declared, and
  `devDependencies` imported by shipped code (`DC` or `NV`; knip reports
  the first two, and the third with `--production --strict`);
- `@types/*` packages for libraries that ship their own types (`DC`);
- several `tsconfig` files repeating options instead of using `extends`
  (`CON`);
- `package.json` scripts that repeat one another, or that nothing calls
  (`DUP`, `DC`; see Not findings for the scripts npm runs by name).

**Currency** (reported as `review-repo-code-quality` Step 2 says; read the
live sources each item names, and run every `npm view` from a scratch
directory: a project's `.npmrc` can redirect the registry and send its
token there)

- **Node.js versions.** Compare `engines.node`, `.nvmrc` /
  `.node-version`, and the CI matrix with the release schedule at
  https://nodejs.org/en/about/previous-releases: an end-of-life line
  still supported or tested, or the current LTS line missing.
- **Compiler and syntax.** A `typescript` dependency behind the newest
  version the project's tooling accepts: compare
  `npm view typescript dist-tags` with the `typescript` peer range of the
  linter and tool versions the lock file pins
  (`npm view typescript-eslint@<locked version> peerDependencies`); where
  only a newer release of such a tool accepts a newer compiler, say both
  must move together. Check deprecated compiler options against the
  newest compiler, not only the project's: an `ignoreDeprecations` key in
  any tsconfig (it silences them, and is itself the finding), the options
  the project's compiler reports (consent:
  `<checkout>/node_modules/.bin/tsc --noEmit -p <tsconfig>`), and those a newer major
  deprecates or removes (its release notes, such as https://aka.ms/ts6).
  Also a
  `target` older than every runtime the project supports, which makes the
  build down-level syntax for nothing (`lib` only decides which built-in
  APIs type-check). Raising `target` to ES2022 or later also turns on
  `useDefineForClassFields` unless the tsconfig sets it, which changes how
  class fields initialize: `NV` unless the option is pinned to its current
  value.
- **Tool formats and deprecations.** ESLint's `.eslintrc*` format,
  deprecated in ESLint 9 and no longer read by ESLint 10
  (`npm view eslint dist-tags`); dependencies the registry marks
  deprecated (`npm view <package>@<version> deprecated`).

## Not findings

- Exports reached from outside the source tree: `package.json` `exports`,
  `main`, `module`, `types`, and `bin`, and the published API of a
  library. Having no caller inside the repository does not make them
  dead; removing one is `NV`.
- Files found by convention: framework routes (Next.js `app/` and
  `pages/`, Nuxt `pages/`, SvelteKit `+page.ts`, Remix and React Router
  route modules), configuration files that tools load (`*.config.*`),
  Storybook stories (`*.stories.*`), tests found by glob, service and web
  workers loaded by URL, and dynamic `import()` with a computed path.
- Exports a framework reads by name from such files: Next.js `metadata`,
  `generateMetadata`, `generateStaticParams`, `revalidate`, `dynamic`,
  `runtime`, `getServerSideProps`; React Router and Remix `loader`,
  `action`, `meta`, `links`; SvelteKit `load`, `prerender`, `ssr`, `csr`,
  `actions`, `GET` / `POST`; Astro `getStaticPaths`; and the default
  export those files must have. Also modules loaded by glob
  (`import.meta.glob`, webpack `require.context`).
- `package.json` scripts the package manager runs by name: lifecycle
  scripts (`prepare`, `prepublishOnly`, `prepack`, `postpack`,
  `preinstall`, `install`, `postinstall`, `version`, …) and the
  `pre<name>` / `post<name>` hooks of scripts that are run (npm, Bun, and
  Yarn 1 run them; pnpm only when `enable-pre-post-scripts` is on, the
  default from pnpm 9; Yarn 2 and later do not: where they do not run, an
  uncalled one is dead), plus scripts
  that CI, documentation, other scripts, or a task runner (turbo, nx)
  invoke.
- Registrations by decorator or dependency injection (Angular, NestJS),
  and Vue or Svelte components used only from templates.
- Side-effect imports (`import "./polyfills"`, stylesheet imports),
  declaration merging and module augmentation (`declare module`,
  `declare global`), and ambient `*.d.ts` files.
- knip hits in a workspace or entry point that its configuration does not
  describe: correct the analysis before reporting them.

## Verification

- **Install** (consent, in the throwaway checkout): the package manager
  the lock file names, at the version `packageManager` names, with the
  lock frozen — `npm ci`, `pnpm install --frozen-lockfile`,
  `yarn install --immutable` for Yarn 2 and later (a `yarn.lock` with a
  top-level `__metadata:` key), else `yarn install --frozen-lockfile` for
  Yarn 1 (`# yarn lockfile v1` on its second line; Yarn 1 silently
  ignores `--immutable` and rewrites an out-of-date lock),
  `bun install --frozen-lockfile`.
- **Baseline and after each group** (consent): the project's own scripts —
  `lint`, `typecheck` (else the `tsc` runs under Tools; plain `tsc -b`
  without `outDir` or `noEmit` writes `.js` files next to the sources,
  tests included, so run it only in the throwaway checkout), `test`
  (vitest, jest, playwright), and `build`, since bundling catches broken
  imports a type check can miss.
- **Static, after any edit**: the static oxlint or biome command above on
  the changed files.
- **Public surface** (consent): emit declarations before and after with
  `tsc -p <the configuration that builds the package> --declaration
  --emitDeclarationOnly --noEmit false --outDir <scratch>/api-before`
  (then `api-after`), check that each directory holds the package's
  `.d.ts` files — a configuration with `"noEmit": true` or a solution
  file writes nothing and still exits 0 — and diff them; or compare the
  `.d.ts` files, or the API Extractor report, the project's own build
  writes.
