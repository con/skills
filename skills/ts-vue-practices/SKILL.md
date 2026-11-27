---
name: ts-vue-practices
description: Vue 3 practices on top of ts-practices — the house's preferences (script setup, typed props and emits from one as-const list, no lost reactivity, computed over watchers that copy, keyed v-for, links over navigating click handlers, one composable for repeated logic), public surface and deprecation, false positives, and verification, with the review tools and detailed checks in references/review.md. Use when writing, changing, or reviewing Vue components or a Vue application, including in a pull-request review or a code-quality review; read ts-practices with it, and ts-vuetify-practices where the project uses Vuetify.
allowed-tools: Read
user-invocable: false
---

# Vue practices

What Vue 3 adds to `ts-practices`, for three kinds of work: writing or
changing Vue code, reviewing a pull request, and the code-quality
reviews. Read `general-practices` and `ts-practices` first: everything in
`ts-practices` holds inside `<script>` blocks too, and `general-practices`
says how to weigh the guides and defines the marks and categories used
here. [references/review.md](references/review.md) holds what a review
needs beyond them: the tools with their **static** / **consent** marks,
the detailed checks with their categories and pitfalls, currency
sources, and verification commands.

It is written for Vue 3 single-page applications built with Vite, with
the Composition API in `<script setup>` and vue-router. Vue 2 and the
Options API appear only where moving off them is the finding; Nuxt and
server-side rendering are left out: check their conventions before
reporting there. Vuetify has its own guide, `ts-vuetify-practices`.

## Recognize

`*.vue` single-file components, in a project whose `package.json`
depends on `vue`.

## Project rules

Besides what `ts-practices` lists, read `vite.config.*`, the tsconfig
`vue-tsc` uses, the `eslint-plugin-vue` configuration, and the router.
The `vue` version in the lock file bounds proposals: `defineModel` needs
3.4; reactive props destructure and `useTemplateRef`, 3.5.

## Preferences

- **`<script setup>`** with the Composition API, not mixed with the
  Options API against the project's rule.
- **Closed sets**: a prop or emit that takes one of a fixed set of
  strings is typed from one `as const` list, not a `validator` array or a
  `v-if` chain restating the values.
- **No lost reactivity**: `toRefs`, `toRef`, or `() => props.x`, not
  `defineProps()` (before 3.5) or `reactive()` destructured into plain
  variables. A child never mutates a prop: it emits an update, or uses
  `defineModel`.
- **Derived state** is a `computed`, not a watcher that only sets another
  ref, nor logic in a template expression.
- **Templates**: a `:key` on every `v-for`, no `v-if` on the same element,
  and `v-html` only for content the application produced.
- **One composable** (`use…()`) for logic repeated across components, and
  one pattern for shared state, the one the project uses most.
- **Links over click handlers**: a `RouterLink` or a component's `to`
  prop, which middle- and ctrl/cmd-click open, not `router.push` in
  `@click`; `router.push` is for navigation after a submit, a search, or
  a query sync.

## Public surface and deprecation

- An application's public surface is its routes: the paths and query
  parameters people bookmark and link to. Renaming a path keeps the old
  one as a `redirect` in the router (`NV` without it). In a component
  library, props, emits, and slots are the API, and a deprecated prop
  keeps working with `/** @deprecated */` on its type, as in
  `ts-practices`.

## Not findings

Components used only from templates, registered globally, or
auto-imported, which `tsc` and knip can report unused; props, emits, and
refs used only in the template or through `defineExpose`; and lazy or
file-system-routed route components. The full list is in
[references/review.md](references/review.md).

## Verification

Type-check with `vue-tsc` (plain `tsc` does not read `.vue` files), and
run the component and end-to-end tests (Vitest, Playwright). After a
template or routing change, open the page in a dev server or deploy
preview: links open in a new tab, and Back works. The review's commands
are in [references/review.md](references/review.md).
