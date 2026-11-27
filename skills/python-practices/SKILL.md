---
name: python-practices
description: Python practices for scientific Python packages — where a Python project states its rules, its review tools and which need execution consent, Python checks such as a long or growing Literal list that becomes one Enum, NumPy idioms, currency (Python versions, NumPy 2, PEPs, PyPA standards, pixi), false positives, and verification commands. Use when writing, changing, or reviewing Python code, including in a pull-request review or a code-quality review (review-repo-code-quality and review-org-code-quality read it).
allowed-tools: Read
user-invocable: false
---

# Python practices

What holds for Python code only, for three kinds of work: writing or
changing it, reviewing a pull request, and the code-quality reviews
(`review-repo-code-quality` reads this guide in Step 1;
`review-org-code-quality` runs its **static** tools). When writing code,
follow Project rules and Checks and leave Not findings alone; when
reviewing, report against them. The procedure, the architecture
principles, the category prefixes (`ARC`, `DC`, `DUP`, `CON`, `CL`, `NV`),
and the **static** / **consent** marks on the Tools are defined in
`review-repo-code-quality`.

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

Besides the files `review-repo-code-quality` Step 1 names, read
`pyproject.toml` — `[project]` (`requires-python`, dependencies and
optional dependencies, `scripts`, `entry-points`) and the `[tool.*]`
tables for ruff, mypy, pytest, coverage and vulture — and whichever of
these exist: `setup.cfg`, `setup.py`, `ruff.toml` / `.ruff.toml`,
`mypy.ini`, `.flake8`, `tox.ini`, `noxfile.py`,
`.pre-commit-config.yaml`, `requirements*.txt`, the environment files
(`pixi.toml` or `[tool.pixi]` in `pyproject.toml`, `environment.yml`,
`.python-version`), and the lock file (`pixi.lock` or `uv.lock`).
`setup.py`, `noxfile.py` and `conftest.py` are code: read them as text.

The oldest Python the project supports — `requires-python`, else the
oldest version CI tests — bounds what may be proposed: no `X | Y` union
evaluated at run time before 3.10, no `match` before 3.10, no
`enum.StrEnum` or `typing.Self` before 3.11. Pass it to ruff as
`--target-version` so its `UP` rules hold to the same bound.

## Tools

`vulture` reads `[tool.vulture]` from the `pyproject.toml` in its working
directory, hence the scratch directory (`review-repo-code-quality`
Step 1). Given a directory, ruff (even with `--isolated`) and `lizard`
skip ignored files: add `--config 'respect-gitignore = false'` to ruff (it
works for `ruff check` and `ruff analyze graph`, which rejects
`--no-respect-gitignore`) and `--no-gitignore` to lizard, or pass the
tracked `*.py` files as Step 1 shows. List scripts without an extension
in `<paths>` explicitly; neither vulture nor ruff collects them from a
directory.

