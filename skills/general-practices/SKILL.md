---
name: general-practices
description: Language-agnostic practices that every <language>-practices guide builds on — how to weigh the guides (the project's own rules first, then house preferences and tie-breakers, never a checklist that overrides judgment), the static and consent marks on their tools and who may grant consent, the finding categories, the architecture principles (one source of truth, boundaries and direction, effects at the edges, cohesion and size, a deliberate public surface with one deprecation cycle, cross-cutting concerns solved once), and how to add a guide. Use with any <language>-practices guide when writing, changing, or reviewing code, including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# General practices

What holds for every language, for the three kinds of work the
`<language>-practices` guides serve: writing or changing code, reviewing
a pull request, and the code-quality reviews (`review-repo-code-quality`,
`review-org-code-quality`). Each guide adds its language to this one;
read this first.

## How to weigh the guides

- **The project comes first.** Its stated rules (`AGENTS.md`,
  `CONTRIBUTING.md`, its linter and formatter configuration, a documented
  deprecation policy) win over every guide, and consistency with the
  surrounding code comes next. A guide's practices are defaults and
  tie-breakers after those. Its house preferences, such as pixi for
  Python environments, are recommendations, never findings against a
  project that chose otherwise.
- **The guides are not a checklist.** They record the choices these
  projects make and the pitfalls worth knowing. They do not replace your
  own knowledge of the language, or what a careful reviewer notices
  anyway: a check that does not fit the code at hand is skipped, and a
  problem no guide lists is still a problem.
- **Facts age.** Version numbers, tool flags, and tool behavior in the
  guides name the versions they were checked on. Where a tool now
  behaves differently, follow what it does and say so; the guide is then
  due a fix, which `suggest-skill-fixes` can propose.
- **Writing and reviewing use the same guide.** When writing code, follow
  Project rules and Checks, leave Not findings alone, and run the
  Verification commands that apply. When reviewing, report against them,
  and name the guide a finding comes from.

## Tool marks

Each guide's Tools table marks every tool:

- **static**: reads the source and nothing else of the repository's. It
  runs no repository code, loads none of the repository's configuration,
  plugins, or ignore files, builds and installs nothing, and writes
  nothing into the repository. `review-repo-code-quality` Step 1 shows how
  to run such a tool so that this holds: from a scratch directory outside
  the checkout, on explicit file lists or a copy of the tracked files.
- **consent**: everything else, because it runs project code: the
  project's own linter configuration and plugins, a type check or build,
  a dependency install, the test suite, a tool the project pins and
  installs.

Consent is given for one repository by whoever is in charge of the run:
the person who asked, or the skill that called this one, which may
withhold it. Each consumer says how it treats a consent tool. A
code-quality review takes consent as an input. A pull-request review
never runs a pull request's code, and reads such a tool's result from CI
instead. When you write code in a checkout you were asked to work in,
running the project's own tools is part of the work.

## Finding categories

The guides tag each check with the category it usually lands in:

| Prefix | Category | Contains |
|---|---|---|
| `ARC` | Architecture | The principles below: a fact defined in several places, boundaries crossed or dependencies pointing the wrong way, import cycles, effects outside the edges, cohesion and public-surface problems |
| `DC` | Dead code | Unreferenced symbols, unreachable branches, inert config |
| `DUP` | Duplication | Verbatim or near-verbatim repeats, drifted twins |
| `CON` | Consolidation | Structural tidy-ups that remove a concept rather than a line |
| `CL` | Cleanup | Local idiom fixes, naming, annotations |
| `NV` | Needs verification | Observations whose fix would change behavior, or that need a maintainer's judgment |

A change in any of the first five keeps observable behavior; anything
that would change it is `NV`, whatever it otherwise is.

## Architecture principles

Measure code against the project's own stated design first, and against
these second:

- **One source of truth.** A fact the code depends on — a closed set of
  allowed values, a constant, a schema, a default, a version string — is
  defined once and referenced everywhere else. A long or growing set of
  values spelled out in several places (signatures, validation lists,
  command-line choices, documentation, comparisons) belongs in one named,
  enumerated type; the guide gives that language's idiom and its
  pitfalls.
- **Boundaries and direction.** Dependencies point one way: entry points
  call into the core, the core does not import them, and lower layers do
  not reach up. Import cycles are findings, and so is reaching into
  another module's private names where a public interface exists.
- **Effects at the edges.** Reading the environment and configuration,
  network and filesystem access, logging setup, and global state live in
  a few named places near the entry points, not in code that runs when a
  module is loaded and not scattered through the core.
- **Cohesion and size.** A module, type, or function does one job. Name
  the outliers in length and complexity relative to the rest of this
  codebase, with their numbers (`lizard`, a static tool, measures most
  languages; a guide may name a native one). Pass-through layers,
  single-implementation abstractions, and wrappers that add nothing are
  candidates for removal.
- **A deliberate public surface.** What the project exposes — documented
  API, command-line interface, file formats, configuration keys,
  environment variables, routes and URLs, entry points — is chosen and
  kept small, and internals are marked with the language's convention
  (each guide's Public surface and deprecation group). A change to that
  surface is a behavior change (`NV`) unless a
  compatibility path (a re-export, an alias, a redirect, a deprecation
  period) keeps every existing caller working. Unless the project states
  its own deprecation policy, which then applies, retiring something
  public takes three steps: soft deprecation, documented with no warning
  (PEP 387's term); a run-time warning in the language's form once
  removal is planned; removal in a later major release (under SemVer, or
  a new minor release before 1.0). A removal that breaks the project's
  compatibility promise is a finding of its own; keeping the promise but
  skipping a step is a smaller one.
- **Cross-cutting concerns solved once.** Retries, timeouts, caching,
  validation, and error reporting are implemented once and reused, not
  rewritten at each call site. Each job has one library: two libraries
  doing the same job (HTTP clients, date handling, logging, command-line
  parsing, serialization) are a finding that names the one to keep —
  `CON` only when a trace shows every moved call site keeps its output,
  defaults, and errors, otherwise `NV`; dropping a dependency that
  shipped code exposes is always `NV`.

## Adding a guide

Every guide has the same sections: **Recognize** (the files it covers),
**Project rules** (where the language keeps its configuration, and the
version settings that bound what may be proposed), **Tools** (for each
sweep, a tool marked **static** or **consent**, including a way to draw
the import graph), **Checks** (each with the category it usually lands
in; among them the idiom for a closed set of values, a **Public surface
and deprecation** group, and a **Currency** group), **Not findings**
(what looks dead or wrong in that language but is not), and
**Verification** (the commands that show a change preserved behavior).
Each also says, after its intro, which kinds of projects it is written
for.

To add a language, add a sibling `<language>-practices` skill
(`user-invocable: false`, `allowed-tools: Read`, its own `apm.yml`
depending on `general-practices`) with those sections, a row in
`review-repo-code-quality`'s guide table and in the repository's README,
and an entry under `dependencies` in `review-repo-code-quality`'s and
`review-org-code-quality`'s `apm.yml`. A framework gets its own guide the
same way, `<language>-<framework>-practices`, holding only what the
framework adds; it names the guide it builds on, and its `apm.yml`
depends on that guide.
