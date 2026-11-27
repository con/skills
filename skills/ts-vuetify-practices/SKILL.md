---
name: ts-vuetify-practices
description: Vuetify 3 practices on top of ts-vue-practices — prefer a component's own props (to, href, active) and Vuetify's utility classes over custom CSS, wrapper links, and click handlers that navigate; a named route in a Vuetify :to passes its own params; static searches, false positives, and checks in the browser. Use when writing, changing, or reviewing Vue components that use Vuetify — especially when adding navigation, click handling, layout or spacing, or before adding a style scoped block, a wrapper a or router-link, or a click handler that navigates — including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# Vuetify practices

What Vuetify 3 adds to `ts-vue-practices` and `ts-practices`, for three
kinds of work: writing or changing components, reviewing a pull request,
and the code-quality reviews (`review-repo-code-quality` reads this guide
in Step 1 with the other two). Read `general-practices` and those two
first: `general-practices` says how to weigh the guides and defines the
**static** / **consent** marks and the category prefixes (`ARC`, `DC`,
`DUP`, `CON`, `CL`, `NV`).

Vuetify components already cover most of what a feature needs:
navigation, active state, spacing, colors, elevation, and alignment.
Reach for the component's own props and Vuetify's utility classes first.
Custom `<style scoped>` blocks, wrapper elements, and hand-written click
handlers are a last resort: they duplicate framework behavior, drift
from the theme, and break when Vuetify's internal DOM changes. Adding a
`<style>` block to a component is a signal to stop and look for the prop.

It is written for Vuetify 3 with vue-router 4, and the rules come from
the review history of dandi-archive's web frontend. Vuetify 2 is left
out.

## Recognize

`*.vue` files that use Vuetify components (`v-…` tags), in a project
whose `package.json` depends on `vuetify`.

## Project rules

The `vuetify` version in the lock file; the `createVuetify` call (its
`theme`, `defaults`, and `aliases`: a default set there is a prop on
every instance); and the router definition, for the params each named
route's path requires.

## Tools

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Custom CSS, wrapper links, navigating handlers, named routes | `git grep` | static | the searches below, on the tracked files |

```sh
git -C <checkout> grep -c '<style' -- '*.vue'        # components with a style block
git -C <checkout> grep -nF ':deep(.v-' -- '*.vue'     # overrides of Vuetify internals
git -C <checkout> grep -nE 'window\.open\(|location\.(href|assign|replace)|router\.push\(' -- '*.vue' '*.ts'
git -C <checkout> grep -nE '@click\.stop([^.a-z]|$)' -- '*.vue'   # .stop without .prevent
git -C <checkout> grep -nE "name: *['\"]" -- '*.vue' '*.ts'      # named routes: check their params
```

Each hit is a candidate, not a finding: read the component around it.

## Checks

- **Navigation goes through `to` or `href`, not a click handler** (`NV`:
  the element becomes a real link). `v-list-item`, `v-btn`, `v-card`,
  `v-chip`, `v-tab`, and `v-breadcrumbs-item` take both: `to` for a
  router link, `href` for a plain one. Setting one makes the whole
  component an anchor, so right-click "Open link in new tab",
  middle-click, and ctrl/cmd-click work. `window.open(url, "_self")`,
  assigning a location, or an `@click` that calls `router.push` produce
  an element the browser cannot treat as a link. Where a row links to a
  file in some cases and to a route in others, bind both and pass
  `undefined` for the one that does not apply, rather than branching the
  element with `v-if`.
- **No `<a>` or `<router-link>` nested inside a component that can be
  one** (`NV`). A link around the label makes only the label clickable,
  and leads to a stretched `::after` overlay and `z-index` juggling to
  cover the rest of the row: put the link on the component.
- **Interactive children of a linked component use `@click.stop.prevent`**
  (a bug with `.stop` alone; `NV` to fix): `.stop` ends the handler
  chain, but the anchor still follows the link. Buttons, menu
  activators, and checkboxes inside a `to` or `href` row all need both,
  including an activator bound with `v-bind` from a `v-menu` or
  `v-tooltip` slot, which takes a bare `@click.stop.prevent`.
- **`:active="false"` where a link should not look selected** (`CL` when
  the rendering is unchanged; check it in the browser): once `to` is set,
  Vuetify derives `active` from route matching. `v-list-item`, `v-btn`,
  `v-tab`, and `v-breadcrumbs-item` have the prop; use it rather than CSS
  that overrides the active classes.
