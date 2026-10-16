#!/bin/sh
# DataLad-oriented recorded-run template with an in-flight commit guard.
# The plain-Git fallback records changed outputs, not a complete execution log.
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
#
# The same zsh rule applies to the *command*, which is the half this comment
# used to leave out: two runs in one round built a command in a variable
# (`E="python3 code/x.py"; ... -- $E args`) and got exit 127 or "no such file
# or directory", because `$E` arrives as one word. Write the command out, or
# run it as `sh -c '…'`.
#
# Declare inputs that exist. `datalad run` refuses the whole run with "Input
# did not match existing file" when one declared path is missing — a subject
# with no derivatives, say — so filter the list before building it rather than
# declaring every subject unconditionally.
#
# `datalad run` does not create the directories of its outputs. After a
# `git rm` of a results directory, a rerun fails with FileNotFoundError from
# the command itself; `mkdir -p` in the script that writes them is the fix.
#
# Many inputs: build the argument list, do not interpolate a string.
#
#   set -- -m 'collect 33 subjects'
#   for s in $(cat code/batch-1.txt); do
#       set -- "$@" -i "sourcedata/ds/$s/ses-1/anat"
#   done
#   ./code/run-recorded.sh "$@" -o results/batch-1.tsv -- \
#       python3 code/collect.py --subjects code/batch-1.txt --output results/batch-1.tsv
#
# The subject list is a tracked file, so the record names it and a rerun reads
# the same list.
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

# must/006 wants the record to name the environment it ran in, and two runs out
# of three forgot to declare theirs: a `datalad run` with no changed output
# writes no commit, so adding `-i code/requirements.lock` afterwards records
# nothing. So the wrapper declares the tracked environment specification as an
# input of every run, which is both true and the evidence the item asks for.
# `-n NAME` already names a container, and `--no-env-input` opts out.
ENV_INPUT=""
if [ "$SUBCMD" = run ]; then
    case " $* " in
        *" --no-env-input "*) : ;;
        *)
            for spec in requirements.lock code/requirements.lock requirements.txt                         code/requirements.txt pixi.lock pixi.toml pyproject.toml environment.yml code/containers.json; do
                if git ls-files --error-unmatch "$spec" >/dev/null 2>&1; then
                    ENV_INPUT="$spec"
                    break
                fi
            done
            ;;
    esac
fi

GITDIR="$(git rev-parse --git-dir)"
MARKER="$GITDIR/datalad-run-in-flight"
cleanup() { rm -f "$MARKER"; }

# This template uses committed Git state as its replay identity.
# Other workflows can capture a complete dirty state; this wrapper does not.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    printf 'refusing to run: the tree is dirty. Commit first.\n' >&2
    git status --short >&2
    exit 1
fi

# The marker carries the pid, so a marker left behind by a killed run can be
# told from a live one. A run that dies with SIGKILL skips the trap below, and
# an undetectable stale marker then refuses every later commit.
echo "$$" > "$MARKER"
trap cleanup EXIT INT TERM HUP
export IN_FLIGHT_OK=1

# `--no-env-input` is this wrapper's own flag; datalad has never heard of it.
# Dropped by rotating the positional parameters, not by rebuilding a string:
# `set -- $(...)` would re-split a multi-word `-m`, which is the first bug this
# template ever had.
case " $* " in
    *" --no-env-input "*)
        n=$#
        i=0
        while [ "$i" -lt "$n" ]; do
            arg="$1"
            shift
            [ "$arg" = "--no-env-input" ] || set -- "$@" "$arg"
            i=$((i + 1))
        done
        ;;
esac

if command -v datalad >/dev/null 2>&1; then
    # `set +e` around the call, and `$?` captured on the next line: after a
    # failed `if cmd; then` the shell reports the *if statement's* status, which
    # is 0, so the obvious spelling swallowed the failure.
    set +e
    if [ -n "$ENV_INPUT" ]; then
        printf 'note: declaring %s as an input, so the record names the environment (must/006).\n' \
            "$ENV_INPUT" >&2
        datalad "$SUBCMD" -i "$ENV_INPUT" "$@"
    else
        datalad "$SUBCMD" "$@"
    fi
    status=$?
    set -e
    if [ "$status" -eq 0 ]; then
        exit 0
    fi
    # A failed `datalad run` can leave the tree partly staged (a type change on
    # an output it had unlocked, for instance), and the next attempt then
    # refuses for a reason that looks unrelated. Say so here rather than
    # letting the next command be the messenger.
    printf '\ndatalad %s failed (exit %s). The tree may be partly staged:\n' "$SUBCMD" "$status" >&2
    git status --short >&2
    printf 'Reset what the run touched before retrying, e.g. `git reset HEAD <paths>` then\n' >&2
    printf '`git checkout -- <paths>`.\n' >&2
    exit $status
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
# A command whose outputs do not change leaves nothing to commit, and
# `git commit` then exits 1 — the wrapper reporting failure for a run that
# succeeded. The datalad path has the same property (an identical output writes
# no record) and says so without failing; this is the fallback's version of it.
# Found by CI, which is a machine with no datalad, so this path is the only one
# it ever runs.
if git diff --cached --quiet; then
    printf 'the command changed nothing tracked; no commit made.\n' >&2
    exit 0
fi
git commit -m "run: $*" -m "Recorded without datalad; declared:$record"
