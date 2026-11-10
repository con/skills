import type { Preview } from "@storybook/html-vite";
import "../../src/style.css";

const preview: Preview = {
  parameters: {
    // The app's stylesheet themes <body> itself, so Storybook's own background layer is disabled
    // rather than painted over it.
    backgrounds: { disable: true },
    // Chromatic renders every story once per mode, each with its own baseline and approval, by
    // setting the `theme` global that the decorator below reads. Stories therefore export one
    // story per state and get both themes from here.
    chromatic: {
      modes: {
        light: { theme: "light" },
        dark: { theme: "dark" },
      },
    },
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
    // color-scheme preference of whichever machine renders it. If the app themes through a class
    // or a stored key instead of data-theme, set that here instead; something explicit must pin it.
    (story, context) => {
      document.documentElement.dataset.theme = context.globals.theme ?? "light";
      return story();
    },
  ],
};

export default preview;