- **Spacing, color, and alignment from utility classes** (`CL`, or `NV`
  when the rendering changes): `ma-*`, `pa-*`, `text-*`, `bg-*`,
  `d-flex`, `align-*`, `justify-*`, `text-truncate`. CSS is for what
  Vuetify has no prop or class for, with a comment naming it. A `:deep()`
  selector into a Vuetify internal class (`.v-list-item__append`, …)
  usually means a prop was missed.
- **A named route in a Vuetify `to` passes its own `params`** (a bug;
  `NV` to fix). Given `{ name, query }` without `params`, vue-router fills
  the params from the current route. A plain `<router-link>` gets away
  with that, but a Vuetify component can resolve its link again while it
  unmounts, after the route has changed: `v-list-item` uses its resolved
  href as its id in the parent `v-list` and unregisters that id in
  `onBeforeUnmount`. If the new route lacks a param the target path
  needs, vue-router throws `Missing required param "…"` in the middle of
  the page change. Helpers that build routes for Vuetify components take
  the params as arguments, and moving a `<router-link>`'s `to` onto a
  Vuetify component is not a markup-only change.
- **A pattern already in the file is checked before it is spread**: the
  existing use may be the bug, as in the worked example below.

**Worked example.** dandi-archive
[#2926](https://github.com/dandi/dandi-archive/pull/2926) made
file-browser rows behave as links. Its first version nested an `<a>` or
`<router-link>` in each `v-list-item` title, with a stretched overlay,
`z-index` rules, and an `openItem` handler calling
`window.open(…, "_self")`. The rewrite put the link on the row, for 12
lines added and 70 removed:

```vue
<v-list-item
  color="primary"
  :href="item.asset ? inlineURI(item.asset.asset_id) : undefined"
  :to="item.asset ? undefined : locationRoute(item.path)"
  :active="false"
>
  <v-list-item-title :title="item.name">{{ item.name }}</v-list-item-title>
  <template #append>
    <v-btn icon variant="text" @click.stop.prevent="setItemToDelete(item)">…</v-btn>
    <v-btn v-bind="openWithProps" @click.stop.prevent>Open With</v-btn>
  </template>
</v-list-item>
```

As merged, it broke browser Back
([#3004](https://github.com/dandi/dandi-archive/issues/3004)):
`locationRoute()` returned `{ name: 'fileBrowser', query }`, and the
`fileBrowser` path needs a `version` that the landing route
`/dandiset/:identifier/:version?` may lack. The old `..` row already used
that helper on a `v-list-item`, but only inside a subfolder; the rewrite
put it on every row. The fix
([#3008](https://github.com/dandi/dandi-archive/pull/3008)) passes the
params:

```ts
function locationRoute(newLocation: string): RouteLocationRaw {
  return {
    name: 'fileBrowser',
    params: { identifier: props.identifier, version: props.version },
    query: { location: newLocation, page: '1' },
  } as RouteLocationRaw;
}
```

**Public surface and deprecation**

- Vuetify reports its own deprecations in a development build's console,
  through Vue's `warn`: `[Vuetify UPGRADE] '…' is deprecated, use '…'
  instead.` Each one is a currency item (`CL` where the replacement
  renders the same, else `NV`).

## Not findings

- `router.push` for navigation that is not a click on a thing:
  redirecting after a form submit, reacting to a search, syncing query
  parameters.
- CSS for something Vuetify has no prop or utility class for, with a
  comment saying what.
- A component with both `:href` and `:to` bound, one of them `undefined`.

## Verification

For a linked component, in a dev server or deploy preview:

- right-click "Open link in new tab", middle-click, and ctrl/cmd-click
  open the target, and every button inside the component works and does
  not navigate;
- leave the page with browser Back to a URL whose route lacks one of the
  target's params (in dandi-archive, a landing URL with no version, such
  as `/dandiset/000003`), with a single Back and with a jump of two or
  more history entries from a nested state, and check that the console
  shows no `Missing required param`;
- an end-to-end test covers the page, as dandi-archive's
  `e2e/tests/fileBrowserPage.spec.ts` does for its file browser.

These rules come from dandi-archive's `vuetify-component-api` skill, by
the same author, adapted so that other projects can install them.
