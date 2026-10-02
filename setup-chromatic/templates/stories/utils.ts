// Defined by the app's Vite config, which Storybook loads too (see configs/storybook/main.ts).
declare const __APP_VERSION__: string;

/** Centers a component at a realistic width, the way the page shell would. */
export function withCard(element: HTMLElement): HTMLDivElement {
  const wrapper = document.createElement("div");
  wrapper.style.maxWidth = "640px";
  wrapper.style.margin = "1.5rem auto";
  wrapper.appendChild(element);
  return wrapper;
}

/**
 * Turns a page's markup (an `?raw` import of its HTML file) into an element Storybook can render:
 * the <body> content with the page's scripts removed, then whatever `apply` does to reach a page
 * state, by hand, since none of the app's script runs here. Shared by every page story so a
 * second page never carries a drifting copy of this.
 */
export function buildPage(rawHtml: string, apply?: (page: HTMLElement) => void): HTMLElement {
  const doc = new DOMParser().parseFromString(rawHtml, "text/html");
  // The page's own <script type="module"> wires up real behavior; the story needs only the markup.
  doc.body.querySelectorAll("script").forEach((s) => s.remove());
  const page = document.createElement("div");
  page.innerHTML = doc.body.innerHTML;
  // The one thing the app's script renders before anything is loaded; an empty version anchor is
  // invisible in a snapshot.
  const version = page.querySelector("#version-indicator");
  if (version) version.textContent = `v${__APP_VERSION__}`;
  apply?.(page);
  return page;
}
