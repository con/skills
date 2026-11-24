# Lens: frontend

Web user interfaces: components, pages, styles, templates, and the client
code that talks to a backend.

## Recognize

`*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.astro`; stylesheets (`*.css`,
`*.scss`, `*.less`, Tailwind configuration); HTML and server-side templates
(`*.html`, Jinja, Django, Handlebars); Storybook stories (`*.stories.*`);
end-to-end tests (Playwright, Cypress); bundler and framework configuration
(`vite.config.*`, `next.config.*`, `webpack.config.*`, `svelte.config.*`);
directories such as `components/`, `pages/`, `app/`, `public/`, `static/`.
A `package.json` that depends on React, Vue, Svelte, Angular or similar
marks the project as one.

## Context to read

The component library or design system the project already uses; how it
fetches data and holds state; its browser support (`browserslist`); its
accessibility and internationalization setup; whether it tests visual
changes (Storybook, Chromatic, Playwright snapshots); the backend contract
the changed views consume (schema, types, API client).

## Checks

**States the user can reach** (usually should-fix)
- Every new data-driven view handles loading, empty, error and partial
  data. A failed request must not leave a spinner forever or a blank page.
- Forms: double submission, validation messages, server errors shown to the
  user, and the state after a failed submit.

**Accessibility** (should-fix; blocking where the project commits to a
standard such as WCAG AA)
- Interactive elements are real `button`, `a` or `input` elements, not a
  `div` with a click handler; each input has a label; images that carry
  meaning have alternative text.
- Dialogs and menus move focus in, trap it, and return it when they close;
  everything works with the keyboard alone.
- ARIA attributes are correct and necessary (a wrong `role` is worse than
  none); new colours meet the contrast the project targets; motion respects
  `prefers-reduced-motion`.

**Security** (usually blocking)
- `dangerouslySetInnerHTML`, `v-html`, `{@html}`, `innerHTML` or a template's
  "safe" filter with content that is not a constant, unless it is sanitized
  on that path.
- URLs built from user or API data placed in `href` or `src` without a
  scheme check (`javascript:`).
- Secrets in client code: anything in a variable the bundler exposes
  (`NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`) ships to every visitor. Tokens
  kept in `localStorage` are readable by any injected script.
- Requests that change state under cookie authentication without the
  project's CSRF protection.

**Effects and state** (usually should-fix)
- React effect dependency lists that are missing values (stale data) or
  include values recreated on every render (loops); effects that subscribe,
  start timers or fetch without cleanup or an `AbortController`.
- State copied from props and then never updated; list `key`s taken from
  the array index in lists that reorder; global state for what one
  component uses.

**Performance** (optional unless measured)
- A whole library imported for one function, or a large new dependency in
  the client bundle; unbounded lists rendered without virtualization;
  images without dimensions (layout shift); expensive work during render.

**Text and layout** (should-fix in projects that translate)
- New user-facing strings outside the project's translation mechanism;
  dates and numbers formatted without the locale; fixed widths that break
  on small screens or with long words.

**Tests** (should-fix for new behaviour)
- Behaviour tested through what the user sees (roles, labels, text), not
  component internals; visual changes covered by the project's stories or
  snapshots when it uses them.

## Not findings

- `useMemo` or `useCallback` missing where nothing shows a cost.
- `rel="noopener"` on `target="_blank"` links: browsers have implied it
  since 2021.
- Decorative elements hidden with `aria-hidden` lacking alternative text.
- Snapshot files changing as a consequence of an intended change.

## Verification

- **static**: read the changed components and the code paths that render
  them; search for the risky APIs named above; compare the `package.json` and lockfile diff
  for new client dependencies.
- **CI only**: building the bundle (it runs the project's configuration and
  plugins), component and end-to-end tests, Storybook, and accessibility
  checkers run against a build. The pull request's visual review and
  end-to-end runs are often the best evidence there is.
