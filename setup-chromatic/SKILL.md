---
name: setup-chromatic
description: Set up Chromatic visual regression testing for a single-page web app with two feeds, Storybook stories (component states) and Playwright snapshots (whole-page states at several viewports), in the layout dandi/usage-page, brain-bbqs/bbqs-uploader, clip-extractor, encoding-helper and stamped-principles/stamped-checklist use (configs/, stories/, tests/chromatic/, two GitHub workflows, two Chromatic projects), and write the README section that walks a maintainer through it and explains how stories and Playwright snapshots differ. Use whenever someone asks to add Chromatic, Storybook, visual snapshots, visual regression or screenshot testing, or a Playwright UI snapshot workflow to a repo, to document that setup in a README, or to explain stories versus Playwright snapshots, even if they name only one of the pieces.
---

# Setting up Chromatic with Storybook and Playwright

Chromatic renders UI in its own browsers and diffs every push against the last accepted baseline.
It is fed two ways here, and both are set up, because they catch different things:

- **Stories** (Storybook) render one component in one state, built by hand from fixed inputs, with none of the app's script running.
  A diff in a story points at that component.
- **Playwright snapshots** boot the real app in Chromium, drive it to a page state the way a person would reach it, and archive the DOM at the end of the test, once per viewport.
  A diff there points at the page as a whole: layout between components, overflow at phone widths, whatever the real boot path rendered.

