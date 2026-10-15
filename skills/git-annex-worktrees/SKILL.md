---
name: git-annex-worktrees
description: Troubleshoot git-annex or DataLad failures in Git linked worktrees and their subdatasets. Use when either tool reports a missing repository, nonexistent working tree, or wrong path even though ordinary Git works; apply a command-local GIT_DIR and GIT_WORK_TREE workaround.
allowed-tools: Bash, Read
user-invocable: true
---

# Fix git-annex and DataLad Worktree Path Errors

When git-annex fails directly or through DataLad in a linked worktree, it may be resolving a relative `core.worktree` from the wrong directory.
The trick is to give the failing Annex command absolute `GIT_DIR` and `GIT_WORK_TREE` paths derived by Git.

Set `repo` to the affected worktree or subdataset, then check whether Git finds it while Annex reports the wrong path:

```bash
git -C "$repo" rev-parse --show-toplevel
git -C "$repo" annex info
```

If so, retry the failing Annex operation with this override, using the project's existing tool environment:

```bash
(
  git_dir=$(git -C "$repo" rev-parse --absolute-git-dir) &&
    work_tree=$(git -C "$repo" rev-parse --show-toplevel) &&
    [ -n "$git_dir" ] && [ -n "$work_tree" ] || {
      echo "git rev-parse failed; not applying the Annex override" >&2
      exit 1
    }

  cd "$work_tree" || exit 1
  GIT_DIR="$git_dir" GIT_WORK_TREE="$work_tree" \
    git annex <command> <arguments>
)
```

Pass file arguments relative to the worktree root (or use absolute paths).
The subshell leaves the caller's working directory unchanged.

For a DataLad failure, apply the override to the failing underlying Annex operation in the affected dataset.
Do not pass one dataset's Git paths to a recursive DataLad command that visits other datasets.
Keep the override local; do not export it for the surrounding shell or rewrite `core.worktree` or Git metadata.

Verify the result with the smallest appropriate check, such as `git annex find`, `git annex whereis`, or the original workflow, applying the same override if needed.
