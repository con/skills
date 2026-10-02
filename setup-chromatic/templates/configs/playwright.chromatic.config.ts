import { defineConfig, devices } from "@playwright/test";

const PORT = 4173;
const baseURL = `http://localhost:${PORT}`;

// The ordinary suite's config (configs/playwright.config.ts) is this file with
// `testDir: "../tests/integration"`: identical settings, so a page renders the same under both.
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
  // One Desktop Chrome project, deliberately. Chromatic names a Playwright archive by the test's
  // file, describe and title, never its project, so several projects write over one story file
  // (viewport-only projects are recovered as modes on upload; anything else that differs is lost).
  // Viewports are set per test instead (tests/chromatic/viewports.ts), never as projects.
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    // The built app, served by vite preview; --strictPort so a preview of another app holding the
    // port cannot be tested in its place. Every page the Vite config lists as an entry is served.
    command: `npm run build && npm run preview -- --port ${PORT} --strictPort`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