Each feed gets its own Chromatic project, workflow, token and badge.
The result is the layout below, which is what [dandi/usage-page](https://github.com/dandi/usage-page), [brain-bbqs/bbqs-uploader](https://github.com/brain-bbqs/bbqs-uploader), [clip-extractor](https://github.com/brain-bbqs/clip-extractor), [encoding-helper](https://github.com/brain-bbqs/encoding-helper), [stamped-principles/stamped-checklist](https://github.com/stamped-principles/stamped-checklist) and the [bbqs-web-app-template](https://github.com/brain-bbqs/bbqs-web-app-template) all share.
When in doubt about a detail, open one of them and copy what it does rather than inventing a variant.

```
.github/workflows/chromatic-storybook.yml   # builds Storybook, uploads it to the Storybook project
.github/workflows/chromatic-playwright.yml  # runs tests/chromatic, uploads the archives to the Playwright project
configs/storybook/main.ts                   # html-vite framework, no addons, stories glob
configs/storybook/preview.ts                # the app's stylesheet, theme pinned through a decorator
configs/playwright.config.ts                # tests/integration (the ordinary Playwright suite)
configs/playwright.chromatic.config.ts      # tests/chromatic (same settings, different testDir)
stories/utils.ts                            # withTheme, withCard
stories/App.stories.ts                      # index.html itself, imported raw, each page state applied by hand
stories/<Component>.stories.ts              # one export per state, in both themes
tests/chromatic/viewports.ts                # VIEWPORTS, forEachViewport, expectNoHorizontalOverflow
tests/chromatic/app.chromatic.test.ts       # one forEachViewport call per page state
```

Work in this order.
Each step says what to write and why it is written that way; the templates are complete, so adapt names rather than retyping.

## Before writing anything

Read the repository's `AGENTS.md` or `CLAUDE.md`, its `README.md`, `package.json` and `configs/` (or wherever its tool configs live), and settle these, because every template below depends on them:

| Decide                | Take it from                                                                                                                                                                                                           |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| JS or TS              | What `configs/` and `tests/` already use. dandi and STAMPED are JS, the BBQS apps are TS. For JS, drop the `import type` lines and annotations; nothing else changes.                                                  |
| Indentation and style | The repo's Prettier config. Run its formatter over everything you add rather than guessing.                                                                                                                            |
| Script names          | Keep the existing ones. The suites agree on `storybook`, `build-storybook` and `test:chromatic`; the ordinary Playwright suite is `test:integration` (BBQS) or `test:e2e` (dandi, STAMPED).                            |
| Where the app lives   | `index.html` at the root or under `src/`, the stylesheet (`src/style.css` or `src/styles.css`), `src/assets/` for the logo. Story and preview imports point at these.                                                  |
| How the app themes    | A `data-theme` attribute on `<html>`, a stored key in `localStorage` (`theme`, `<app>.theme`), an OS-preference fallback. The preview decorator and the dark-theme snapshot must pin it the same way the app reads it. |
| A version stamp       | A footer that shows `package.json`'s version (injected as `__APP_VERSION__` by Vite). If there is one, it has to be pinned for Chromatic (step 8), or every version bump re-snapshots everything.                      |
| Node version          | Match the repo's other workflows, but not below 22: `@chromatic-com/playwright` 0.15+ is ESM-only and requires Node 22.                                                                                                |
| A BBQS app?           | If `@brain-bbqs/config` is in `devDependencies`, the configs and helpers already exist as factories; see "When the repo is a BBQS companion app" and use those instead of the vanilla templates.                       |

Also note what the conventions file asks for around a change like this: the BBQS and STAMPED repos bump `package.json`'s version when `configs/` or `package.json` change, add a `#### 🏠 Internal` line to `CHANGELOG.md`, and run `pre-commit` before pushing.

## Step 1. Install

```bash
npm install --save-dev storybook @storybook/html-vite chromatic @chromatic-com/playwright @playwright/test
npx playwright install chromium --with-deps   # once per machine; Chromatic archives only from Chromium
```

`storybook` and `@storybook/html-vite` are the whole of Storybook for a framework-less HTML/TypeScript app (Storybook 9+ folded the rest into the `storybook` package).
Nothing else, and no `npx storybook init`: it would drop a `.storybook/` folder at the root with addons and example stories these repos keep out.
`chromatic` is the CLI the GitHub Action runs; `@chromatic-com/playwright` is the test fixture that records the archives and the `build-archive-storybook` tool that turns them into a Storybook for upload.
If the registry cannot be reached and `package.json` has to be edited by hand, the majors at the time of writing are `storybook` and `@storybook/html-vite` `^10`, `chromatic` `^18`, `@chromatic-com/playwright` `^1` (the sibling repos still carry `^0.14`, which runs on Node 20) and `@playwright/test` `^1.63`; a later `npm install` corrects the ranges.
A TypeScript repo also needs Vite's client types for the `?raw` import in step 3 to typecheck: a `src/vite-env.d.ts` holding `/// <reference types="vite/client" />`, if there is not one already.

Add the scripts:

```json
"test:chromatic": "playwright test --config configs/playwright.chromatic.config.ts",
"storybook": "storybook dev -p 6006 --config-dir configs/storybook",
"build-storybook": "storybook build --config-dir configs/storybook"
```

`build-storybook` is what the Chromatic action runs by default (`buildScriptName`), so keep that exact name.

## Step 2. Storybook config (`configs/storybook/`)

`main.ts`:

```ts
import type { StorybookConfig } from "@storybook/html-vite";

const config: StorybookConfig = {
  // Stories live beside the app rather than in src/, so a story is never mistaken for shipped code.
  stories: ["../../stories/**/*.stories.@(js|ts)"],
  // No addons: the stories exist to be snapshotted and looked at, nothing more.
  addons: [],
  framework: { name: "@storybook/html-vite", options: {} },
  // Only needed when App.stories injects index.html raw: its /src/assets/... URLs bypass Vite's
  // asset pipeline, so the folder is served at that same path in dev and in the built Storybook.
  staticDirs: [{ from: "../../src/assets", to: "/src/assets" }],
};

export default config;
```

Storybook's Vite builder loads the app's own `vite.config.*` from the parent of its config directory, so with `--config-dir configs/storybook` a `configs/vite.config.ts` is picked up as is, `define` and plugins included.
If the app's Vite config lives elsewhere (the repository root, say), point at it with `framework.options.builder.viteConfigPath` (a path relative to the repository root), or the stories build without it.

`preview.ts`:

```ts
import type { Preview } from "@storybook/html-vite";
import "../../src/style.css";

const preview: Preview = {
  parameters: {
    // The app's stylesheet themes <body> itself, so Storybook's own background layer is disabled
    // rather than painted over it.
    backgrounds: { disable: true },
  },
  globalTypes: {
    theme: {
      description: "App color theme",
      toolbar: {
        title: "Theme",
        icon: "circlehollow",
        items: [
          { value: "light", title: "Light" },
          { value: "dark", title: "Dark" },
        ],
        dynamicTitle: true,
      },
    },
  },
  initialGlobals: { theme: "light" },
  decorators: [
    // Pins the theme the same way the app reads it, so a snapshot never depends on the OS
    // color-scheme preference of whichever machine renders it.
    (story, context) => {
      document.documentElement.dataset.theme = context.globals.theme ?? "light";
      return story();
    },
  ],
};

export default preview;
```

If the app themes through a class or a stored key instead of `data-theme`, the decorator sets that instead; the point is that something explicit pins it.

## Step 3. Stories (`stories/`)

`stories/utils.ts`:

```ts
/** Centers a component at a realistic width, the way the page shell would. */
export function withCard(element: HTMLElement): HTMLDivElement {
  const wrapper = document.createElement("div");
  wrapper.style.maxWidth = "640px";
  wrapper.style.margin = "1.5rem auto";
  wrapper.appendChild(element);
  return wrapper;
}

/**
 * Forces the theme before building a story, so it renders the same regardless of the OS preference
 * or whatever the previously viewed story left on <html>.
 */
export function withTheme<T extends HTMLElement>(theme: "light" | "dark", build: () => T): T {
  document.documentElement.dataset.theme = theme;
  return build();
}
```

A component story builds the markup by hand, mirroring `index.html` (a comment says so, since the two can drift), and exports one story per state in each theme, with a human-readable `name`:

```ts
import { withCard, withTheme } from "./utils";

type DropzoneState = "idle" | "dragover" | "rejected";

// Kept in sync with the dropzone markup in index.html.
function buildDropzone(state: DropzoneState): HTMLElement {
  const dz = document.createElement("div");
  dz.id = "dropzone";
  dz.className = "dropzone";
  if (state === "dragover") dz.classList.add("dragover");
  dz.innerHTML = `<div class="dz-inner"><p>Drop a file here, or <button type="button" class="dz-browse">browse</button>.</p>
    <p class="dz-reject" ${state === "rejected" ? "" : "hidden"}>That wasn't a file.</p></div>`;
  return withCard(dz);
}

