---
name: python-practices
description: Python practices for scientific Python packages — the house's preferences (pyproject metadata and dependency groups, pixi environments, SPEC 0 support windows, one Enum for a growing Literal set, no import-time effects, NumPy's Generator, pytest idioms), public surface and deprecation, false positives, and verification, with the review tools and detailed checks in references/review.md. Use when writing, changing, or reviewing Python code, including in a pull-request review or a code-quality review.
allowed-tools: Read
user-invocable: false
---

# Python practices

The house's practices for Python code, for three kinds of work: writing or
changing it, reviewing a pull request, and the code-quality reviews. Read
`general-practices` first: it says how to weigh these preferences against
the project's own rules and your own judgment, and defines the marks and
categories used here. [references/review.md](references/review.md) holds
what a review needs beyond them: the tools with their **static** /
**consent** marks, the detailed checks with their categories and pitfalls,
currency sources, and verification commands.

It is written for pure-Python scientific packages and command-line tools
on the NumPy stack, tested with pytest. Web frameworks and compiled
extensions are left out: check their conventions before reporting there.

## Recognize

`*.py` files, scripts without an extension whose shebang runs `python`,
and Jupyter notebooks (`*.ipynb`) when the scope includes them. Generated
code is out of scope unless the project edits it by hand: version files
written by setuptools-scm, hatch-vcs, or versioneer, a vendored
`versioneer.py`, and other vendored packages.

## Project rules

Read `pyproject.toml` (`[project]`, `requires-python`, the `[tool.*]`
tables), the environment and lock files (`pixi.toml` / `pixi.lock`,
`uv.lock`, `environment.yml`), `tox.ini` or `noxfile.py`,
`.pre-commit-config.yaml`, and the CI matrix. The oldest supported Python
bounds what may be proposed: no `match` or run-time `X | Y` before 3.10,
no `enum.StrEnum` or `typing.Self` before 3.11.

## Preferences

- **Packaging**: metadata in `[project]` (PEP 621) with a declared build
  backend, development, test, and documentation dependencies in
  `[dependency-groups]` (PEP 735), an SPDX `license` (PEP 639), and
  releases through PyPI Trusted Publishing.
- **Environments, locks, and tools**: pixi, as a house recommendation; a
  project that chose uv, conda, or pip-tools keeps its choice.
- **Supported versions**: Python and core dependencies per SPEC 0, or the
  policy the project states; CI tests the oldest and newest supported
  Python, and `requires-python`, classifiers, and CI agree.
- **One source of truth**: a long or growing `Literal` set becomes one
  `Enum` (`enum.StrEnum` from 3.11), reached safely through one alias
  whose run-time copies come from `typing.get_args`; constants, versions,
  and pins are defined once.
- **Modules**: imports at the top, except to break a cycle or defer a
  slow or optional dependency; nothing with effects at import time
  (`logging.basicConfig`, warnings filters, `matplotlib.use`, environment
  reads, file or network access).
- **Data and state**: a `dataclass`, `TypedDict`, or `NamedTuple` for a
  fixed set of keys passed between functions; no mutable defaults, no
  broad `except` that swallows errors, `logging` rather than `print` in
  library code.
- **NumPy**: one `np.random.default_rng(seed)` passed down, not the
  global random state, and none of the names NumPy removed (`np.float`,
  `np.NaN`, `np.product`, `np.trapz`).
- **Standard library over legacy**: `importlib.metadata` and
  `importlib.resources`, not `pkg_resources`; current typing spellings
  where the oldest supported Python has them.
- **Tests**: pytest, shared fixtures in the nearest `conftest.py`,
  `pytest.mark.parametrize` for tests that differ only in their data, and
  patches that name the module where the code looks the name up.
- **Lint and format**: ruff, where the project has not chosen otherwise.

## Public surface and deprecation

- **Internals** carry a leading underscore (modules and names), and
  `__all__` lists what a star import binds and the documentation
  promises; reaching into another package's `_name` is a finding
  (references/review.md, Imports and modules).
- **Deprecating** a public function, argument, or module: keep it
  working, and call `warnings.warn("…", DeprecationWarning, stacklevel=2)`
  where it is used, naming the replacement, or decorate it with
  `@warnings.deprecated("…")` (PEP 702; Python 3.13, else
  `typing_extensions.deprecated`), which type checkers also report at
  each use. `DeprecationWarning` is shown by default only in `__main__`
  and under test runners (PEP 565); a warning the users of an
  application must see is a `FutureWarning`.
- **Breaking changes**: the Public surface step under Verification in
  [references/review.md](references/review.md) lists them.

## Not findings

Names reached by string or by convention (entry points, plugin
registries, pytest fixtures and hooks, decorator-registered commands),
imports kept for their side effects (`# noqa: F401` with the reason),
public API that `__all__` or the documentation promises, and classes
stored in pickles or joblib files, which renaming breaks. The full list
is in [references/review.md](references/review.md).

## Verification

Run the project's own entry point before and after a change (`pixi run
…`, `tox`, `nox`, else `python -m pytest -q`), and its type checker and
`ruff check` where it configures them. A rewrite of array code compares
outputs exactly before and after. The review's commands are in
[references/review.md](references/review.md).
