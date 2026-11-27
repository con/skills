---
name: ts-vue-practices
description: Vue 3 practices on top of ts-practices — single-file components (script setup, props, emits, v-model, templates), composables, vue-router, the review tools that read .vue files and which need execution consent, false positives such as components used only from templates, currency, and verification. Use when writing, changing, or reviewing Vue components or a Vue application, including in a pull-request review or a code-quality review (review-repo-code-quality and review-org-code-quality read it); read ts-practices with it, and ts-vuetify-practices where the project uses Vuetify.
allowed-tools: Read
user-invocable: false
---

# Vue practices

What Vue 3 adds to `ts-practices`, for three kinds of work: writing or
changing Vue components, reviewing a pull request, and the code-quality
reviews (`review-repo-code-quality` reads this guide in Step 1 with
`ts-practices`; `review-org-code-quality` runs its **static** tools). Read
`general-practices` and `ts-practices` first: everything in `ts-practices`
holds inside `<script>` blocks too, this guide only adds to it, and
`general-practices` says how to weigh the guides and defines the
**static** / **consent** marks, the category prefixes (`ARC`, `DC`, `DUP`,
`CON`, `CL`, `NV`), and the architecture principles.

It is written for Vue 3 single-page applications built with Vite, with
the Composition API in `<script setup>` and vue-router. Vue 2 and the
Options API appear only where moving off them is the finding; Nuxt and
server-side rendering are left out: check their conventions before
reporting there. Vuetify has its own guide, `ts-vuetify-practices`.

## Recognize

`*.vue` single-file components, in a project whose `package.json`
depends on `vue`.

## Project rules

Besides what `ts-practices` lists, read `vite.config.*`
(`@vitejs/plugin-vue`, and `resolve.alias`, which must agree with the
tsconfig `paths`), the tsconfig that type-checks the components (in a
create-vue project, `tsconfig.app.json`, referenced from a solution-style
`tsconfig.json`), the `eslint-plugin-vue` configuration the ESLint setup
extends (`flat/essential`, `flat/strongly-recommended`, or
`flat/recommended`), and the router definition (route names, and the
params each path requires). These are code: read them as text.

The `vue` version in the lock file bounds what may be proposed:
`defineModel` needs 3.4 (3.3 marks it experimental), and a destructured
`defineProps` stays reactive, and `useTemplateRef` exists, only from 3.5.

## Tools

These add to the `ts-practices` table.

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Types, and dead locals in components | `vue-tsc` | consent | `<checkout>/node_modules/.bin/vue-tsc` in place of `tsc` in each `ts-practices` `tsc` command, with the same flags (`-b` included): plain `tsc` does not read `.vue` files |
| Idiom drift, templates included | the project's ESLint with `eslint-plugin-vue` `flat/recommended` layered on | consent | as the `ts-practices` ESLint row |
| Idiom drift | `oxlint`, your configuration | static | the `ts-practices` command with the tracked `*.vue` files added to `<paths>`: oxlint 1.95 lints their `<script>` blocks, not their templates |
| Complexity | `lizard` | static | add `-l vue` to the `ts-practices` lizard command |

madge cannot read `.vue` files (given `vue` in `--extensions`, madge 8.0.0
stops with a SyntaxError), so cycles through components go unseen: say
so in Method & limits. The template checks below need `eslint-plugin-vue`,
and so consent; without it, search the templates
(`git -C <checkout> grep -n 'v-for=' -- '*.vue'`) and read the hits.

## Checks

**Closed sets and constants**

- **A prop or emit that takes one of a fixed set of strings** (`ARC`;
  `CON` inside one component): type it with the union `ts-practices`
  derives from one `as const` list (`defineProps<{ mode: Mode }>()`), not
  a `validator` array or a template `v-if` chain that restates the
  values. A run-time validator checks against the same list.

**Components**

- **Reactivity lost** (`NV`): destructuring `defineProps()` before Vue
  3.5, or a `reactive()` object at any version, into plain variables, or
  passing `props.x` where a composable expects a ref or getter
  (`vue/no-setup-props-reactivity-loss`); use `toRefs`, `toRef`, or
  `() => props.x`.
- **A prop mutated in the child** (`vue/no-mutating-props`): a bug, `NV`
  to fix; emit an update, or use `defineModel` (3.4).
- **`v-for` without a `:key`** (`vue/require-v-for-key`), and **`v-if` on
  the element that has `v-for`** (`vue/no-use-v-if-with-v-for`; in Vue 3
  `v-if` is evaluated first, so it cannot see the loop variable): `NV`.
- **`v-html`** with content the application did not produce
  (`vue/no-v-html`): a security finding, `NV`.
- **A `watch` or `watchEffect` that only sets another ref** from reactive
  sources becomes a `computed` (`NV`: a watcher's value lags until it
  runs, and other code may write the ref).
- **Logic repeated across components** (`DUP`): one composable
  (`use…()`); state shared through module-level refs in some places and
  a store in others (`CON`): one pattern, the one the project uses most.
- **Options API and `<script setup>` mixed** against the project's own
  rule (`CL`), and logic in template expressions that a `computed` would
  name (`CL`).

**Routing**

- **Navigation in a click handler** (`router.push` in `@click`) where a
  `RouterLink`, or a component's `to` prop, gives a real link that
  right-click, middle-click, and ctrl/cmd-click can open (`NV`: the
  element becomes an anchor). Keep `router.push` for navigation that is
  not a click on a thing: after a form submit, a search, or a query
  sync.

**Public surface and deprecation**

- An application's public surface is its routes: the paths and query
  parameters people bookmark and link to. Renaming a path keeps the old
  one as a `redirect` in the router (`NV` without it). In a component
  library, props, emits, and slots are the API, and a deprecated prop
  keeps working with `/** @deprecated */` on its type, as in
  `ts-practices`.

**Currency** (reported as `review-repo-code-quality` Step 2 says; read
the live sources)

- Vue 2 is past end of life (https://v2.vuejs.org/eol/): a Vue 2
  dependency is the finding, and its migration `NV`.
- Vue CLI (`@vue/cli-service`) is in maintenance mode
  (https://cli.vuejs.org/), with Vite through create-vue
  (https://github.com/vuejs/create-vue) as the recommended setup, and
  Pinia (https://pinia.vuejs.org/) replaces Vuex as the official store.
  Each move is `NV`.

## Not findings

- Components used only from templates, registered globally
  (`app.component(…)`), or auto-imported (`unplugin-vue-components`
  writes their names to `components.d.ts`): `tsc` and knip can report
  them unused.
- Props, emits, and refs used only in the template, and members a parent
  reaches through a template ref and `defineExpose`.
- Route components loaded by `() => import(…)`, or found by file-system
  routing (`unplugin-vue-router`).

## Verification

- **Types** (consent): the `vue-tsc` runs above; create-vue projects run
  them as their `type-check` script (`vue-tsc --build`).
- **Behavior** (consent): the project's component tests (Vitest with
  `@vue/test-utils`) and end-to-end tests (Playwright). For a change to a
  template or to routing, also open the page in a dev server or deploy
  preview: links open in a new tab, the buttons inside them do not
  navigate, and browser Back works.