export default { title: "Components/Dropzone" };

// Every state in both themes: a dark-only regression in one of them is otherwise invisible.
export const IdleLight = { name: "Idle (light)", render: () => withTheme("light", () => buildDropzone("idle")) };
export const IdleDark = { name: "Idle (dark)", render: () => withTheme("dark", () => buildDropzone("idle")) };
export const DragOverLight = {
  name: "Drag over (light)",
  render: () => withTheme("light", () => buildDropzone("dragover")),
};
export const DragOverDark = {
  name: "Drag over (dark)",
  render: () => withTheme("dark", () => buildDropzone("dragover")),
};
export const RejectedLight = {
  name: "Rejected (light)",
  render: () => withTheme("light", () => buildDropzone("rejected")),
};
export const RejectedDark = {
  name: "Rejected (dark)",
  render: () => withTheme("dark", () => buildDropzone("rejected")),
};
```

`stories/App.stories.ts` renders the page itself, so the whole-page story cannot drift from the markup:

```ts
// Loaded through Vite's ?raw import so this story always mirrors the real markup in index.html.
import indexHtml from "../index.html?raw";

// Defined by the app's Vite config, which Storybook loads too (see configs/storybook/main.ts).
declare const __APP_VERSION__: string;

function buildApp({ fileLoaded = false } = {}): HTMLElement {
  const doc = new DOMParser().parseFromString(indexHtml, "text/html");
  // The app's own <script type="module"> wires up real behavior; the story needs only the markup.
  doc.body.querySelectorAll("script").forEach((s) => s.remove());
  const wrapper = document.createElement("div");
  wrapper.innerHTML = doc.body.innerHTML;
  // Mirrors what main.ts renders, by hand, since none of it runs here: the version stamp first
  // (an empty anchor is invisible in a snapshot), then the state.
  const version = wrapper.querySelector("#version-indicator");
  if (version) version.textContent = `v${__APP_VERSION__}`;
  if (fileLoaded) {
    wrapper.querySelector("#load-card")?.setAttribute("hidden", "");
    wrapper.querySelector("#file-card")?.removeAttribute("hidden");
  }
  return wrapper;
}

export default { title: "App" };

export const Default = { name: "Default (nothing loaded)", render: () => buildApp() };
export const FileLoaded = { name: "File loaded", render: () => buildApp({ fileLoaded: true }) };
```

Which components get stories: anything with more than one visual state (a dropzone, a file row, a banner, a tab bar, a section divider), each state in both themes.
A `?raw` import of `index.html` needs the `staticDirs` entry from step 2 for its images to resolve.

## Step 4. Playwright configs (`configs/`)

Two configs that differ only in `testDir` (and a reporter folder, if one is set), so the ordinary suite and the Chromatic suite run under identical settings.
If the repo already has a Playwright config, copy it as `configs/playwright.chromatic.config.ts` and change only those, keeping whatever retries, reporter and server it already uses: identical settings matter more than the template's particular choices.
The template below is for a repo that has none yet (write `configs/playwright.config.ts` from it too, with `testDir: "../tests/integration"`):

```ts
import { defineConfig, devices } from "@playwright/test";

const PORT = 4173;
const baseURL = `http://localhost:${PORT}`;

