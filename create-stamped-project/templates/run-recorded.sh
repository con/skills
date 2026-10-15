#!/bin/sh
# Start a recorded run, with the in-flight marker the pre-commit guard reads.
#
#   ./code/run-recorded.sh -m 'collect volumes' -o results/volumes.tsv -- \
#       python3 code/collect_volumes.py --input sourcedata/ds007116 --output results/volumes.tsv
#
#   ./code/run-recorded.sh -n synthstrip -m 'strip sub-20919' \
#       -i sourcedata/ds007116/sub-20919/ses-1/anat/sub-20919_ses-1_T1w.nii.gz \
#       -o derivatives/masks/sub-20919_mask.nii.gz -- \
#       mri_synthstrip -i {inputs} -m {outputs}
#
# Everything before `--` goes to `datalad run`; everything after is the command.
# `-n NAME` (a registered container) switches it to `datalad containers-run`,
# which is the only way a run record names the image it ran in (must/006,
# must/015). Passing `datalad containers-run …` as the command instead nests
# one record inside another and declares no inputs or outputs — found by an
# agent doing exactly that on R1.
#
# Quote path lists. `-i "$FILES"` passes one argument under zsh, which does not
# word-split unquoted variables, and `datalad run` then looks for a single file
# with ten names in it. One run per subject, or `-i` repeated, or `xargs`.
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

# `-n NAME` is a containers-run flag; `datalad run` has no such option, so its
# presence is the dispatch. A leading `datalad` or `run`/`containers-run` word
# is tolerated and dropped: that is how this gets called by mistake.
SUBCMD=run
case "${1:-}" in
    datalad) shift ;;
esac
case "${1:-}" in
    run) shift ;;
    containers-run) SUBCMD=containers-run; shift ;;
esac
for arg in "$@"; do
    case "$arg" in
        -n|--container-name) SUBCMD=containers-run ;;
        --) break ;;
    esac
done

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
    datalad "$SUBCMD" "$@"
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