| Sweep | Tool | Mark | Command |
|---|---|---|---|
| Dead code | `vulture` | static | `vulture <paths> --min-confidence 90` for unused imports (90%), unreachable code and unused parameters (100%); then without `--min-confidence` for the 60% tail (functions, classes, methods, attributes, variables) |
| Idiom drift | `ruff`, your configuration | static | `ruff check --isolated --no-cache --target-version py3XX --select E,F,W,B,UP,RET,SIM,C4,PIE,PERF,PLR,PLC0415,BLE001,S110,RUF012,PLW0603,T201,PGH003,NPY --output-format concise <paths>` |
| Idiom drift | `ruff`, the project's configuration | consent | `ruff check --no-cache --extend-select B,UP,RET,SIM,C4,PIE,PERF,PLR,PLC0415,BLE001,S110,RUF012,PLW0603,T201,PGH003,NPY --output-format concise` from the checkout |
| Types | the project's type checker | consent | the project's own invocation |
| Dependencies | `deptry` | consent: maps distributions to modules through the installed project | `deptry .` from the checkout |
| Import graph | `ruff analyze graph` (experimental) | static | `ruff analyze graph --isolated <paths>`; `--direction dependents` for the reverse map |
| Complexity | `ruff` | static | `ruff check --isolated --no-cache --select C901,PLR0911,PLR0912,PLR0913,PLR0915 --output-format concise <paths>` (each hit gives its count at the function's `def` line; only `C901` names the function), or `lizard -l python <paths>` |
| Tests | the project's runner | consent | see Verification |

With `--isolated`, ruff ignores the whole project configuration: disabled
rules, `per-file-ignores`, excludes, `line-length`, thresholds such as
`lint.pylint.max-args`, and rule options. Read them from the project's
configuration and drop or re-judge the affected hits, or pass the values
back with `--config 'KEY = VALUE'` (full keys), which reads nothing from
the repository. Ruff resolves `exclude`, `extend-exclude`, and
`per-file-ignores` patterns against the working directory, here the
scratch directory: prefix each relative pattern with the checkout's
absolute path, and add `--force-exclude` when `<paths>` lists files, or
the excludes do not apply at all.

## Checks

**Closed sets and constants**

- **A long or growing `Literal` list becomes one `Enum`** (`ARC`; `CON`
  when it stays inside one module). A `Literal[...]` of more than a
  handful of values, or one that has gained values over time, will need
  updating again. When it is repeated across signatures, mirrored by a
  run-time tuple or set (validation, `argparse` `choices`, `click.Choice`),
  or compared against bare strings elsewhere, recommend one `Enum` —
  `enum.StrEnum` from Python 3.11, `class Mode(str, Enum)` before — used
  in every annotation, choice list, and comparison. Keep short, stable
  sets as `Literal` (`Literal["r", "w"]`).
  Before rating the switch **High**, trace every place a value crosses a
  boundary: pydantic models (`model_dump()` returns members unless
  `use_enum_values` or JSON mode is set), JSON and YAML writers,
  attributes written to HDF5, Zarr or NWB files, pickles, and formatting.
  `str()` of a `(str, Enum)` member gives `"Mode.FAST"` on every version,
  while f-strings and `format()` give `"fast"` up to Python 3.10 and
  `"Mode.FAST"` from 3.11, so one line prints different text across a
  range that spans both; `StrEnum`, or `__str__ = str.__str__` on the
  class, gives the value everywhere. Type checkers also reject callers
  that pass plain strings, so for a public function the switch is an API
  change (`NV`).
  The safe first step, which changes no annotation, value, or output
  (`CON`), is one named alias that the run-time copies derive from:
  `Mode = Literal["fast", "slow", …]` and `MODES = typing.get_args(Mode)`
  for `choices=` and validation (`get_args(Mode.__value__)` for a PEP 695
  `type` alias). Propose the `Enum` alongside it as the follow-up.
- **The same magic value in several modules** (`ARC`; `CON` when it stays
  inside one module): one named constant, or a member of the `Enum`
  above. `PLR2004` finds numeric comparisons only; for strings add
  `--config 'lint.pylint.allow-magic-value-types = []'` (its default
  skips `str` and `bytes`), or search for the literal.
- **Dicts with a fixed set of keys passed between functions** (`ARC`):
  a `dataclass`, `TypedDict`, or `NamedTuple` makes the shape one
  definition. Code that serializes, mutates, or `**`-unpacks the dict
  makes the switch `NV`.

**Imports and modules**

- **Import cycles** (`ARC`): look for them in the map `ruff analyze graph`
  prints (it lists imports, not cycles), and in imports moved into
  functions or under `if TYPE_CHECKING:` to dodge one.
  Name the cycle and the move that breaks it. `TYPE_CHECKING` imports used
  only in annotations are fine.
- **Function-local imports** (`CL`; `PLC0415`) with no cycle to break and
  no slow or optional dependency to defer move to the top of the module.
  Keep the ones that break a cycle or defer a slow or optional dependency
  (a plotting or machine-learning library that only one function needs),
  and say which.
- **Private imports** (`ARC`): `from pkg._impl import X` where `pkg`
  exports `X` publicly, and private names imported across package
  boundaries.
- **Effects at import time** (`ARC`): `logging.basicConfig`,
  `warnings.filterwarnings`, `matplotlib.use`, environment variables read
  into module constants, file or network access, `sys.path` edits, and
  registrations. Moving them into a function the entry point calls
  changes when they happen; trace every importer, tests included.
- **`__all__` drift**: a name listed but defined nowhere makes
  `from pkg import *` raise `AttributeError` today, so its fix is `NV`.
  First rule out submodules of the package (a star import loads them) and
  names that a module-level `__getattr__` serves;
  `ruff check --isolated --preview --select F822` lists candidates,
  submodule names included. For public names that the documentation
  presents but `__all__` leaves out, correcting the documentation is `CL`;
  adding them to `__all__` changes what a star import binds (`NV`).
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
  `UP035`, `UP045`) where the oldest supported Python has the new ones.
  Where a library reads the annotations at run time (see Types), the
  oldest supported Python must evaluate the new spelling, and code that
  checks `typing.get_origin(…) is Union` breaks, since
  `get_origin(int | None)` is `types.UnionType` before Python 3.14. The
  PEP 695 rewrites (`UP040`, `UP046`, `UP047`) are not spellings: see
  Currency;
