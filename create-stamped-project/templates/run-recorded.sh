#!/bin/sh
# Start a recorded run, with the in-flight marker the pre-commit guard reads.
#
#   ./code/run-recorded.sh -m 'collect volumes' -o results/volumes.tsv -- \
#       python3 code/collect_volumes.py --input sourcedata/ds007116 --output results/volumes.tsv
#
# Everything before `--` goes to `datalad run`; everything after is the command.
# Falls back to a plain recorded commit when datalad is absent, so the project
# still records *something* rather than nothing.
#
# Three things here are the way they are because the obvious version is broken,
# each found by an agent using this template for real:
#
#   * `"$@"`, never `$@`: unquoted, a multi-word `-m 'collect per-session …'`
#     re-splits and `datalad run` tries to execute `per-session`.
#   * no `exec`: `exec` replaces this process, so `trap cleanup EXIT` never
#     fires, the marker is left behind after every run, and the pre-commit
#     guard then refuses every later commit — the guard inflicting the exact
#     hazard it exists to prevent.
#   * the marker lives in the git directory, not the worktree: `datalad run`
#     refuses to start when there are untracked files, so a marker beside the
#     code makes the documented usage fail out of the box.
set -eu

GITDIR="$(git rev-parse --git-dir)"
MARKER="$GITDIR/datalad-run-in-flight"
cleanup() { rm -f "$MARKER"; }

# Commit before execute: a run that starts from a dirty tree cannot be rerun.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    printf 'refusing to run: the tree is dirty. Commit first.\n' >&2
    git status --short >&2
    exit 1
fi

: > "$MARKER"
trap cleanup EXIT INT TERM HUP
export IN_FLIGHT_OK=1

if command -v datalad >/dev/null 2>&1; then
    datalad run "$@"
    exit $?
fi

printf 'warning: datalad not found; recording the command in a plain commit.\n' >&2
record=""
while [ $# -gt 0 ]; do
    case "$1" in
        --) shift; break ;;
        -m|-o|-i) record="$record $1 $2"; shift 2 ;;
        *) record="$record $1"; shift ;;
    esac
done
"$@"
git add -A
git commit -m "run: $*" -m "Recorded without datalad; declared:$record"
