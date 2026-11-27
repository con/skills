# Vuetify practices: review reference

The detail behind [`ts-vuetify-practices`](../SKILL.md) for reviews: the
static searches with their mark, and the worked example the rules come
from. `review-repo-code-quality` reads it with the guide in Step 1.

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

## Worked example

dandi-archive
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