- `any(...)` written to mean "not empty": `if xs:` is the same only when
  `xs` is a sized built-in collection (list, tuple, set, dict, str) and no
  element can be falsy. An iterator or generator (`path.iterdir()`,
  `os.scandir()`, `map()`) is always truthy, and a NumPy array or pandas
  object raises `ValueError`, so keep `any()` there;
- `open()` outside a `with` block (`SIM115`) — `CL` when every path
  already closes the file, else `NV`.

**NumPy** (`NPY`)

- names NumPy removed (`NPY001`, `NPY003`, `NPY201`: `np.float` in 1.24,
  `np.NaN` and `np.product` in 2.0, `np.trapz` by 2.5) raise
  `AttributeError` once that release is installed: a bug under Needs
  Verification unless the project caps NumPy below it. A replacement that
  exists only from NumPy 2.0 (`np.trapezoid`) is `NV` while NumPy 1 is
  supported;
- the legacy global random state (`np.random.seed`; `NPY002`) becomes one
  `np.random.default_rng(seed)` passed down; every draw changes (`NV`).

**Errors and state** (usually `NV`: the fix changes behavior)

- broad or bare `except` that swallows errors (`BLE001`, `E722`, `S110`);
- mutable default arguments and class attributes (`B006`, `RUF012`);
- module state changed through `global` (`PLW0603`);
- `print` in library code where the project logs (`T201`).

**Types** (`CL` when only type checkers read the annotations; `NV` when a
library reads them at run time — pydantic models, settings, and
`validate_call`, typer commands, `functools.singledispatch`
registration, or any other `typing.get_type_hints` caller — since
narrowing `Any` there changes coercion, validation, or dispatch): `Any`
where the concrete type is known; `# type: ignore` without an error code
(`PGH003`; a comment, so always `CL`); annotations that disagree with
what the function returns (the type checker confirms the disagreement,
not that the fix is safe).

**Packaging and dependencies**

- metadata declared in both `setup.py` / `setup.cfg` and `pyproject.toml`
  (`CON`), and one version string kept in several files (`ARC`);
- dependencies declared for run time but never imported by shipped code
  (`deptry` `DEP002`; it skips `tests/` by default, so this also catches
  dependencies only tests use), imported but not declared (`DEP001`), or
  only reachable through another package (`DEP003`), and development
  dependencies that shipped code imports (`DEP004`) — `DC`, or `NV` when
  the fix changes what installs;
- the same pins repeated across `requirements*.txt`, `tox.ini`, CI, and
  `pyproject.toml` (`ARC`);
- a `requires-python` lower bound that CI never tests (`NV`: the claim or
  the test matrix has to change).