export default defineConfig({
  // Paths here are relative to this file, so ../ reaches the repository root.
  testDir: "../tests/chromatic",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  // outputDir is left alone on purpose: it defaults to <package.json dir>/test-results even for a
  // config under configs/, and that is where the Chromatic fixture writes its archives and where
  // the Chromatic action looks for them. Setting it means also setting CHROMATIC_ARCHIVE_LOCATION.
  use: { baseURL, trace: "on-first-retry" },
  // One Desktop Chrome project, deliberately. Chromatic keys a Playwright archive by the test's
  // title alone, so viewports are set per test (tests/chromatic/viewports.ts), never as projects:
  // run as projects, each viewport writes over the last one's manifest and only one reaches Chromatic.
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    // The built app, served by vite preview; --strictPort so a preview of another app holding the
    // port cannot be tested in its place.
    command: `npm run build && npm run preview -- --port ${PORT} --strictPort`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
```

dandi and STAMPED run the dev server (`npm run dev` on 5173) instead; either works, the built app is simply closer to what is deployed.

## Step 5. Playwright snapshot tests (`tests/chromatic/`)

`tests/chromatic/viewports.ts` (adapted from `@brain-bbqs/test-utils`, MIT; a BBQS app imports these from the package instead):

```ts
import { expect, type Page } from "@playwright/test";

export interface Viewport {
  name: string;
  width: number;
  height: number;
}

/** Two device classes in both orientations, plus the desktop width the suite runs under. */
export const VIEWPORTS: readonly Viewport[] = [
  { name: "desktop", width: 1280, height: 720 },
  { name: "tablet portrait", width: 768, height: 1024 },
  { name: "tablet landscape", width: 1024, height: 768 },
  { name: "mobile portrait", width: 390, height: 844 },
  { name: "mobile landscape", width: 844, height: 390 },
];

type Registrar = (title: string, body: (args: { page: Page }) => Promise<void>) => void;

/**
 * Registers `title` once per viewport, named in the title and with the page already sized to it.
 * Chromatic snapshots the page after each test body and names the capture by the test's title
 * alone, so the viewport in the title is what keeps the captures apart.
 */
export function forEachViewport(
  test: Registrar,
  title: string,
  body: (args: { page: Page }, viewport: Viewport) => Promise<void>,
  viewports: readonly Viewport[] = VIEWPORTS,
): void {
  for (const viewport of viewports) {
    test(`${title} [${viewport.name}]`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await body({ page }, viewport);
    });
  }
}

/**
 * Fails naming the elements that reach past the right edge of the viewport. A narrow screen's
 * first failure is a row of controls that cannot wrap, and a named element is far easier to act
 * on than a pixel diff in a snapshot.
 */
export async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const { scrollWidth, clientWidth, offenders } = await page.evaluate(() => {
    const root = document.documentElement;
    const offenders: string[] = [];
    document.querySelectorAll("body *").forEach((el) => {
      // Shapes inside an inline <svg> are measured in its own coordinate space; the <svg> is checked.
      if ((el as SVGElement).ownerSVGElement) return;
      const { width, right } = el.getBoundingClientRect();
      if (width > 0 && right > root.clientWidth + 1) {
        const id = el.id ? `#${el.id}` : "";
        const names = typeof el.className === "string" ? el.className.trim().split(/\s+/).filter(Boolean) : [];
        const classes = names.length ? `.${names.join(".")}` : "";
        offenders.push(
          `${el.tagName.toLowerCase()}${id}${classes} (${Math.round(width)}px wide, ends at ${Math.round(right)}px)`,
        );
      }
    });
    return { scrollWidth: root.scrollWidth, clientWidth: root.clientWidth, offenders };
  });
  expect(offenders, `Elements past the right edge of the ${clientWidth}px viewport`).toEqual([]);
  expect(scrollWidth, `Page scrolls sideways at ${clientWidth}px`).toBeLessThanOrEqual(clientWidth + 1);
}
```

`tests/chromatic/app.chromatic.test.ts`, one `forEachViewport` call per page state:

```ts
import { test, expect } from "@chromatic-com/playwright";
import { expectNoHorizontalOverflow, forEachViewport } from "./viewports";

// The Chromatic fixture archives the page after each test body; the assertions are there so a
// capture of the wrong state fails here, by name, rather than turning up as a diff.

forEachViewport(test, "Main page - default", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("App Name");
  await expectNoHorizontalOverflow(page);
});

forEachViewport(test, "Main page - dark theme", async ({ page }) => {
  // Seeded before the page's own script reads it, the way a returning visitor's choice would be;
  // the key and value are whatever the app itself stores ("theme", "<app>.theme", ...).
  await page.addInitScript(() => localStorage.setItem("theme", "dark"));
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expectNoHorizontalOverflow(page);
});

