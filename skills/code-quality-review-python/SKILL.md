---
name: code-quality-review-python
version: 0.1.0
description: Python guide for the code-quality review skills — where a Python project states its rules, which tools sweep it (each marked static or needing execution consent), Python checks such as a long or growing Literal list that belongs in one Enum, currency checks (supported Python versions, PEPs, PyPA packaging standards, pixi for environments and locks), Python false positives to reject, and the commands that verify a change. review-repo-code-quality reads it for Python code, and review-org-code-quality uses its static tools. Use when a review skill tells you to read it, or when asked for a code-quality review of Python code (then run review-repo-code-quality, which loads this guide).
allowed-tools: Read, Skill
user-invocable: true
---

# Python guide for the code-quality reviews

`review-repo-code-quality` holds the review procedure, the report layout,
and the architecture principles that apply to every language; this guide
adds what holds for Python only. That skill reads it in Step 1 for every
repository with Python code in scope, and `review-org-code-quality` uses
its **static** tools in Phase 2. The category prefixes (`ARC`, `DC`,
`DUP`, `CON`, `CL`, `NV`) and the **static** / **consent** marks are
defined in `review-repo-code-quality`.

## When invoked directly

This guide is not a review on its own. Asked for a Python code-quality
review, or for this guide by name, run `review-repo-code-quality` (with
`Skill`, or by reading `../review-repo-code-quality/SKILL.md`); its Step 1
loads this guide. Limit that review to the Python code only when the user
asked for that; otherwise it covers every language in the repository,
each with its own guide. If `review-repo-code-quality` is not installed,
stop and ask the user to install it; do not review from this guide alone.

## Recognize

`*.py` and `*.pyi` files, scripts without an extension whose shebang runs
`python`, and Jupyter notebooks (`*.ipynb`) when the scope includes them.
Generated code is out of scope unless the project edits it by hand:
version files written by setuptools-scm or versioneer, protobuf and gRPC
stubs (`*_pb2.py`, `*_pb2_grpc.py`), and vendored packages.

## Project rules

Besides the files `review-repo-code-quality` Step 1 names, read
`pyproject.toml` — `[project]` (`requires-python`, dependencies and
optional dependencies, `scripts`, `entry-points`) and the `[tool.*]`
tables for ruff, mypy, pyright, pytest, coverage and vulture — and
whichever of these exist: `setup.cfg`, `setup.py`, `ruff.toml` /
`.ruff.toml`, `mypy.ini` / `.mypy.ini`, `pyrightconfig.json`, `.flake8`,
`.pylintrc` / `pylintrc`, `tox.ini`, `noxfile.py`,
`.pre-commit-config.yaml`, `requirements*.txt`, `constraints*.txt`, the
environment files (`pixi.toml` or `[tool.pixi]` in `pyproject.toml`,
`environment.yml`, `.python-version`), and the lock file (`pixi.lock`,
`uv.lock`, `poetry.lock`, `pdm.lock`, `pylock.toml`). `setup.py`,
`noxfile.py` and `conftest.py` are code: read them as text.

The oldest Python the project supports — `requires-python`, else the
oldest version CI tests — bounds what may be proposed: no `X | Y` union
evaluated at run time before 3.10, no `match` before 3.10, no
`enum.StrEnum` or `typing.Self` before 3.11. Pass it to ruff as
`--target-version` so its `UP` rules hold to the same bound.

## Tools

Run each from a scratch directory, with paths pointing into the checkout:
`vulture` reads `[tool.vulture]` from the `pyproject.toml` in its working
directory.

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Dead code | `vulture` | static | `vulture <paths> --min-confidence 60`; again without `--min-confidence` for the long tail |
| Idiom drift | `ruff`, your configuration | static | `ruff check --isolated --no-cache --target-version py3XX --select E,F,W,B,UP,RET,SIM,C4,PIE,PERF,PLR,PLC0415 --output-format concise --statistics <paths>` |
| Idiom drift | `ruff`, the project's configuration | consent | `ruff check --no-cache --extend-select B,UP,RET,SIM,C4,PIE,PERF,PLR --statistics` from the checkout |
| Types | the project's mypy or pyright setup | consent | the project's own invocation |
| Dependencies | `deptry` | consent: maps distributions to modules through the installed project | `deptry .` from the checkout |
| Import graph | `ruff analyze graph` (experimental) | static | `ruff analyze graph --isolated <paths>`; `--direction dependents` for the reverse map |
| Complexity | `ruff` | static | `ruff check --isolated --no-cache --select C901,PLR0911,PLR0912,PLR0913,PLR0915 --statistics <paths>`, or `lizard -l python <paths>` |
| Tests | the project's runner | consent | see Verification |

With `--isolated`, ruff ignores the project's `per-file-ignores` and
disabled rules: read them from its configuration and drop those hits.

## Checks

Each check names the category it usually lands in. A fix that would
change behavior goes under `NV` instead, with the change spelled out.

**Closed sets and constants**

