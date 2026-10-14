#!/bin/sh
# Refuse to start work from a state whose results could not be reproduced.
#
#   ./code/preflight.sh            # before a batch of compute
#   ./code/preflight.sh --quiet    # in CI
#
# Each check maps to a checklist item, named in its message, so a failure says
# which property is at risk rather than only that something is wrong.
set -eu
quiet=0
[ "${1:-}" = "--quiet" ] && quiet=1
fail=0
say() { [ "$quiet" = 1 ] || printf '%s\n' "$1"; }
bad() { printf 'FAIL  %s\n' "$1" >&2; fail=1; }

# must/004 — the committed state is the whole state.
if [ -n "$(git status --porcelain)" ]; then
    bad "the tree is dirty (must/004): commit or stash before executing"
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
if git ls-files -z | xargs -0 grep -lE '(^|[^[:alnum:]:])/(home|Users|data|scratch|mnt)/[A-Za-z]' 2>/dev/null | grep -qv '^$'; then
    bad "a tracked file carries a host-specific absolute path (must/009)"
else
    say "ok    no host-specific absolute paths in tracked files"
fi

[ "$fail" = 0 ] && say "preflight passed" || printf '\npreflight failed: fix the above, or say in the run record why it is acceptable.\n' >&2
exit "$fail"
