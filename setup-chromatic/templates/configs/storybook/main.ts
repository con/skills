import type { StorybookConfig } from "@storybook/html-vite";

const config: StorybookConfig = {
  // Stories live beside the app rather than in src/, so a story is never mistaken for shipped code.
  stories: ["../../stories/**/*.stories.@(js|ts)"],
  // No addons: the stories exist to be snapshotted and looked at, nothing more.
  addons: [],
  framework: { name: "@storybook/html-vite", options: {} },
  // Only needed when a page story injects its HTML raw: the markup's /src/assets/... URLs bypass
  // Vite's asset pipeline, so the folder is served at that same path in dev and in the built
  // Storybook.
  staticDirs: [{ from: "../../src/assets", to: "/src/assets" }],
};

export default config;