- **A long or growing `Literal` list becomes one `Enum`** (`ARC`; `CON`
  when it stays inside one module). A `Literal[...]` of more than a
  handful of values, or one that has gained values over time, will need
  updating again. When it is repeated across signatures, mirrored by a
  run-time tuple or set (validation, `argparse` `choices`, `click.Choice`),
  or compared against bare strings elsewhere, define one `Enum` —
  `enum.StrEnum` from Python 3.11, `class Mode(str, Enum)` before — and
  use it in every annotation, choice list, and comparison. Keep short,
  stable sets as `Literal` (`Literal["r", "w"]`); one named `Literal` alias
  is enough when nothing at run time needs the list. Before rating the
  change **High**, trace every place a value crosses a boundary: pydantic
  models (`model_dump()` returns members unless `use_enum_values` or JSON
  mode is set), YAML dumpers and custom JSON encoders, database columns,
  pickles, and formatting — `str()` and f-strings of a `(str, Enum)` member
  give `"Mode.FAST"`, not `"fast"` (`StrEnum` gives the value). Type
  checkers also reject callers that pass plain strings, so for a public
  function the switch is an API change (`NV`).
- **The same magic value in several modules** (`CON`): one named constant,
  or a member of the `Enum` above. `PLR2004` finds the comparisons.
- **Dicts with a fixed set of keys passed between functions** (`ARC`):
  a `dataclass`, `TypedDict`, or `NamedTuple` makes the shape one
  definition. Code that serializes, mutates, or `**`-unpacks the dict
  makes the switch `NV`.

**Imports and modules**

- **Import cycles** (`ARC`): `ruff analyze graph` shows them, and so do
  imports moved into functions or under `if TYPE_CHECKING:` to dodge one.
  Name the cycle and the move that breaks it. `TYPE_CHECKING` imports used
  only in annotations are fine.
- **Function-local imports** (`CL`; `PLC0415`) with no cycle to break and
  no slow or optional dependency to defer move to the top of the module.
  Keep the ones that do either, and say which.
- **Private imports** (`ARC`): `from pkg._impl import X` where `pkg`
  exports `X` publicly, and private names imported across package
  boundaries.
- **Effects at import time** (`ARC`): `logging.basicConfig`, environment
  variables read into module constants, file or network access, `sys.path`
  edits, and registrations. Moving them into a function the entry point
  calls changes when they happen; trace every importer, tests included.
- **`__all__` drift** (`CL`): names listed but not defined, or public
  names the documentation presents but `__all__` leaves out.
- **Star imports** (`CL`; `F403`, `F405`) outside an `__init__.py` that
  re-exports.

**Idioms** (`CL`; ruff finds most — group its hits by rule)

- assign-then-return (`RET504`), `else` after `return` (`RET505`),
  collapsible `if` (`SIM102`), `key in d.keys()` (`SIM118`),
  `d.get(k, None)` (`SIM910`), repeated `isinstance` calls (`SIM101`),
  needless comprehensions and conversions such as `list(sorted(...))`
  (`C4`), `pass` in a non-empty body (`PIE790`), loops that only build a
  list (`PERF401`);
- old typing spellings (`typing.List`, `Optional[X]`; `UP006`, `UP007`,
  `UP035`, `UP045`) where the oldest supported Python has the new ones;
- `any(...)` written to mean "not empty": `if xs:` is the same only when
  no element can be falsy;
- `open()` outside a `with` block (`SIM115`) — `CL` when every path
  already closes the file, else `NV`.

**Errors and state** (usually `NV`: the fix changes behavior)

- broad or bare `except` that swallows errors (`BLE001`, `E722`, `S110`);
- mutable default arguments and class attributes (`B006`, `RUF012`);
- module state changed through `global` (`PLW0603`);
- `print` in library code where the project logs (`T201`).

**Types** (`CL`): `Any` where the concrete type is known; `# type: ignore`
without an error code (`PGH003`); annotations that disagree with what the
function returns (confirm with the type checker under consent).

**Packaging and dependencies**

- metadata declared in both `setup.py` / `setup.cfg` and `pyproject.toml`,
  or one version string kept in several files (`CON`);
- dependencies declared for run time but never imported by shipped code
  (`deptry` `DEP002`; it skips `tests/` by default, so this also catches
  dependencies only tests use), imported but not declared (`DEP001`), or
  only reachable through another package (`DEP003`), and development
  dependencies that shipped code imports (`DEP004`) — `DC`, or `NV` when
  the fix changes what installs;
- the same pins repeated across `requirements*.txt`, `tox.ini`, CI, and
  `pyproject.toml` (`CON`);
- a `requires-python` lower bound that CI never tests (`NV`: the claim or
  the test matrix has to change).

**Currency** — check the live sources below on the day of the review and
cite them with the date; the examples here are a starting point, not the
current state. Moving the version floor or switching tools is usually
`NV`, a maintainer's decision.