**Currency** (reported as `review-repo-code-quality` Step 2 says; read the
live sources each item names rather than trusting its examples)

- **Python versions.** Compare `requires-python`, the
  `Programming Language :: Python :: 3.x` classifiers, the CI matrix, and
  the other places a version is named (`.python-version`, tox `envlist`
  and nox sessions, the pixi or conda `python` pin, and tool targets such
  as `[tool.ruff] target-version` and `[tool.mypy] python_version`) with
  the status of each version at
  https://devguide.python.org/versions/, or with the support policy the
  project states (scientific Python projects often follow SPEC 0,
  https://scientific-python.org/specs/spec-0000/, which also drops core
  dependencies two years after their release: compare their lower bounds
  too). Report an end-of-life version still supported or tested, the
  newest stable release missing from CI, and places that disagree with
  `requires-python`.
- **The PEPs a newer floor brings.** Model the floor the Python versions
  item would move to, run the static ruff command with `--target-version`
  at that floor, and list its `UP` hits inside that floor-raise `NV` item,
  as what the move unlocks: built-in generics (PEP 585, 3.9), `X | Y`
  unions (PEP 604, 3.10), type parameters and `type` aliases (PEP 695,
  3.12; `UP040`, `UP046`, `UP047`), and branches for versions no longer
  supported (`UP036`). None is a finding of its own while the current
  floor is lower: a `type` statement is a `SyntaxError` before 3.12.
  Where the current floor already allows them, the PEP 695 rewrites are
  still `NV` unless nothing reads the alias or type variable at run time:
  `UP040` turns an alias into a `TypeAliasType`, so `typing.get_args()`
  returns `()` and `isinstance()` rejects it, and ruff marks all three
  fixes unsafe. For the rest, read the "What's New" of each version the
  floor now guarantees (https://docs.python.org/3/whatsnew/) and the PEP
  index (https://peps.python.org/).
- **Packaging standards** (the PyPA specifications,
  https://packaging.python.org/en/latest/specifications/): metadata in
  the `[project]` table (PEP 621) with a declared `[build-system]`
  (PEP 517, PEP 518) rather than `setup.py` arguments; `python -m build`
  and `pip install .` rather than `python setup.py …` commands; an SPDX
  `license` expression with `license-files` (PEP 639) rather than a
  license table or license classifiers; development, test, and
  documentation dependencies in `[dependency-groups]` (PEP 735) rather
  than extras or loose requirements files; inline script metadata
  (PEP 723) for standalone scripts; `sysconfig` or setuptools rather than
  `distutils` (removed from the standard library in 3.12, PEP 632);
  releases uploaded through PyPI Trusted Publishing
  (https://docs.pypi.org/trusted-publishers/) rather than with a stored
  API token. These migrations change what the built distributions
  declare, so each is `NV` unless the project's rules already require it:
  extras moved into `[dependency-groups]` leave the published metadata
  (`pip install pkg[test]` stops installing them), an SPDX `license`
  string needs a build backend that implements PEP 639 (setuptools 77 or
  later), and moving `setup.py` arguments into `[project]` can change
  package discovery, data files, and entry points.
- **`pkg_resources`.** Setuptools removed it in 82.0.0
  (https://setuptools.pypa.io/en/latest/history.html), so a run-time
  import fails wherever setuptools 82 or later, or none, is installed:
  report it under Needs Verification as a bug, not as a preference, unless
  the project pins `setuptools<82`; `importlib.metadata` and
  `importlib.resources` replace it.
- **Environments, locks, and tools: pixi** (house preference; see
  `review-repo-code-quality` Configuration and Step 2). Pixi
  (https://pixi.sh) gives one manifest (`pixi.toml`, or `[tool.pixi]` in
  `pyproject.toml`) and one `pixi.lock` for conda-forge and PyPI packages
  on every platform the project supports, `pixi run` tasks for the
  commands contributors and CI share, and `pixi global install` for
  command-line tools that conda-forge packages (it installs conda
  packages only). It replaces uv, conda or mamba `environment.yml` files,
  pip-tools, hand-pinned `requirements*.txt` files, and `pipx` for tools
  on conda-forge; name the files it would replace and the CI steps it
  would change.

**Tests**

- fixtures copied between `conftest.py` files or test modules (`DUP`):
  one fixture in the nearest shared `conftest.py`;
- test functions that differ only in their data (`DUP`):
  `pytest.mark.parametrize`, noting that test IDs change;
- patch targets around a symbol the review moves (`mock.patch("pkg.mod.name")`,
  `mocker.patch`, `monkeypatch.setattr("pkg.mod.name", …)`): a patch
  replaces the name only in the module it names, so it must name the
  module where the code under test looks the name up when it runs, not
  where the symbol is defined. The target stays when that code stays and
  imports the name with `from … import`, or keeps calling
  `old.mod.name()` through a re-export. It moves when that code moves
  with the symbol (a re-export left in the old module does not carry the
  patch) or is rewritten to call `new.mod.name()`. A target that resolves
  on the wrong module raises nothing and the real function runs, so after
  the move run those tests and check that each mock was called.

## Not findings

- Names reached by string or by convention: `getattr`, `importlib`,
  `__import__`, string-keyed registries, `[project.scripts]` and
  `[project.entry-points]` (or setuptools `entry_points`), pytest hooks
  (`pytest_*`), module-level `__getattr__`, Sphinx `conf.py` settings.
- pytest fixtures (used by parameter name, or `autouse`), `conftest.py`
  contents, and the `test_*` names discovery collects.
- Functions registered by decorator: click and typer commands, `atexit`
  handlers, and the project's own registries.
- Imports kept for their side effects: `import readline`, or a module
  imported so that it registers handlers, plugins, codecs, or file-format
  extensions. vulture reports them, and ruff's `F401` fix would delete
  them; marking them `# noqa: F401` with the reason is a `CL` both tools
  honor.
- Methods that a library calls by name on a subclass
  (`json.JSONEncoder.default`, `logging.Handler.emit`,
  `unittest.TestCase.setUp`), and parameters a signature must keep
  because its caller passes them: a signal handler's `frame`,
  `sys.excepthook`'s `tb`, callbacks, overrides. vulture reports such a
  parameter at 100% confidence when its name is unused anywhere in the
  scan. Renaming it to `_name` silences vulture but is safe only when
  every caller passes it by position (`signal.signal`, `sys.excepthook`).
- Dunder methods, `__all__` entries, `__version__`, re-exports in
  `__init__.py`, `if TYPE_CHECKING:` imports, `@overload` signatures,
  `Protocol` members, and abstract methods.
- Names a test patches by string, and attributes only serializers read
  (dataclass and pydantic fields, `__slots__`).
- Classes and module paths stored in pickles, joblib, or shelve files:
  renaming or moving one breaks loading saved data (`NV`).
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
- **Public surface** (consent):
  `python -c "import pkg; print(sorted(getattr(pkg, '__all__', None) or [n for n in dir(pkg) if not n.startswith('_')]))"`
  before and after, or `griffe check pkg --against <ref> --no-inspection`
  (add `--search src` for a src layout) to list breaking API changes;
  griffe loads the old version through a temporary git worktree, and
  `--no-inspection` stops it from importing a package it cannot find.
- **Packaging changes** (consent, throwaway checkout): `python -m build
  --outdir <scratch>/dist-before` before the change and
  `--outdir <scratch>/dist-after` after it; diff each archive's file list,
  `METADATA`, and `entry_points.txt`.
- **Enum migrations**: capture what crosses each boundary — JSON or YAML
  output, data-file attributes, log lines, command-line help — on the same
  fixture before and after, under both the oldest and the newest
  supported Python; the bytes must match.
- **Array code** (consent): vectorizing a loop or reordering a reduction
  can change floating-point results; compare outputs before and after
  exactly, and report a difference rather than widen a test tolerance.