forEachViewport(test, "Main page - file loaded", async ({ page }) => {
  // The ?test&mock_file injection stands a fixed fake in for a dropped file (see below).
  await page.goto("/?test&mock_file");
  await expect(page.locator("#file-card")).toBeVisible();
  await expectNoHorizontalOverflow(page);
});
```

The import from `@chromatic-com/playwright` instead of `@playwright/test` is the whole integration: `test` is Playwright's `test` extended with a fixture that records a DOM archive at the end of the test.
Which page states get a test: the ones a person would recognize as different pages of the app (nothing loaded, something loaded, signed out, an error card).

Each state must be reachable deterministically, and the sibling repos reach them through `?test&...` URL injections rather than `page.route` stubs, because a URL is documented, reusable by a person on the deployed site, and exercised by the boot smoke test.
The pattern, in `src/main.ts` (the BBQS apps keep the parsing in `src/lib/testInjection.ts` and list every flag in `docs/README.md`):

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
To capture a moment mid-test rather than the end, `test.use({ disableAutoSnapshot: true })` and call `takeSnapshot(page, "After adding to cart", testInfo)` from the same import, with `testInfo` as the test's second argument.

## Step 6. Chromatic projects and secrets

Two projects on the same repository, which Chromatic calls sub-projects:

1. In Chromatic, add a project and pick the repository: this is the Storybook project.
2. **Add project** again, pick the same repository a second time, and name this one for Playwright.
3. Copy each project's token (Manage → Configure) into a repository secret under Settings → Secrets and variables → Actions: `CHROMATIC_STORYBOOK_PROJECT_TOKEN` and `CHROMATIC_PLAYWRIGHT_PROJECT_TOKEN`.

Until both secrets exist, both workflows fail; that is expected and is why the README's setup steps list them.
Each project posts its own status check on pull requests.

## Step 7. Workflows (`.github/workflows/`)

`chromatic-storybook.yml`:

```yaml
name: Chromatic (Storybook)

on: push

permissions:
  contents: read

jobs:
  chromatic:
    name: Run Chromatic (Storybook)
    # Dependabot-triggered runs cannot read Actions secrets, so the Chromatic project token is
    # unavailable; skip instead of failing.
    if: github.actor != 'dependabot[bot]'
    # Pinned rather than ubuntu-latest: a runner image bump (system fonts, antialiasing,
    # rasterizer) shifts screenshot pixels on its own, with no code change to explain it.
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout
        uses: actions/checkout@v7
        with:
          # The whole history: Chromatic picks the baseline from it, and TurboSnap needs it.
          fetch-depth: 0

      - name: Report the runner image
        # The ubuntu-24.04 label is not a fixed machine: the image behind it is rebuilt roughly
        # weekly, and a new one brings new fonts and rasterizer libraries. Printed so a snapshot
        # diff with no code change behind it can be checked against the image its baseline used.
        # (A block scalar: the colon in the message would otherwise make this line invalid YAML.)
        run: |
          echo "Runner image: ${ImageOS:-unknown} ${ImageVersion:-unknown}"

      - name: Report how far the branch is behind main
        # Chromatic takes the branch's own last build as the baseline, so a branch that has not
        # seen main in a week diffs against a week-old UI and reports main's changes as this
        # branch's. Merge main in before reading the result.
        if: github.ref != 'refs/heads/main'
        run: |
          git fetch --no-tags --quiet origin main
          behind=$(git rev-list --count HEAD..origin/main)
          if [ "$behind" -eq 0 ]; then
            echo "Branch is up to date with main."
          else
            echo "::notice::This branch is $behind commit(s) behind main. Chromatic diffs it against the branch's own last build, so the changes it reports may be main's rather than this branch's; merge main in before reading them."
          fi

      - name: Set up Node
        uses: actions/setup-node@v7
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Run Chromatic
        uses: chromaui/action@v18.10.2
        env:
          # Pins the footer's version string so a version bump alone does not re-snapshot every story.
          CHROMATIC_STATIC_VERSION: "true"
        with:
          projectToken: ${{ secrets.CHROMATIC_STORYBOOK_PROJECT_TOKEN }}
          # TurboSnap: only stories whose files changed are re-snapshotted.
          onlyChanged: true
