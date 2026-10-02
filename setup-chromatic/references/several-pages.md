# When the app has several pages

Two shapes count as several pages, and they differ in one place.

- **Several HTML entries**, a Vite multi-page app: `index.html`, `about.html`, `help/index.html`, each with its own `<script type="module">`.
  Every entry is a page here: a line in `configs/pages.ts`, a story file under `stories/pages/`, and its states in `tests/chromatic/`.
- **Routes inside one `index.html`**, a hash or history router.
  One HTML entry, so one page story file (`stories/App.stories.ts`), with each route's markup applied by hand as a state; the Playwright suite still gets one set of titles per route (`About - default`), reached with `page.goto("/#/about")` or the history path.
  A history router also needs `vite preview` and the host to answer every route with `index.html`; Vite's default `appType: "spa"` does, and the deployed host already does if the app works there.

Everything below is about the first shape.
The sibling repos are all one-page apps, so the templates are the reference here, not a sibling.

## The list of pages

`configs/pages.ts` (template under `templates/configs/`) names every page once: the HTML file Vite builds, the URL the suite visits, the heading it expects.
The Vite config builds its entry list from it and `pages.chromatic.test.ts` loops over it, so adding a page is one line plus a story file; the story files cannot read the list, because Storybook indexes stories from static exports, so they are the one place a page is listed again.

```ts
// configs/vite.config.ts
import { fileURLToPath } from "node:url";
// With the extension: Vite's native config loader refuses extensionless imports between config files.
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
  // of a missing page would silently capture the index page instead of failing.
  appType: "mpa",
  // ...
});
```

Absolute entry paths work on Vite 7 (`build.rollupOptions.input`) and Vite 8, where `build.rollupOptions` is a deprecated alias of `build.rolldownOptions` and a top-level `input` of root-relative paths is the new form; the Vite docs' own example uses `resolve(import.meta.dirname, "nested/index.html")`.
When `index.html` lives under `src/` (`root: "src"`), the entries are still absolute paths, and a page's URL and output path are relative to that root (`src/help/index.html` is served at `/help/` and built to `dist/help/index.html`).
Vite ignores the entry's key for the output name; the built page keeps its path.

## Which URL a test visits

Vite's dev and preview servers resolve page URLs the same way, with no redirects:

| Layout             | Served at                     | Not served at                                            |
| ------------------ | ----------------------------- | -------------------------------------------------------- |
| `about.html`       | `/about.html`, `/about`       | `/about/`                                                |
| `help/index.html`  | `/help/`, `/help/index.html`  | `/help` (404 under `mpa`; `index.html` under `spa`)      |

Static hosts differ on the extensionless and slash-less forms, so `path` in `configs/pages.ts` is the form that works everywhere, `/about.html` and `/help/`, and it is the form the app's own `<a href>` links should use, since Vite does not rewrite link targets (only asset references) at build time.
If the app deploys under a sub-path (`base: "/<repo>/"` for a GitHub Pages project site), root-absolute links break there; write them relative or from `import.meta.env.BASE_URL`, and give the Playwright `baseURL` the same sub-path so `page.goto` lands under it.
The sibling apps avoid all of this with `base: "./"` or a custom domain.

## Stories, one file per page

Copy `templates/stories/pages/Page.stories.ts` once per page, named for it, with `title: "Pages/<Page>"` so the pages sit together in Storybook.
Each imports its own HTML raw and renders it through `buildPage` from `stories/utils.ts`; a page state the script would produce is applied in the callback, as `App.stories.ts` does for one page.

Two things a nested page needs that the index page does not:

- **Root-absolute asset URLs.** The story injects the markup into Storybook's iframe, so a relative `../src/assets/logo.svg` resolves against the iframe's URL, not the page's folder, and breaks; `/src/assets/logo.svg` is served by the `staticDirs` mount in `main.ts`. Vite rewrites either form correctly in the real build, so root-absolute costs nothing there.
- **Its own stylesheet.** `preview.ts` imports the shared stylesheet; a page that links one of its own imports it at the top of its story file, and it stays loaded in the local Storybook until the preview reloads, which does not matter to Chromatic, which renders each story on its own.

## Snapshot tests, shared and per page

`pages.chromatic.test.ts` registers the states every page has (default, dark theme) once per page from `PAGES`; `<page>.chromatic.test.ts` holds that page's own states.
Chromatic names each archive by the test file's path (relative to `testDir`, extension and `.test` dropped), its `describe` titles and its title, so the Chromatic UI groups captures by file; leading every title with the page's name (`About - default [desktop]`) keeps the shared file readable by page, and Playwright itself rejects two identical titles in one file.
A test may navigate between pages, since the fixture archives assets from every page it visits, but only the DOM at the end (or at `takeSnapshot`) is kept, so a page state is one test, not one step of a longer flow.
Relative URLs inside the archived pages are fine: the archive absolutizes them and rewrites same-origin ones to root-relative paths.

## What stays the same

The workflows, the Playwright configs, the Chromatic projects and secrets, the version pin and the README template all carry over unchanged; the README's "Where it lives" row and its last day-to-day item already mention the pages.
`vite preview` serves every entry the Vite config lists, so the `webServer` command needs nothing more.
