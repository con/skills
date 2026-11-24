# Lens: docs

Documentation for people: guides, references, READMEs, tutorials,
changelogs and docstrings that a user reads.

## Recognize

`*.md`, `*.rst`, `*.adoc` and `*.txt` meant for readers; `docs/`, `README*`,
`CHANGELOG*`, `CONTRIBUTING*`; documentation tooling (`mkdocs.yml`, Sphinx
`conf.py`, Docusaurus or Jekyll configuration); man pages; notebooks used as
tutorials; changes that touch only docstrings and comments.

## Context to read

Who reads these pages (users, contributors, operators) and what they arrive
knowing; the documentation's structure and style guide; how it is built and
versioned; the code the pages describe, at the reviewed commit.

## Checks

**Accuracy** (blocking when following the page breaks something; else
should-fix)
- Every command, flag, option, default value, path, function name and
  output shown matches the code at the reviewed commit. Check each one.
- Version-specific statements say which versions; internal links and
  anchors resolve; examples run as written.
- Commands that delete, overwrite or publish say so before the reader runs
  them.
- A deprecated feature stays documented until it is removed, marked with
  the release that deprecated it, its replacement, and the planned removal
  where one is set (Sphinx's `deprecated` directive, for example); a
  removal comes with a migration note.

**Structure** (optional; should-fix when it misleads)
- The page leads with what the reader needs; prerequisites come before the
  steps that need them; the steps are in order; there is one recommended
  way, not three; terms match the rest of the documentation.

**Clarity** (optional)
- Passages that are hard to follow. If your companion skills include
  `review-human-prose`, use its cues for them.

**Rendering** (should-fix)
- Markup that renders wrongly: unclosed code fences, skipped heading
  levels, broken tables, unknown directives, relative links that break in
  the rendered site.

**Safety** (blocking)
- No secrets, internal host names or personal paths in examples.

## Not findings

- Style choices the project's documentation already makes consistently.

## Verification

- **static**: compare each documented command and option with the code
  (argument parsers, configuration schemas, function signatures); search
  for every other page that mentions a changed name.
- **CI only**: building the documentation (Sphinx's `conf.py` and MkDocs
  plugins are code); running the examples; link checkers that fetch URLs.
