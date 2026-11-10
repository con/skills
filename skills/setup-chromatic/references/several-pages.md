# When the app has several pages

Two shapes count as several pages, and they differ in one place.

- **Several HTML entries**, a Vite multi-page app: `index.html`, `about.html`, `help/index.html`, each with its own `<script type="module">`.
  Every entry is a page here: a line in `configs/pages.ts`, a story file under `stories/pages/`, and its states in `tests/chromatic/`.
- **Routes inside one `index.html`**, a hash or history router.
  One HTML entry, so the Vite config is untouched, but the suite keeps the same list: `configs/pages.ts` with `path` as the route (`/#/about`, or `/about` for a history router) and no `file` column, looped by `pages.chromatic.test.ts` for the states every route has, plus a `<route>.chromatic.test.ts` for a route with states of its own; titles lead with the route's name.
  On the story side there are two cases.
  When `index.html` already carries each route's markup, `stories/App.stories.ts` applies a route by hand in the callback, as it does any page state.
  When a router renders into an empty mount point, `buildPage` strips the script that would have rendered it; give each route a `stories/pages/<Route>.stories.ts` whose markup is built by hand, as `Component.stories.ts` does.
  Keep Vite's default `appType: "spa"` for this shape (a history router needs every route answered with `index.html`, and the deployed host already does that if the app works there); the `mpa` setting below is for HTML entries only.

Everything below is about the first shape.
The reference repos are all one-page apps, so the templates are the reference here.

## The list of pages

`configs/pages.ts` (template under `templates/configs/`) names every page once: the HTML file Vite builds, the URL the suite visits, the heading it expects.
The Vite config builds its entry list from it and `pages.chromatic.test.ts` loops over it, so adding a page is one line plus a story file.
The config of a several-page app already lists its entries; replace that list with the one built from `PAGES`, so a page is named once, and keep whatever else the `build` block holds (`outDir`, `emptyOutDir`).

```ts
// configs/vite.config.ts
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
// With the extension: Vite's `configLoader: 'native'`, its planned default, needs it, and Vite 8
// already warns on every start without it. tsc accepts it with allowImportingTsExtensions (below).
import { PAGES } from "./pages.ts";

export default defineConfig({
  // The dev server serves any HTML file under root; the build contains only these entries, so a
  // page left out works locally and is missing from preview and production.
  build: {
    rollupOptions: {
      input: Object.fromEntries(
        PAGES.map((p) => [p.name.toLowerCase(), fileURLToPath(new URL(`../${p.file}`, import.meta.url))]),
      ),
    },
  },
  // Without this, Vite's default "spa" answers a URL it cannot match with index.html, and a snapshot
  // of a missing page would silently capture the index page instead of failing. It changes
  // `npm run dev` the same way (an unmatched URL now 404s); say so in the hand-over.
  appType: "mpa",
  // ...
});
```

Add `allowImportingTsExtensions: true` to the tsconfig that covers `configs/` (legal there, since it is `noEmit`); the tests' `../../configs/pages` import may stay extensionless, since Playwright compiles tests itself.
Absolute entry paths work on Vite 7 (`build.rollupOptions.input`) and Vite 8.
On Vite 8 `build.rollupOptions` is a deprecated alias of `build.rolldownOptions`, and a top-level `input` of root-relative paths is the new form.
The Vite docs' own example uses `resolve(import.meta.dirname, "nested/index.html")`.
When `index.html` lives under `src/` (`root: "src"`), the entries are still absolute paths, and a page's URL and output path are relative to that root (`src/help/index.html` is served at `/help/` and built to `dist/help/index.html`).
The entry's key names only the page's JS chunk (`assets/help-<hash>.js`); the built HTML keeps its path (`dist/help/index.html`), so the `p.name.toLowerCase()` keys are a convenience, not a URL.

## Which URL a test visits

Vite's dev and preview servers resolve page URLs the same way, with no redirects:

| Layout             | Served at                     | Not served at                                            |
| ------------------ | ----------------------------- | -------------------------------------------------------- |
| `about.html`       | `/about.html`, `/about`       | `/about/`                                                |
| `help/index.html`  | `/help/`, `/help/index.html`  | `/help` (404 under `mpa`; `index.html` under `spa`)      |

Static hosts differ on the other forms (GitHub Pages serves `about.html` at `/about` but redirects `/help` to `/help/`; Cloudflare Pages redirects `/about.html` to `/about`; Vercel's defaults 404 `/about`).
So `path` in `configs/pages.ts` is `/help/` for a `help/index.html` entry and `/about.html` for a root-level file, the forms Vite and every host serve (at most through a redirect that still lands on the page), and never `/about` or `/help`.
When the layout is yours to choose, use `help/index.html` entries with `/help/` URLs, the one form nothing redirects.
The app's own `<a href>` links use the same forms, since Vite rewrites asset references at build time but never link targets.
If the app deploys under a sub-path (`base: "/<repo>/"` for a GitHub Pages project site), root-absolute links break there: write them relative or from `import.meta.env.BASE_URL`.
The suite then needs the same care, because Playwright resolves `page.goto` with `new URL(path, baseURL)` and a root-absolute path drops the sub-path: make `path` relative (`about.html`, `help/`) and end the Playwright `baseURL` with the sub-path and a slash (`http://localhost:4173/<repo>/`).
The reference repos avoid all of this with `base: "./"` or a custom domain.

## Stories, one file per page

Copy `templates/stories/pages/Page.stories.ts` once per page, named for it, with `title: "Pages/<Page>"` so the pages sit together in Storybook.
Each imports its own HTML raw and renders it through `buildPage` from `stories/utils.ts`; a page state the script would produce is applied in the callback, as `App.stories.ts` does for one page.

Two things a nested page needs that the index page does not:

- **Asset URLs.** The story injects the markup into Storybook's `/iframe.html`, so relative URLs resolve from the site root, not the page's folder: `../src/assets/logo.svg` and `/src/assets/logo.svg` both land on the `staticDirs` mount and work, while a page-local URL (`./img/x.png` inside `help/index.html`) resolves to `/img/x.png` and misses. Do not rewrite the app's markup for this; mount the folder at the URL the markup resolves to inside the iframe, which is the page-relative path hoisted to the site root: `{ from: "../../help/img", to: "/img" }` (`from` is relative to `configs/storybook/`, so under `root: "src"` it is `../../src/help/img`). Only when two pages' local folders share a name (`help/img/` and `about/img/` would both want `/img`) make that page's asset URLs root-absolute (`/help/img/x.png`) and mount `{ from: "../../help/img", to: "/help/img" }`.
- **Its own stylesheet.** A page that links one of its own imports it at the top of its story file.

## Snapshot tests, shared and per page

`pages.chromatic.test.ts` registers the states every page has (default, dark theme) once per page from `PAGES`; `<page>.chromatic.test.ts` holds that page's own states.
Chromatic names each archive by the test file's path (relative to `testDir`, extension and `.test` dropped), its `describe` titles and its title (step 4), never by the URL visited, so its UI groups captures by file.
Leading every title with the page's name (`About - default [desktop]`) keeps the shared file readable by page; Playwright itself rejects two identical titles in one file.
A test may navigate between pages, since the fixture archives assets from every page it visits, but only the DOM at the end (or at `takeSnapshot`) is kept, so a page state is one test, not one step of a longer flow.
Relative URLs inside the archived pages are fine: the archive absolutizes them and rewrites same-origin ones to root-relative paths.

## What stays the same

The workflows, the Playwright configs, the Chromatic projects and secrets, the version pin and the README template all carry over unchanged; the README's "Where it lives" row and its last day-to-day item already mention the pages.
`vite preview` serves every entry the Vite config lists, so the `webServer` command needs nothing more.
