#!/bin/sh
# Checks for a workflow that uses committed Git state as its run identity.
# Adapt these guards to the project; they are not the complete STAMPED rubric.
#
#   ./code/preflight.sh            # before a batch of compute
#   ./code/preflight.sh --quiet    # in CI
#
# Each check maps to a checklist item, named in its message, so a failure says
# which property is at risk rather than only that something is wrong.
set -eu
quiet=0
[ "${1:-}" = "--quiet" ] && quiet=1

# Installed tooling is not the project. An agent harness directory, a vendored
# dependency or a compiled cache carries paths and commands that are none of
# this project's business, and flagging them produces a FAIL nobody can fix.
# Extend with PREFLIGHT_EXCLUDE=':(exclude)vendor/*' etc.
EXCLUDE=":(exclude).claude/* :(exclude)**/__pycache__/* :(exclude)**/*.pyc ${PREFLIGHT_EXCLUDE:-}"
fail=0
say() { [ "$quiet" = 1 ] || printf '%s\n' "$1"; }
bad() { printf 'FAIL  %s\n' "$1" >&2; fail=1; }

# This template requires a clean commit; other workflows can identify a complete
# dirty delivery by a retained content snapshot. Cleanliness alone is not must/004.
if [ -n "$(git status --porcelain)" ]; then
    bad "this commit-based workflow requires a clean tree before executing"
else
    say "ok    tree is clean"
fi

# must/002, should/003 — inputs are modules at their recorded commit.
if [ -f .gitmodules ]; then
    if git submodule status --recursive | grep -q '^+'; then
        bad "an input module differs from the recorded commit (should/003)"
    elif git submodule status --recursive | grep -q '^-'; then
        say "note  an input module is not installed; get it before executing"
    else
        say "ok    input modules are at their recorded commits"
    fi
    if git config -f .gitmodules --get-regexp 'submodule\..*\.url' | grep -qE ' (\.\.?/|/|file://)'; then
        bad "a module url resolves only on this machine (must/002, must/016)"
    fi
fi

# must/010, must/013 — the environment is pinned and tracked.
if git ls-files | grep -qE '(^|/)(requirements.*\.txt|requirements\.lock|pyproject\.toml|environment\.ya?ml|pixi\.(toml|lock)|uv\.lock|renv\.lock|Dockerfile|Singularity.*|.*\.def)$'; then
    say "ok    an environment specification is tracked"
else
    bad "no tracked environment specification (must/010, must/013)"
fi

# P.1 — nothing the next host will not have.
# shellcheck disable=SC2086  # EXCLUDE is a list of pathspecs on purpose
hits=$(git ls-files -z -- . $EXCLUDE | xargs -0 grep -lE '(^|[^[:alnum:]:])/(home|Users|data|scratch|mnt)/[A-Za-z]' 2>/dev/null || true)
if [ -n "$hits" ]; then
    bad "a tracked file carries a host-specific absolute path (must/009):"
    printf '%s\n' "$hits" | sed 's/^/        /' >&2
else
    say "ok    no host-specific absolute paths in the project's own tracked files"
fi

[ "$fail" = 0 ] && say "preflight passed" || printf '\npreflight failed: fix the above, or say in the run record why it is acceptable.\n' >&2
exit "$fail"
