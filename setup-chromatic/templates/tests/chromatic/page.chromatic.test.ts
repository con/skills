import { test, expect } from "@chromatic-com/playwright";
import { expectNoHorizontalOverflow, forEachViewport } from "./viewports";

// One of these per page that has states of its own, named for the page (index.chromatic.test.ts,
// about.chromatic.test.ts). The states every page shares are in pages.chromatic.test.ts; only this
// page's are here, each title starting with the page's name, as there.

forEachViewport(test, "Index - file loaded", async ({ page }) => {
  // The ?test&mock_file injection stands a fixed fake in for a dropped file (SKILL.md, step 5).
  await page.goto("/?test&mock_file");
  await expect(page.locator("#file-card")).toBeVisible();
  await expectNoHorizontalOverflow(page);
});
