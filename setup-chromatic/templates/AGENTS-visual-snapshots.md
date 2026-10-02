<!--
For the target repository's AGENTS.md / CLAUDE.md, or as a `visual-snapshots` skill under
.claude/skills/ (the BBQS apps keep it that way). The README is for people using the repo and does
not carry these rules.
-->
## Visual snapshots

Rules for the stories under `stories/` and the Chromatic tests under `tests/chromatic/`, distilled from Chromatic diffs that no code change explained.

- **One test per viewport, viewport in the title.** `forEachViewport`, never a Playwright project: Chromatic names an archive by the test's file, describe and title, never its project, so several projects write over one story file and only their viewports survive.
- **Fail on overflow by name.** Every snapshot test ends with `expectNoHorizontalOverflow`; the usual fix is a `@media (max-width: 600px)` rule that lets a row wrap.
- **Pin what changes on its own.** The version stamp (`CHROMATIC_STATIC_VERSION`, read by the Vite config), the runner image (`ubuntu-24.04`, printed by the workflow), the theme (the preview decorator and the Chromatic modes in Storybook, a seeded storage key in Playwright), media fixtures (a pinned encoder, a printed hash, or a committed file), dates, random ids, live fetches.
- **Reach states honestly.** A `?test` injection substitutes a fixed, obviously fake value at the one point the real code reads a file or the network, so the capture is the real rendering; `?test` alone is a no-op, nothing writes to storage, and a state that races gets a `freeze_...` flag. Prefer an injection to `page.route` stubbing when both reach the same state.
- **Merge main before reading a diff.** The baseline is the branch's own last build.
- **A canvas is not in the archive.** The DOM carries a canvas element's size, not its pixels: inline a screenshot of it before the test ends, or keep a Playwright `toHaveScreenshot` suite with committed PNGs for that one section.
- **Growing the suite.** A new component state gets a story (both themes come from the modes). A new page state gets a `forEachViewport` test and a deterministic way to reach it. A new page gets a line in `configs/pages.ts`, a story file under `stories/pages/`, and its own `<page>.chromatic.test.ts`; titles lead with the page's name.
