# When a shared package already carries the configs

Some organizations keep the Storybook and Playwright configuration, and the test helpers, in a node package of their own that every app depends on: a workspace package in a monorepo, a package vendored into the repo, or one installed from npm or a git URL.
The BBQS apps do this with `@brain-bbqs/config` and `@brain-bbqs/test-utils` from [bbqs-web-components](https://github.com/brain-bbqs/bbqs-web-components).
When the repo has such a package, use what it exports instead of the vanilla templates, so the app does not carry a copy that drifts from the package and from the other apps that use it.

## How to tell

Look in `package.json` for a dependency of the organization's own (`@<org>/config`, `@<org>/test-utils`, a `workspace:` or `file:` reference, a git URL) and read its exports.
The pieces to look for, each replacing one template:

| The package exports                                                     | It replaces                                                  |
| ----------------------------------------------------------------------- | ------------------------------------------------------------ |
| A Storybook main factory (framework, stories glob, `__APP_VERSION__`)   | `templates/configs/storybook/main.ts`                        |
| A preview object (background off, theme global, decorator, modes)       | `templates/configs/storybook/preview.ts`, minus the CSS import |
| A Playwright config factory (one Chromium project, preview web server)  | `templates/configs/playwright.chromatic.config.ts`           |
| Viewport helpers (`forEachViewport`, `expectNoHorizontalOverflow`)      | `templates/tests/chromatic/viewports.ts`                     |
| Story helpers (`withCard`, `buildPage`)                                 | `templates/stories/utils.ts`                                 |
| A version resolver that honors `CHROMATIC_STATIC_VERSION`               | The pin in step 8 of SKILL.md                                |

Whatever the package does not export, the app takes from the templates, and the right fix is to move that piece into the package afterwards (its own PR, per its conventions) rather than let every app grow a copy.

## What the app's files become

The BBQS form, as an example:

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

// tests/chromatic/app.chromatic.test.ts (or pages.chromatic.test.ts)
import { expectNoHorizontalOverflow, forEachViewport } from "@brain-bbqs/test-utils/playwright";
```

Things to check against the package rather than assume:

- **The version pin.** `resolveAppVersion` in `@brain-bbqs/config` honors `CHROMATIC_STATIC_VERSION`; another package's resolver may not, and then a version bump re-snapshots everything until it does.
- **The Vite config.** A factory such as `createViteConfig` may own `build`; a multi-page app's entry list (`build.rollupOptions.input` from `configs/pages.ts`, see `several-pages.md`) goes through the factory's override mechanism, not beside it.
- **Modes.** If the package's preview object predates Chromatic modes (the BBQS one themes through a global and decorator but declares no `chromatic.modes`), add the `parameters.chromatic.modes` block from the template to the package, or spread it over the import in the app's `preview.ts` until the package has it.
- **A static asset mount.** Page stories that inject HTML raw still need the `staticDirs` entry; pass it through the factory's option for it, as the BBQS apps do.
- **`testInfo` in `forEachViewport`.** A mid-test `takeSnapshot(page, name, testInfo)` needs the helper to hand `testInfo` to its body, as the template's third argument does; the BBQS helper does not yet, so add that one-line pass-through to the package before a test relies on it.

A repository generated from a project template that already depends on the package (the BBQS apps come from [bbqs-web-app-template](https://github.com/brain-bbqs/bbqs-web-app-template)) may already have the configs, helpers and workflows; check which of steps 1 to 8 it covers, then do the rest, which is at least the Chromatic projects and secrets (step 6) and the README section (step 9).
