# Selected subdataset metadata preparation

Prepared only `selected` with `datalad get -n selected`, then initialized its annex metadata with `git annex init metadata-inspection`, using the specified Pixi environment. No annex payload was retrieved.

- Selected HEAD: `77dedfe19f21ec17fc704fc5aa30e782345a98d8`, matching the parent repository's selected gitlink before and after preparation.
- Tracked input link: `code/containers/analysis.sif` remains a mode-120000 symlink at the same committed blob (`62bd5c1f034ff7236fed5242a3d5f45a577d1b18`); the selected worktree status is clean.
- Annex location metadata: `git annex whereis --json code/containers/analysis.sif` reports key `SHA256E-s2304--7a3838d9d993f455975a9a9eac0cf5107aa92f0750b3d1aaacfb193fbd210ce1.sif`, with two known copies: UUID `2b4a96f1-fa74-4fde-b902-3df0bc4933ac` and UUID `5cc56a23-e45a-4f43-a8d6-96b1d237b818` (`test [origin]`). `here` is false for both, confirming metadata inspection without local payload retrieval.
- The parent repository's status is clean after preparation.

Friction: none. The skill's instructions to use `datalad get -n PATH` for metadata-only installation and initialize a plain-cloned annex before queries were clear and compatible with this task.

Executed commands and captured results are in `commands.json`.
