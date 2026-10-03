import { test, expect } from "@chromatic-com/playwright";
import { expectNoHorizontalOverflow, forEachViewport } from "./viewports";

// The one-page form: one forEachViewport call per page state. An app with several pages uses
// pages.chromatic.test.ts for the states every page has and one <page>.chromatic.test.ts per page
// for its own, instead of this file.
//
// The Chromatic fixture archives the page after each test body; the assertions are there so a
// capture of the wrong state fails here, by name, rather than turning up as a diff.

forEachViewport(test, "Main page - default", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("App Name");
  await expectNoHorizontalOverflow(page);
});

forEachViewport(test, "Main page - dark theme", async ({ page }) => {
  // The theme the app does not default to (rename and reseed when the default is dark), seeded
  // before the page's own script reads it, the way a returning visitor's choice would be; the key
  // and value are whatever the app itself stores ("theme", "<app>.theme", ...).
  await page.addInitScript(() => localStorage.setItem("theme", "dark"));
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expectNoHorizontalOverflow(page);
});

forEachViewport(test, "Main page - file loaded", async ({ page }) => {
  // The ?test&mock_file injection stands a fixed fake in for a dropped file (see the `?test`
  // injections in the app's entry script).
  await page.goto("/?test&mock_file");
  await expect(page.locator("#file-card")).toBeVisible();
  await expectNoHorizontalOverflow(page);
});
