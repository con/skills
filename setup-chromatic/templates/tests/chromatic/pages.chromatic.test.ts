import { test, expect } from "@chromatic-com/playwright";
import { PAGES } from "../../configs/pages";
import { expectNoHorizontalOverflow, forEachViewport } from "./viewports";

// The states every page has, registered once per page from the one list of pages. A page's own
// states live beside this file in <page>.chromatic.test.ts. The page's name leads every title:
// Chromatic groups captures by test file and title, so this one file stays readable by page, and
// Playwright rejects two identical titles in a file.
//
// The Chromatic fixture archives the page after each test body; the assertions are there so a
// capture of the wrong page or state fails here, by name, rather than turning up as a diff.

for (const { name, path, heading } of PAGES) {
  forEachViewport(test, `${name} - default`, async ({ page }) => {
    await page.goto(path);
    await expect(page.locator("h1")).toContainText(heading);
    await expectNoHorizontalOverflow(page);
  });

  forEachViewport(test, `${name} - dark theme`, async ({ page }) => {
    // Seeded before the page's own script reads it, the way a returning visitor's choice would be;
    // the key and value are whatever the app itself stores ("theme", "<app>.theme", ...).
    await page.addInitScript(() => localStorage.setItem("theme", "dark"));
    await page.goto(path);
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await expectNoHorizontalOverflow(page);
  });
}
