# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""The STAMPED probes: deterministic checks over committed state.

``REGISTRY`` maps a probe name to its callable.  The same code runs inside
``assess-alignment-with-stamped-principles`` and inside the eval graders, so a
mutant that the probe misses is a bug in one place only.
"""

from __future__ import annotations

from .common import Evidence, Object, Probe
from .modules import inputs_untouched, modules_separated, subdatasets_resolvable
from .provenance import derived_have_records, run_env_linked
from .structure import (
    ci_present,
    clone_weight,
    entry_point,
    env_spec_tracked,
    large_in_annex,
    license_declared,
    no_abs_paths,
    tree_clean,
)

REGISTRY = {
    "tree-clean": tree_clean,
    "no-abs-paths": no_abs_paths,
    "large-in-annex": large_in_annex,
    "subdatasets-resolvable": subdatasets_resolvable,
    "derived-have-records": derived_have_records,
    "run-env-linked": run_env_linked,
    "env-spec-tracked": env_spec_tracked,
    "entry-point": entry_point,
    "modules-separated": modules_separated,
    "inputs-untouched": inputs_untouched,
    "license-declared": license_declared,
    "clone-weight": clone_weight,
    "ci-present": ci_present,
}

# `fresh-rerun` lives in ../fresh_rerun.py: it needs another host, a network and
# minutes to hours, so it is never part of the default sweep.
EXPENSIVE = ("fresh-rerun",)

__all__ = ["REGISTRY", "EXPENSIVE", "Evidence", "Object", "Probe"]
