---
name: setup-chromatic
description: Set up Chromatic visual regression testing for a web app with one page or several, fed two ways, Storybook stories (component and page states, in each theme) and Playwright snapshots (whole-page states at several viewports), including the two GitHub workflows and a README section explaining both. Use when asked to add Chromatic, Storybook, visual snapshots, visual regression or Playwright UI snapshot testing to a repo, or to explain stories versus Playwright snapshots.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
---

# Setting up Chromatic with Storybook and Playwright

Chromatic renders UI in its own browsers and diffs every push against the last accepted baseline.
It is fed two ways here, and both are set up, because they catch different things:

- **Stories** (Storybook) render one component or one page in one state, built by hand from fixed inputs, with none of the app's script running, once per theme.
  A diff in a story points at that component or page.
- **Playwright snapshots** boot the real app in Chromium, drive it to a page state the way a person would reach it, and archive the DOM at the end of the test, once per viewport.
  A diff there points at the page as a whole: layout between components, overflow at phone widths, whatever the real boot path rendered.

Each feed gets its own Chromatic project, workflow, token and badge.
The result is the layout below, shared by [dandi/usage-page](https://github.com/dandi/usage-page), [brain-bbqs/bbqs-uploader](https://github.com/brain-bbqs/bbqs-uploader), [clip-extractor](https://github.com/brain-bbqs/clip-extractor), [encoding-helper](https://github.com/brain-bbqs/encoding-helper), [stamped-principles/stamped-checklist](https://github.com/stamped-principles/stamped-checklist) and [bbqs-web-app-template](https://github.com/brain-bbqs/bbqs-web-app-template).
All of those are one-page apps; the several-page form (`stories/pages/`, `configs/pages.ts`, one test file per page) comes from this skill's templates, with [references/several-pages.md](references/several-pages.md) for what differs.

```
.github/workflows/chromatic-storybook.yml   # builds Storybook, uploads it to the Storybook project
.github/workflows/chromatic-playwright.yml  # runs tests/chromatic, uploads the archives to the Playwright project
configs/storybook/main.ts                   # html-vite framework, no addons, stories glob
configs/storybook/preview.ts                # the app's stylesheet, theme pinned through a decorator, Chromatic modes
configs/playwright.config.ts                # tests/integration (the ordinary Playwright suite)
configs/playwright.chromatic.config.ts      # tests/chromatic (same settings, different testDir)
configs/pages.ts                            # several pages: every page once (file, URL, heading)
stories/utils.ts                            # withCard, buildPage
stories/App.stories.ts                      # one page: index.html itself, imported raw, each page state applied by hand
stories/pages/<Page>.stories.ts             # several pages: the same, one file per page
stories/<Component>.stories.ts              # one export per state; themes come from the modes
tests/chromatic/viewports.ts                # VIEWPORTS, forEachViewport, expectNoHorizontalOverflow
tests/chromatic/app.chromatic.test.ts       # one page: one forEachViewport call per page state
tests/chromatic/pages.chromatic.test.ts     # several pages: the states every page has, looped over configs/pages.ts
tests/chromatic/<page>.chromatic.test.ts    # several pages: that page's own states
```

Every file above has a complete template under [templates/](templates/) at the same relative path; copy, then adapt names rather than retyping.
Sections too long for this file live under [references/](references/): several pages, a shared config package, pull requests from forks, troubleshooting.
When in doubt about a detail the templates do not settle, open one of the sibling repos and copy what it does rather than inventing a variant.

## When to Use

- User asks to add Chromatic, Storybook, visual snapshots, visual regression or screenshot testing to a web app
- User asks for a Playwright snapshot or UI snapshot workflow, or to test an app at several viewports
- User asks to document a visual-testing setup in a README, or to explain stories versus Playwright snapshots
- User runs `/setup-chromatic`

## Step 0. Read the repository, then ask

Read `AGENTS.md` or `CLAUDE.md`, `README.md`, `package.json`, the Vite config and the folder the tool configs live in (`configs/` in the siblings), and settle what the repository already answers:

- **JS or TS**: what `configs/` and `tests/` use. For JS, drop the `import type` lines and annotations from the templates; nothing else changes.
- **Formatting**: the repo's Prettier config. Run its formatter over everything added rather than guessing.
- **Script names**: keep the existing ones for the dev server, build, preview and the ordinary Playwright suite.
- **Where the app lives**: `index.html` at the root or under `src/` (a Vite `root`), the stylesheet, `src/assets/` for the logo. Story and preview imports point at these.
- **One page or several**: one `index.html`, or several HTML entries (`about.html`, `help/index.html`, an entry list in the Vite config). Pages that are routes inside one `index.html` count as one entry with several states; see [references/several-pages.md](references/several-pages.md) for both shapes.
- **How the app themes**: a `data-theme` attribute, a class, a stored key in `localStorage`, an OS-preference fallback. The preview decorator and the dark-theme snapshot must pin it the same way the app reads it.
- **A version stamp**: a footer showing `package.json`'s version (Vite `define`). If there is one, step 8 pins it, or every version bump re-snapshots everything.
- **Node version**: match the repo's other workflows, but not below 22; `@chromatic-com/playwright` is ESM-only and requires Node 22.
- **A shared package**: a dependency of the organization's own that exports Storybook or Playwright config factories or viewport helpers. If so, read [references/shared-package.md](references/shared-package.md) and use its exports instead of the vanilla templates.
- **The conventions file**: whatever it asks for around a change like this (a version bump, a changelog line, `pre-commit`), note it for step 8.

Then ask, in one `AskUserQuestion` call, what the repository cannot answer:

1. **Web server for the snapshot suite**: the built app under `vite preview` (closer to what is deployed; the default) or the dev server (what dandi and STAMPED run).
2. **Where pull requests come from**: only branches pushed to this repository (the two workflows as templated) or outside forks too (the split in [references/fork-pull-requests.md](references/fork-pull-requests.md)).
3. **Production code**: the page states a person would recognize (nothing loaded, something loaded, signed out, an error card) are reached through `?test&...` URL injections, which means editing the app's own entry script (step 5). List the states proposed and ask whether that edit is welcome; if not, reach the states with `page.route` stubs and say so in the test.
4. **JS or TS**, only when the repo has neither yet.

## Step 1. Install

```bash
npm install --save-dev storybook @storybook/html-vite chromatic @chromatic-com/playwright @playwright/test
npx playwright install chromium   # once per machine; Chromatic archives only from Chromium (CI adds --with-deps, which needs root)
```

`storybook` and `@storybook/html-vite` are the whole of Storybook for a framework-less HTML/TypeScript app; nothing else, and no `npx storybook init`, which would drop a `.storybook/` folder at the root with addons and example stories these repos keep out.
`chromatic` is the CLI the GitHub Action runs; `@chromatic-com/playwright` is the test fixture that records the archives and the `build-archive-storybook` tool that turns them into a Storybook for upload.
If the registry cannot be reached, stop and tell the user rather than hand-writing version ranges; `npm install` resolves current ones.
A TypeScript repo also needs Vite's client types for the `?raw` imports to typecheck: a `src/vite-env.d.ts` holding `/// <reference types="vite/client" />`, if there is not one already.

Add the scripts (`build-storybook` is what the Chromatic action runs by default, so keep that exact name):

```json
"test:chromatic": "playwright test --config configs/playwright.chromatic.config.ts",
"storybook": "storybook dev -p 6006 --config-dir configs/storybook",
"build-storybook": "storybook build --config-dir configs/storybook"
```

## Step 2. Storybook config (`configs/storybook/`)

Copy `templates/configs/storybook/main.ts` and `preview.ts`.
`main.ts` is the html-vite framework, no addons, the stories glob, and a `staticDirs` mount of `src/assets` at `/src/assets`, which the raw-HTML page stories need because their asset URLs bypass Vite's pipeline.
`preview.ts` imports the app's stylesheet, disables Storybook's background layer (the stylesheet themes `<body>` itself), declares a `theme` global with a toolbar, and pins it on `<html>` through a decorator.
It also declares two Chromatic modes, `light` and `dark`, that set that global: Chromatic renders every story once per mode, each with its own baseline, so stories export one story per state and never a second set for the other theme.
If the app themes through a class or a stored key instead of `data-theme`, the decorator sets that instead; the point is that something explicit pins it.

Storybook's Vite builder loads the app's own `vite.config.*` from the parent of its config directory (`configs/` with `--config-dir configs/storybook`), so `define` and plugins are picked up as is.
It drops the config's `build` block, so a multi-page entry list does no harm there, and a `define` must sit at the top level to reach the stories.
If the Vite config lives elsewhere, point at it with `framework.options.builder.viteConfigPath` (resolved from the working directory, so build it from `import.meta.url`), or the stories build without it.

## Step 3. Stories (`stories/`)

Copy `templates/stories/utils.ts`: `withCard` centers a component at a realistic width; `buildPage` turns a page's raw HTML into an element, scripts removed, version stamp filled in, with a callback that applies a page state by hand.

The page story is `templates/stories/App.stories.ts` for one page, or one copy of `templates/stories/pages/Page.stories.ts` per page under `stories/pages/`, titled `Pages/<Page>`.
Each imports its own HTML through Vite's `?raw` suffix, so the story cannot drift from the markup; Storybook finds stories by their static exports, so each page needs its own file rather than a loop.
A page with a stylesheet of its own imports it at the top of its story file.

Component stories follow `templates/stories/Component.stories.ts`: markup built by hand, mirroring `index.html` (a comment says so, since the two can drift), one export per visual state with a human-readable `name`.
Which components get stories: anything with more than one visual state (a dropzone, a file row, a banner, a tab bar, a section divider).

## Step 4. Playwright configs (`configs/`)

Two configs that differ only in `testDir` (and a reporter folder, if one is set), so the ordinary suite and the Chromatic suite run under identical settings.
If the repo already has a Playwright config, copy it as `configs/playwright.chromatic.config.ts` and change only those; identical settings matter more than the template's particular choices.
Otherwise copy `templates/configs/playwright.chromatic.config.ts` and write `configs/playwright.config.ts` from it with `testDir: "../tests/integration"`.
The template serves the built app with `vite preview --strictPort`; switch the `webServer` command to the dev server if the user chose that in step 0.
It keeps one Chromium project on purpose.
Chromatic names a Playwright archive by the test's file, describe and title ([why tests show as new](https://www.chromatic.com/docs/faq/why-tests-show-as-new); `writeTestResult` in [chromatic-e2e](https://github.com/chromaui/chromatic-e2e/blob/main/packages/shared/src/write-archive/index.ts) builds it from `testInfo.titlePath`), never by its Playwright project, so several projects write over one story file.
Since `@chromatic-com/playwright` 1.0.0 the upload step recovers viewport-only projects as modes, but anything else that differs between projects is lost; one project with viewports set per test (step 5) sidesteps all of it.

## Step 5. Snapshot tests (`tests/chromatic/`)

Copy `templates/tests/chromatic/viewports.ts` (adapted from `@brain-bbqs/test-utils`, MIT; a repo whose shared package exports these imports them instead).
`forEachViewport` registers a title once per viewport, viewport in the title, page already sized; `expectNoHorizontalOverflow` fails naming the elements past the right edge, which is far easier to act on than a pixel diff.

For one page, copy `templates/tests/chromatic/app.chromatic.test.ts`: one `forEachViewport` call per page state, importing `test` from `@chromatic-com/playwright`, which is the whole integration (Playwright's `test` extended with a fixture that archives the DOM when the test body ends).
For several pages, copy `pages.chromatic.test.ts` (the states every page has, looped over `configs/pages.ts`) and one `<page>.chromatic.test.ts` per page with states of its own; every title starts with the page's name.
Each test asserts the state it expects before the capture, so a capture of the wrong state fails here, by name, rather than turning up as a diff.

Each state must be reachable deterministically.
The siblings reach them through `?test&...` URL injections rather than `page.route` stubs, because a URL is documented, reusable by a person on the deployed site, and exercised by the boot smoke test.
This edits production code, which is why step 0 asked first; the pattern, in the app's entry script (the BBQS apps keep the parsing in `src/lib/testInjection.ts` and list every flag in `docs/README.md`):

```ts
// `?test` alone is a no-op: every flag defaults to off, so nothing branches away from the ordinary
// boot path. The fake is substituted at the one point the real code would read the file, so what
// renders is the real loaded state, not a mockup beside it. Fixed name and size, so every capture
// comes out alike; obviously fake, so it is never mistaken for data; nothing written to storage.
const params = new URLSearchParams(location.search);
const injection = params.has("test") ? { mockFile: params.has("mock_file") } : { mockFile: false };
if (injection.mockFile) {
  showFile(new File(["a,b\n1,2\n"], "test-injection-mock-file.csv", { type: "text/csv" }));
}
```

A state that would race (a scan that finishes in milliseconds) gets a `freeze_...` flag that holds it mid-way.
To capture a moment mid-test rather than the end, `test.use({ disableAutoSnapshot: true })` and call `takeSnapshot(page, "After adding to cart", testInfo)` from the same import, with `testInfo` as the test's second argument; two snapshots with one name in a test silently overwrite each other.

## Step 6. Chromatic projects and secrets

This step is the user's: it needs their Chromatic account and the repository's settings.
Tell them what to do and wait for it, or carry on with steps 7 to 11 and say the workflows will fail until it is done:

1. In Chromatic, add a project and pick the repository: this is the Storybook project.
2. **Add project** again, pick the same repository a second time, and name this one for Playwright. Chromatic calls these [sub-projects](https://www.chromatic.com/docs/combine-stories-e2e/); each posts its own status check on pull requests.
3. Copy each project's token (Manage → Configure) into a repository secret under Settings → Secrets and variables → Actions: `CHROMATIC_STORYBOOK_PROJECT_TOKEN` and `CHROMATIC_PLAYWRIGHT_PROJECT_TOKEN`.

## Step 7. Workflows (`.github/workflows/`)

Copy both files from `templates/.github/workflows/`.
They run `on: push`, deliberately: Chromatic needs every commit on a branch to have a build, or it has no baseline to compare the next one with.
Both pin the runner image and print it, warn when the branch is behind `main`, skip Dependabot runs (no secrets there), and set `CHROMATIC_STATIC_VERSION` before anything is built.
The Storybook one turns on TurboSnap (`onlyChanged`); the Playwright one installs Chromium, runs `test:chromatic`, and uploads with `playwright: true`, which builds a Storybook from the archives under `test-results/`; TurboSnap cannot apply to a black-box archive of the running app.
Pin `chromaui/action` to its newest release tag (`git ls-remote --tags https://github.com/chromaui/action`), never `@latest`: a floating dependency is one more thing that can move a snapshot with no code change behind it, and Dependabot proposes the bumps.
If the user said pull requests come from forks, use [references/fork-pull-requests.md](references/fork-pull-requests.md) instead.

## Step 8. Housekeeping

- `.gitignore`: `storybook-static/`, `test-results/`, `playwright-report/` (and `playwright-report-chromatic/` if the html reporter is used).
- **The version stamp.** `CHROMATIC_STATIC_VERSION` is this layout's own convention, not a Chromatic setting: the Vite config reads it and pins the version it defines, which both workflows set before anything is built (in the Playwright workflow the build runs inside `webServer.command`, under the step's `env`):

  ```ts
  // configs/vite.config.ts
  const version = process.env.CHROMATIC_STATIC_VERSION ? "0.0.0" : pkg.version;
  export default defineConfig({ define: { __APP_VERSION__: JSON.stringify(version) } /* ... */ });
  ```

  Storybook loads that same config (step 2), so one pin covers the app build and the stories.
  Only when it does not (the Vite config is somewhere it does not look) repeat the define in `main.ts` through `viteFinal` with `mergeConfig`.
  Anything else that changes on its own (today's date, a random id, a live fetch) needs the same treatment or a mocked route, or it diffs on every build.

- **Agent guidance.** If the repo keeps any (`AGENTS.md`, `CLAUDE.md`, skills under `.claude/skills/`), add `templates/AGENTS-visual-snapshots.md` to it, so the next change to a story or test follows the same rules; the BBQS repos keep them as a `visual-snapshots` skill.
- **The conventions file.** Do what it asks for a change like this: the version bump, the changelog entry in its format, `pre-commit` before committing.

## Step 9. README

Follow `templates/README-visual-snapshots.md`: two badges in the header block, the two commands in the existing tests block, and a `## Visual snapshots` section (stories versus Playwright snapshots, setup once, day to day), in the README's own voice, with the app's own names and states.
A repo that keeps its README short puts the section in `docs/README.md` beside the live test injections.

## Step 10. Consistency check

Run the `analyze-duplicates` skill from this collection over what was added, as a consistency job rather than a style gate:

```
/analyze-duplicates stories tests/chromatic configs .github/workflows --output .tmp/chromatic-duplicates.md --no-html
```

Neither the report nor `.tmp/` is committed.
Read the report with one policy: a cluster that is only comments or docstrings is ignored.
The rationale is repeated in both workflows, in each page's test file, and in a story and the test that mirrors it on purpose, so each file explains itself.
A cluster of code is one of two things, and both are fixed: a helper that should be shared (`buildPage`, `forEachViewport`, the `PAGES` list, or the shared package when there is one), or a copy that has drifted (the two Playwright configs differing in more than `testDir`, the two workflows in more than the Playwright steps, two page story files in more than the page's own markup and states).
Nothing else is restructured on the report's account.

## Step 11. Verify, then hand over

```bash
npm run build-storybook                 # the Storybook the action will upload
npm run storybook                       # every story, in both themes from the toolbar, by eye
npm run test:chromatic                  # the archives land in test-results/chromatic-archives/
./node_modules/.bin/build-archive-storybook --output-dir=storybook-static   # what the action does with them
npm run format && npm run lint    # and pre-commit run --all-files, where the repo has it
```

Call `build-archive-storybook` through its path, not `npm exec`, which takes `--output-dir` as one of its own options and drops it.
Then stop and report: what was added, what step 0's answers decided, what step 6 still needs, and the commit and push the user should make (this skill does not push).
A push that opens a pull request falls under this collection's repo-wide conventions in `AGENTS.md`: check for a PR template and `CONTRIBUTING.md`, follow their branch, commit and changelog rules, and say what was found.
Once pushed, both workflows should go green, the first build of each project is accepted by hand in Chromatic, and the two badges render.
Symptoms after that are in [references/troubleshooting.md](references/troubleshooting.md).
