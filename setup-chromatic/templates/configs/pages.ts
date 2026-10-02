/**
 * Every page of the app, listed once (several pages only; a one-page app has no need of this).
 * The Vite config builds its entry list from `file`; the Chromatic suite visits `path`, the URL the
 * app's own links use, and expects `heading` there. A page missing here is served by the dev
 * server but left out of the build, of the preview and of the snapshots.
 */
export const PAGES = [
  { name: "Index", file: "index.html", path: "/", heading: "App Name" },
  { name: "About", file: "about.html", path: "/about.html", heading: "About" },
  { name: "Help", file: "help/index.html", path: "/help/", heading: "Help" },
] as const;

export type PageName = (typeof PAGES)[number]["name"];
