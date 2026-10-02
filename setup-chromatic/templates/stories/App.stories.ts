// The page itself. Loaded through Vite's ?raw import so this story always mirrors the real markup
// in index.html. An app with several pages has one of these per page under stories/pages/
// (see stories/pages/Page.stories.ts) instead of this file.
import indexHtml from "../index.html?raw";
import { buildPage } from "./utils";

// fullscreen: the page fills the canvas edge to edge, as it does in the browser, instead of sitting
// inside Storybook's default padding.
export default { title: "App", parameters: { layout: "fullscreen" } };

export const Default = { name: "Default (nothing loaded)", render: () => buildPage(indexHtml) };

export const FileLoaded = {
  name: "File loaded",
  // Mirrors what main.ts renders once a file is in, by hand, since none of it runs here.
  render: () =>
    buildPage(indexHtml, (page) => {
      page.querySelector("#load-card")?.setAttribute("hidden", "");
      page.querySelector("#file-card")?.removeAttribute("hidden");
    }),
};
