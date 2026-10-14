#!/bin/sh
# Start a recorded run, with the in-flight marker the pre-commit guard reads.
#
#   ./code/run-recorded.sh -m 'collect volumes' -o results/volumes.tsv -- \
#       python3 code/collect_volumes.py --input sourcedata/ds007116 --output results/volumes.tsv
#
# Everything before `--` goes to `datalad run`; everything after is the command.
# Falls back to `make`-style execution when datalad is absent, so the project
# still records *something* (a git commit naming the command) rather than
# nothing.
set -eu

MARKER=".datalad-run-in-flight"
cleanup() { rm -f "$MARKER"; }

# Commit before execute: a run that starts from a dirty tree cannot be rerun.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    printf 'refusing to run: the tree is dirty. Commit first.\n' >&2
    git status --short >&2
    exit 1
fi

: > "$MARKER"
trap cleanup EXIT INT TERM
export IN_FLIGHT_OK=1

if command -v datalad >/dev/null 2>&1; then
    # shellcheck disable=SC2068  # word splitting is the interface here
    exec datalad run $@
fi

printf 'warning: datalad not found; recording the command in a plain commit.\n' >&2
args_before_dashdash=""
while [ $# -gt 0 ]; do
    case "$1" in
        --) shift; break ;;
        -m|-o|-i) args_before_dashdash="$args_before_dashdash $1 $2"; shift 2 ;;
        *) args_before_dashdash="$args_before_dashdash $1"; shift ;;
    esac
done
"$@"
git add -A
git commit -m "run: $*" -m "Recorded without datalad; outputs:$args_before_dashdash"
