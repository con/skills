<!--
Three pieces for the target repository's README, in the README's own voice: short declarative
sentences, the why beside the what, one sentence per line where the repo does that, few em-dashes.
Replace <org>/<repo>, the component and page names, and the script names with the app's own.

1. Two badges in the centered header block, after the codecov/license/prettier row, each on its own
   line, linking to the workflow (or to the project's Chromatic library page,
   https://www.chromatic.com/library?appId=<appId>, when it is public).
-->
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

<!--
2. The commands, in the `## Development` / `### Tests` block the README already has (one command
   per line, an aligned `#` comment saying what each is).
-->
```bash
npm run storybook          # the component and page stories, live
npm run test:chromatic     # the page snapshots, in Chromium (nothing is uploaded)
```

<!--
3. The section. Where the README is kept to a short shape (logo, title, badges, one line, credits),
   the badges still go in the README and this section goes in docs/README.md beside the live test
   injections, which is where such repos keep what a developer needs to know.
-->
## Visual snapshots

Every push is rendered on [Chromatic](https://www.chromatic.com) and compared against the last accepted baseline, twice: once per story, once per page state.
The two feeds answer different questions, which is why there are two projects, two workflows and two badges.

### Stories versus Playwright snapshots

|                          | Storybook stories                                                                                                        | Playwright snapshots                                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| What is captured         | One component or page in one state, built by hand from fixed inputs, with none of the app's script running, in each theme | The real app, booted in Chromium and driven to a state the way a person would reach it, at desktop, tablet and phone sizes |
| Where it lives           | `stories/*.stories.ts` (the pages under `stories/pages/`)                                                                | `tests/chromatic/*.test.ts`                                                                                                |
| What a diff points at    | That component or page, in that state and theme                                                                          | The page as a whole: layout between components, overflow at narrow widths, what the real boot path rendered                |
| How it reaches Chromatic | The built Storybook (`npm run build-storybook`)                                                                          | An archive of the DOM that `@chromatic-com/playwright` records at the end of each test (`npm run test:chromatic`)          |
| Workflow and badge       | Chromatic (Storybook)                                                                                                    | Chromatic (Playwright)                                                                                                     |

A story is the place for a component's own states (idle, drag-over, rejected), each rendered in light and dark by Chromatic.
A Playwright snapshot is the place for a page state (nothing loaded, a file loaded, signed out) on each page of the app, since only the running app knows how its pieces fit together.
Neither keeps pixels in this repository: Chromatic renders both in its own browsers, holds the baselines, and a change is accepted or rejected in its review UI.

### Setup (once per repository)

1. Create two Chromatic projects for this repository: one for Storybook, then **Add project**, pick the same repository again, and name the second one for Playwright.
2. Add each project's token as a repository secret: `CHROMATIC_STORYBOOK_PROJECT_TOKEN` and `CHROMATIC_PLAYWRIGHT_PROJECT_TOKEN`.
3. Push. `chromatic-storybook.yml` and `chromatic-playwright.yml` under `.github/workflows/` run on every push; the first build of each project is its baseline, accepted by hand in Chromatic.

### Day to day

1. `npm run storybook` to look at the stories; `npm run test:chromatic` to run the page captures locally. Nothing is uploaded from a local run.
2. Push a branch. Each workflow uploads its captures, and Chromatic posts one status check per project.
3. Open the check and review each diff: accept what was intended, otherwise fix and push again. Chromatic diffs a branch against that branch's own last build, so merge `main` in first when the branch is behind, or `main`'s changes show up as yours.
4. A new component state gets a story; a new page state gets a `forEachViewport` test in `tests/chromatic/`, plus a way to reach it deterministically; a new page gets a story file under `stories/pages/`, a line in `configs/pages.ts`, and its own states in `tests/chromatic/<page>.chromatic.test.ts`.

<!--
Where the repo also compares pixels with Playwright's own `toHaveScreenshot` (dandi/usage-page
does, for a WebGL map that a DOM archive cannot carry), add one line saying that is a third kind:
pixels against PNGs committed beside the test, used only where Chromatic cannot see.
-->
