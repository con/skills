# Lens: packaging

Dependencies, build metadata, versions, releases and licensing: what decides
what users install and how it reaches them.

## Recognize

`pyproject.toml` (`[project]`, `[build-system]`, dependency groups),
`setup.py`, `setup.cfg`, `MANIFEST.in`, `requirements*.txt`,
`constraints*.txt`, `environment.yml`, `pixi.toml`; `package.json`
dependencies and scripts; `go.mod`, `Cargo.toml`, `Gemfile`; lockfiles
(`*.lock`, `package-lock.json`, `pnpm-lock.yaml`, `go.sum`, `pylock.toml`);
version files; `LICENSE`, `LICENSES/`, `REUSE.toml`; `CITATION.cff`,
`.zenodo.json`; release notes and changelog fragments (`changelog.d/`,
`newsfragments/`).

## Context to read

The supported versions (`requires-python`, `engines`, the CI matrix); how
the project releases (manual, label-driven such as intuit/auto, changelog
tools such as scriv or towncrier); whether it is a library (loose ranges,
no committed pins) or an application (locked); its license and policy on
dependency licenses.

## Checks

**Dependencies** (should-fix; blocking for a dependency that cannot be
installed or is unsafe)
- A new dependency is needed (not duplicating one already present),
  maintained, of reasonable size, and under a compatible license; heavy or
  rarely used ones are optional extras.
- Version ranges: a raised minimum is actually needed and tested; a library
  does not pin or cap without a stated reason; an application's lockfile
  changed together with its manifest, by the project's tool, without
  unrelated churn.
- A removed dependency is no longer imported anywhere, tests and scripts
  included.

**Build and distribution** (blocking when the built package breaks)
- Files needed at run time are included in the wheel or package; entry
  points and scripts point at code that exists; `requires-python` and
  classifiers agree with the CI matrix; a change of build backend is
  deliberate.

**Versions and releases** (should-fix; blocking when it cuts the wrong
release)
- The version change matches the change (a breaking change is a major
  version, or minor before 1.0); a changelog entry or fragment exists where
  the project requires one; release labels are right, since label-driven
  tools release from them (a stray `major` label cuts a major release).

**Licensing** (should-fix)
- New files carry the headers the project uses (REUSE); vendored code keeps
  its license; the license metadata matches `LICENSE`.

**Supply chain** (blocking when suspicious)
- Install hooks in new dependencies (npm `postinstall`); names that imitate
  popular packages; dependencies from URLs or git rather than the registry;
  lockfile entries resolved from unexpected hosts.

## Not findings

- Dependency bumps opened by bots (`bot-pr-sweep` handles those).
- A preference between environment tools (pip, uv, pixi, poetry) unless the
  project states one.

## Verification

- **static**: `git grep` for imports of added and removed dependencies;
  read the lockfile diff for unexpected packages and hosts.
- **consent**: resolving or installing the environment, building the
  package and listing its contents, and audit tools that install or build
  packages to resolve them (they can run build scripts).