- **Python versions.** Compare `requires-python`, the
  `Programming Language :: Python :: 3.x` classifiers, and the CI matrix
  with the status of each version at https://devguide.python.org/versions/,
  or with the support policy the project states (scientific Python
  projects often follow SPEC 0, https://scientific-python.org/specs/spec-0000/).
  Report an end-of-life version still supported or tested, the newest
  stable release missing from CI, and classifiers or a matrix that
  disagree with `requires-python`.
- **The PEPs a newer floor brings.** With `--target-version` at the new
  floor, ruff's `UP` rules apply the syntax PEPs — built-in generics
  (PEP 585, 3.9), `X | Y` unions (PEP 604, 3.10), type parameters and
  `type` aliases (PEP 695, 3.12; `UP040`, `UP046`, `UP047`) — and remove
  branches for versions no longer supported (`UP036`). For the rest, read
  the "What's New" of each version the floor now guarantees
  (https://docs.python.org/3/whatsnew/) and the PEP index
  (https://peps.python.org/).
- **Packaging standards** (the PyPA specifications,
  https://packaging.python.org/en/latest/specifications/): metadata in
  the `[project]` table (PEP 621) with a declared `[build-system]`
  (PEP 517, PEP 518) rather than `setup.py` arguments; `python -m build`
  and `pip install .` rather than `python setup.py …` commands; an SPDX
  `license` expression with `license-files` (PEP 639) rather than a
  license table or license classifiers; development, test, and
  documentation dependencies in `[dependency-groups]` (PEP 735) rather
  than extras or loose requirements files; inline script metadata
  (PEP 723) for standalone scripts; `importlib.metadata`,
  `importlib.resources`, and `sysconfig` rather than `pkg_resources` and
  `distutils` (removed in 3.12); releases uploaded through PyPI Trusted
  Publishing rather than with a stored API token.
- **Environments, locks, and tools: pixi.** These guides recommend pixi
  (https://pixi.sh) for how a project is installed, locked, and run: one
  manifest (`pixi.toml`, or `[tool.pixi]` in `pyproject.toml`) and one
  `pixi.lock` for conda-forge and PyPI packages on every platform the
  project supports, `pixi run` tasks for the commands contributors and CI
  share, and `pixi global install` for command-line tools. It replaces
  uv, conda or mamba `environment.yml` files, pip-tools, hand-pinned
  `requirements*.txt` files, and `pipx`. Recommend the move with the
  files it would replace and the CI steps it would change (`NV`).

**Tests**

- fixtures copied between `conftest.py` files or test modules (`DUP`):
  one fixture in the nearest shared `conftest.py`;
- test functions that differ only in their data (`DUP`):
  `pytest.mark.parametrize`, noting that test IDs change;
- `mock.patch("pkg.mod.name")` targets naming a symbol the review moves:
  the patch target moves with it.

## Not findings

What looks dead or wrong in Python but is not. List the ones you checked
under "Not changed (deliberately)".

- Names reached by string or by convention: `getattr`, `importlib`,
  `__import__`, string-keyed registries, `[project.scripts]` and
  `[project.entry-points]` (or setuptools `entry_points`), pluggy and
  pytest hooks (`pytest_*`), module-level `__getattr__`, Sphinx `conf.py`
  settings.
- pytest fixtures (used by parameter name, or `autouse`), `conftest.py`
  contents, and the `test_*` names discovery collects.
- Functions registered by decorator: web routes (Flask, FastAPI),
  commands (click, typer), Django views, models, admin classes and signal
  handlers, Celery tasks, `atexit` handlers.
- Dunder methods, `__all__` entries, `__version__`, re-exports in
  `__init__.py`, `if TYPE_CHECKING:` imports, `@overload` signatures,
  `Protocol` members, abstract methods, and `*.pyi` stubs.
- Names a test patches by string, and attributes only serializers read
  (dataclass and pydantic fields, `__slots__`).
- Classes and module paths stored in pickles, joblib, or shelve files:
  renaming or moving one breaks loading saved data (`NV`).
- Database migrations: removing or squashing one changes the migration
  history of every deployed database (`NV`).
- Public API that the documentation or `__all__` promises to downstream
  users: having no caller inside the repository does not make it dead;
  removing it is `NV`.

## Verification

- **Baseline and after each group** (consent): the project's own entry
  point — the CI step, `tox`, `nox`, `hatch test`, `pixi run …`, a
  Makefile target — else `python -m pytest -q`; record passed, failed and
  skipped counts. Add the type checker and `ruff check` / `ruff format
  --check` when the project configures them.
- **Static, after any edit**: `ruff check --isolated --no-cache --select
  E9,F63,F7,F82 <paths>` reports syntax errors and undefined names.
- **Public surface** (consent): `python -c "import pkg; print(sorted(pkg.__all__))"`
  before and after, or `griffe check pkg --against <ref>` to list breaking
  API changes (it loads the old version through a temporary git worktree).
- **Enum migrations**: capture what crosses each boundary — JSON or YAML
  output, database values, log lines, command-line help — on the same
  fixture before and after; the bytes must match.