```

`chromatic-playwright.yml` is a copy of that file with four edits:

1. `name: Chromatic (Playwright)`; the job id becomes `chromatic-playwright` and its `name: Run Chromatic (Playwright)`.
2. Two steps inserted after `Install dependencies`:

   ```yaml
   - name: Install Playwright browsers
     run: npx playwright install chromium --with-deps

   - name: Run Playwright tests
     run: npm run test:chromatic
     env:
       # Pins the footer's version string so a version bump alone does not re-snapshot the page.
       CHROMATIC_STATIC_VERSION: "true"
   ```

3. The `Run Chromatic` step loses its `env` block (the pin was applied when the app was built, in the step above) and `onlyChanged` (TurboSnap cannot apply to a black-box archive of the running app), and gains `playwright: true`, which builds a Storybook from the archives under `test-results/` and uploads that:

   ```yaml
   - name: Run Chromatic
     uses: chromaui/action@v18.10.2
     with:
       projectToken: ${{ secrets.CHROMATIC_PLAYWRIGHT_PROJECT_TOKEN }}
       playwright: true
   ```

4. The token is the Playwright project's, as shown.

Pin `chromaui/action` to the newest release tag when writing the files (`v18.10.2` at the time of writing; the sibling repos carry `v18.10.1` from when they were set up).
`@latest` would track every release, breaking ones included, and a floating dependency is one more thing that can move a snapshot with no code change behind it.
`on: push` is deliberate: Chromatic needs every commit on a branch to have a build, or it has no baseline to compare the next one with.

## Step 8. Housekeeping

- `.gitignore`: `storybook-static/`, `test-results/`, `playwright-report/` (and `playwright-report-chromatic/` if the html reporter is used).
- The version stamp.
  If Vite defines `__APP_VERSION__` from `package.json`, pin it when `CHROMATIC_STATIC_VERSION` is set, which both workflows do before anything is built:

  ```ts
  // configs/vite.config.ts
  const version = process.env.CHROMATIC_STATIC_VERSION ? "0.0.0" : pkg.version;
  export default defineConfig({ define: { __APP_VERSION__: JSON.stringify(version) } /* ... */ });
  ```

  Storybook loads that same config (step 2), so one pin covers the app build and the stories.
  Only when Storybook does not load it (the Vite config is somewhere it does not look, or something else needs overriding) repeat the define in `main.ts`:

  ```ts
  import { mergeConfig } from "vite";
  // ...
  async viteFinal(viteConfig) {
    const version = process.env.CHROMATIC_STATIC_VERSION ? "0.0.0" : pkg.version;
    return mergeConfig(viteConfig, { define: { __APP_VERSION__: JSON.stringify(version) } });
  },
  ```

  Anything else that changes on its own (today's date, a random id, a live fetch) needs the same treatment or a mocked route, or it diffs on every build.

- Agent guidance.
  If the repo keeps any (`AGENTS.md`, `CLAUDE.md`, or skills under `.claude/skills/`), add the rules from "Keeping snapshots deterministic" below to it, so the next change to a story or test follows them; the BBQS repos keep them as a `visual-snapshots` skill.
  The README (step 9) is for people using the repo and does not carry those rules.
- The version bump and changelog entry in whatever form the conventions file asks for (a new version heading when it says to bump per PR, the top `## Upcoming` section when it keeps one).

## Step 9. README

