// One of these per HTML entry, named for the page (Index.stories.ts, About.stories.ts, ...): that
// page's own markup, imported raw, so the story cannot drift from it. Storybook finds stories by
// their static exports, so each page needs its own file; a loop over the pages cannot export them.
import aboutHtml from "../../about.html?raw";
import { buildPage } from "../utils";

// A page with a stylesheet of its own (one its HTML links that the shared one from
// configs/storybook/preview.ts does not cover) imports it here:
// import "../../src/about.css";

// Titles nest under "Pages/" so the page stories sit together, apart from the components; each
// file's title must differ (Storybook indexes stories by title and export name). fullscreen: the
// page fills the canvas edge to edge, as in the browser, instead of sitting inside the default padding.
export default { title: "Pages/About", parameters: { layout: "fullscreen" } };

export const Default = { name: "Default", render: () => buildPage(aboutHtml) };

// A state the page's script would produce is applied by hand, the way stories/App.stories.ts does:
// export const Expanded = {
//   name: "Details expanded",
//   render: () => buildPage(aboutHtml, (page) => page.querySelector("details")?.setAttribute("open", "")),
// };
