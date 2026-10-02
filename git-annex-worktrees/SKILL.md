---
name: git-annex-worktrees
description: Run git-annex reliably in Git linked worktrees and worktree-hosted submodules when relative core.worktree resolution points Annex at the wrong path. Use when ordinary Git finds a repository but git-annex reports a nonexistent or incorrectly rooted working tree.
allowed-tools: Bash, Read
user-invocable: true
---

# Git Annex in Linked Worktrees

Use this workaround only when Git Annex misresolves a linked worktree, often through a submodule whose `.git` entry reaches a worktree-specific module directory.
Ordinary Git may work while Git Annex interprets a relative `core.worktree` from the wrong directory and reports a nonexistent path.

First confirm the mismatch:

```bash
git -C "$repo" rev-parse --show-toplevel
git -C "$repo" annex info
```

If Git reports the correct worktree but Annex does not, derive both paths with Git and scope them to the Annex invocation:

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

Keep the override local to each affected command.
Do not rewrite `core.worktree`, replace worktree or submodule Git metadata, or export these variables for the surrounding shell merely to make Annex work.
Those changes can break ordinary Git's already-correct repository discovery.

After the Annex operation, verify its externally relevant result with the smallest appropriate check, such as `git annex find`, `git annex whereis`, or the workflow that originally required the content.