Two badges in the centered header block, after the codecov/license/prettier row, each on its own line, linking to the workflow (or to the project's Chromatic library page, `https://www.chromatic.com/library?appId=<appId>`, when it is public):

```html
<p align="center">
  <a href="https://github.com/<org>/<repo>/actions/workflows/chromatic-storybook.yml"
    ><img
      src="https://github.com/<org>/<repo>/actions/workflows/chromatic-storybook.yml/badge.svg"
      alt="Chromatic (Storybook)"
  /></a>
  <a href="https://github.com/<org>/<repo>/actions/workflows/chromatic-playwright.yml"
    ><img
      src="https://github.com/<org>/<repo>/actions/workflows/chromatic-playwright.yml/badge.svg"
      alt="Chromatic (Playwright)"
  /></a>
</p>
```

Then the commands in the `## Development` / `### Tests` block the README already has (dandi style: one command per line, an aligned `#` comment saying what each is):

```bash
npm run storybook          # the component stories, live
npm run test:chromatic     # the page snapshots, in Chromium (nothing is uploaded)
```

And a `## Visual snapshots` section.
Where the README is kept to the sibling shape (logo, title, badges, one line, credits), as the BBQS apps keep theirs, the badges still go in the README and this section goes in `docs/README.md` beside the live test injections, which is where those repos keep what a developer needs to know.
Write it in the README's own voice: short declarative sentences, the why beside the what, one sentence per line where the repo does that, few em-dashes.
Replace the names, states and script names with the app's own; the shape to keep is below.

```markdown
## Visual snapshots

Every push is rendered on [Chromatic](https://www.chromatic.com) and compared against the last accepted baseline, twice: once per story, once per page state.
The two feeds answer different questions, which is why there are two projects, two workflows and two badges.

### Stories versus Playwright snapshots

|                          | Storybook stories                                                                                  | Playwright snapshots                                                                                                       |
| ------------------------ | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| What is captured         | One component in one state, built by hand from fixed inputs, with none of the app's script running | The real app, booted in Chromium and driven to a state the way a person would reach it, at desktop, tablet and phone sizes |
| Where it lives           | `stories/*.stories.ts`                                                                             | `tests/chromatic/*.test.ts`                                                                                                |
| What a diff points at    | That component, in that state and theme                                                            | The page as a whole: layout between components, overflow at narrow widths, what the real boot path rendered                |
| How it reaches Chromatic | The built Storybook (`npm run build-storybook`)                                                    | An archive of the DOM that `@chromatic-com/playwright` records at the end of each test (`npm run test:chromatic`)          |
| Workflow and badge       | Chromatic (Storybook)                                                                              | Chromatic (Playwright)                                                                                                     |

A story is the place for a component's own states (idle, drag-over, rejected, light and dark).
A Playwright snapshot is the place for a page state (nothing loaded, a file loaded, signed out), since only the running app knows how its pieces fit together.
Neither keeps pixels in this repository: Chromatic renders both in its own browsers, holds the baselines, and a change is accepted or rejected in its review UI.

### Setup (once per repository)

1. Create two Chromatic projects for this repository: one for Storybook, then **Add project**, pick the same repository again, and name the second one for Playwright.
2. Add each project's token as a repository secret: `CHROMATIC_STORYBOOK_PROJECT_TOKEN` and `CHROMATIC_PLAYWRIGHT_PROJECT_TOKEN`.
3. Push. `chromatic-storybook.yml` and `chromatic-playwright.yml` under `.github/workflows/` run on every push; the first build of each project is its baseline, accepted by hand in Chromatic.

### Day to day

1. `npm run storybook` to look at the stories; `npm run test:chromatic` to run the page captures locally. Nothing is uploaded from a local run.
2. Push a branch. Each workflow uploads its captures, and Chromatic posts one status check per project.
3. Open the check and review each diff: accept what was intended, otherwise fix and push again. Chromatic diffs a branch against that branch's own last build, so merge `main` in first when the branch is behind, or `main`'s changes show up as yours.
4. A new component state gets a story in both themes; a new page state gets a `forEachViewport` test in `tests/chromatic/`, plus a way to reach it deterministically.
```

Where the repo also compares pixels with Playwright's own `toHaveScreenshot` (dandi/usage-page does, for a WebGL map that a DOM archive cannot carry), add one line saying that is a third kind, pixels against PNGs committed beside the test, used only where Chromatic cannot see.

## Step 10. Verify

```bash
npm run build-storybook                 # the Storybook the action will upload
npm run storybook                       # every story, in both themes, by eye
npm run test:chromatic                  # the archives land in test-results/chromatic-archives/
./node_modules/.bin/build-archive-storybook --output-dir=storybook-static   # what the action does with them
npx chromatic --project-token=<storybook token>              # optional: the first baseline, from a machine
npx chromatic --playwright --project-token=<playwright token>
npm run format && npm run lint && pre-commit run --all-files
```

Call `build-archive-storybook` through its path, not `npm exec`, which takes `--output-dir` as one of its own options and drops it.
Then push, watch both workflows go green, accept the first build of each project in Chromatic, and confirm the two badges render.

## Keeping snapshots deterministic

These are the rules the sibling repos distilled from Chromatic diffs that no code change explained; the templates above already follow them, and they belong in the repo's agent guidance:

- **One test per viewport, viewport in the title.**
  Chromatic keys an archive by the test's title; projects overwrite each other.
  `forEachViewport`, never a second project.
- **Fail on overflow by name.**
  `expectNoHorizontalOverflow` at the end of every snapshot test; the fix is usually a `@media (max-width: 600px)` rule that lets a row wrap.
- **Pin what changes on its own.**
  The version stamp (`CHROMATIC_STATIC_VERSION`), the runner (`ubuntu-24.04`, image printed), the theme (decorator, `withTheme`, a seeded storage key), media fixtures (pin the encoder version, print the file's hash, or commit a small fixture).
- **Reach states honestly.**
  A `?test` injection substitutes a fixed, obviously fake value at the one point the real code reads a file or the network, so the capture is the real rendering; `?test` alone is a no-op, nothing writes to `localStorage`, and a state that races (a scan that finishes in milliseconds) gets a `freeze_...` flag.
  Prefer an injection to `page.route` stubbing when both reach the same state.
- **Merge main before reading a diff.**
  The baseline is the branch's own last build.
- **A canvas is not in the archive.**
  The DOM archive carries a canvas element's size, not its pixels.
  Either stand a screenshot in for it before the end of the test (usage-page's `inlineMapCanvas`) or keep a Playwright `toHaveScreenshot` suite with committed PNGs for that one section.

## When the repo is a BBQS companion app

`@brain-bbqs/config` and `@brain-bbqs/test-utils` (from [bbqs-web-components](https://github.com/brain-bbqs/bbqs-web-components)) already contain steps 2, 4 and 5; use them instead of the vanilla templates, so the app does not carry a copy that drifts:

```ts
// configs/storybook/main.ts
import { createStorybookMain } from "@brain-bbqs/config/storybook";
export default createStorybookMain({ packageJson: new URL("../../package.json", import.meta.url) });

// configs/storybook/preview.ts
import "../../src/style.css";
import { storybookPreview } from "@brain-bbqs/config/storybook-preview";
export default { ...storybookPreview }; // spread: Storybook parses the default export statically

// configs/playwright.chromatic.config.ts
import { defineConfig } from "@playwright/test";
import { createPlaywrightConfig } from "@brain-bbqs/config/playwright";
export default defineConfig(
  createPlaywrightConfig({ rootDir: new URL("..", import.meta.url), testDir: "../tests/chromatic" }),
);

// tests/chromatic/app.chromatic.test.ts
import { expectNoHorizontalOverflow, forEachViewport } from "@brain-bbqs/test-utils/playwright";
```

`resolveAppVersion` in that package already honors `CHROMATIC_STATIC_VERSION`.
A repository generated from `bbqs-web-app-template` has all of this, plus the two workflows, in place; what it still needs is step 6 and the README.

## When pull requests come from forks

Secrets are not available to a fork's pull request, so the workflows above cannot upload for it.
dandi/usage-page, which takes outside contributions, splits each workflow in two: `chromatic.yml` and `chromatic-playwright.yml` build with no token (Storybook via `build-storybook`, the archives via `build-archive-storybook --output-dir=storybook-static`) and upload `storybook-static/` as a one-day artifact; `chromatic-publish.yml` runs on `workflow_run`, from `main` and therefore with the tokens, checks out the built commit by hash for the git history Chromatic reads baselines from, downloads the artifact, and runs the CLI with `--storybook-build-dir`, `--exit-zero-on-changes`, `CHROMATIC_SHA`/`CHROMATIC_BRANCH`/`CHROMATIC_SLUG` set from the triggering run, and `--auto-accept-changes` only for a push to the repository's own `main`.
Copy those three files from that repository when this applies; the single-workflow form is right for a repository whose contributors all push branches to it.

## Troubleshooting

| Symptom                                                                   | Cause and fix                                                                                                                                  |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Only one viewport's captures reach Chromatic                              | Viewports were Playwright projects; Chromatic keys archives by title. Use `forEachViewport`.                                                   |
| `Chromatic archives directory cannot be found`                            | A custom `outputDir` in the Playwright config, or the tests did not run. Leave `outputDir` alone or set `CHROMATIC_ARCHIVE_LOCATION` to match. |
| `build-archive-storybook` ignores `--output-dir`                          | It was run through `npm exec`, which eats the flag. Call `./node_modules/.bin/build-archive-storybook` directly.                               |
| `Failed to run chromatic --playwright`                                    | No Chromium project; Chromatic archives only from Chromium.                                                                                    |
| Every story re-snapshotted after a version bump                           | The version stamp is not pinned under `CHROMATIC_STATIC_VERSION` in the Vite config Storybook loads (or in `viteFinal`, when it loads none).   |
| Text pixels moved with no code change                                     | The runner image changed (compare the printed `ImageVersion`), or the branch is behind `main`. Accept, or merge `main` and re-read.            |
| Workflow fails on a Dependabot or fork branch                             | No secrets there. The `dependabot[bot]` guard skips the former; for forks, see the section above.                                              |
| `ERR_REQUIRE_ESM` or Node version errors from `@chromatic-com/playwright` | 0.15+ is ESM-only and needs Node 22; raise `node-version` in the workflow.                                                                     |
| Stories show the wrong theme on CI                                        | Nothing pins it; the runner's OS preference won. Add the preview decorator and `withTheme`.                                                    |
| The raw `index.html` story shows broken images                            | Its `/src/assets/...` URLs bypass Vite; add the `staticDirs` mount in `main.ts`.                                                               |
