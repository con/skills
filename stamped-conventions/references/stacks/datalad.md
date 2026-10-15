# Stack: DataLad and git-annex

Load this only when the object uses DataLad or git-annex, or when the user's environment has them and a new project is being laid out.
It says what evidence to look for and what to never do; it is not a DataLad tutorial.

## Evidence this stack produces

| Property | Where the evidence is | Items |
|---|---|---|
| Large content is content-addressed | `.git/annex/`, `git annex info`, symlinks or unlocked pointers in the worktree; `git cat-file -s` on tracked blobs stays small | must/005 |
| Components are one version-control system | `.datalad/config`, `datalad status --recursive` | should/001 |
| Inputs are modules, not copies or paths | `.gitmodules` + `datalad subdatasets --recursive`, with retrievable URLs | must/002, must/003, may/001 |
| Every derived file has a re-executable record | `[DATALAD RUNCMD]` commit messages carrying the `run_info` JSON (`cmd`, `inputs`, `outputs`, `dsid`), reachable with `git log --grep`; `datalad rerun` works | must/006, A.2 |
| Runs name their environment | `datalad containers-run` records the container name, and `.datalad/config` carries its image path and `datalad-container` registration | must/006, must/015 |
| The environment is tracked | `.datalad/environments/`, a container definition, or a lockfile under version control | must/010, must/013 |
| Others can retrieve it | `datalad siblings` with a reachable URL, `git annex whereis` showing a non-local remote, `datalad clone` from the published location | must/016, D.1 |

## Reading a run record

```console
git log --format='%H%n%B' --grep='\[DATALAD RUNCMD\]' | …     # the JSON block follows the message body
datalad rerun --report <commit>                                # structured form, when datalad is available
```
A record whose `outputs` list is empty does not cover the files that commit touched — that is `partial` on must/006, not `met`.

## Never do

- **Never `git commit` (or let a hook commit) while a `datalad run` is in flight.**
  The run commits its own result; an outside commit in between has silently lost computed content before ([compression-comparisons](https://github.com/dandi/compression-comparisons)).
  The fix that project landed — a pre-commit hook that refuses while a run is in progress — is the artifact to install, not a sentence in a document.
  A `Stop`-hook autosave is the same hazard with a friendlier name.
- **Never `datalad save` a derived file by hand** to make a tree clean; re-run it through the recorded mechanism instead.
- **Never leave a subdataset URL that only resolves on one machine.**
  `url = ../..` inside `.gitmodules` resolves relative to wherever the superdataset happens to sit, so a fresh clone elsewhere fails: that is must/002 and must/016 `unmet`, and it is the single most common real-world failure in the projects this collection was calibrated on.
- **Never pin a container as `:latest`** — must/015 wants a digest or a frozen version.

## Traps, each hit by a live run

These cost real time in the R1 runs of this collection's own evaluation, and
none of them is discoverable from the error message alone.

- **`containers-run` with a registered container, not `datalad run` around a container command.**
  Only the first records the image, which is what must/006 and must/015 read.
  Wrapping `datalad containers-run …` in `datalad run` nests one record inside
  another and declares no inputs or outputs.
- **`run` versus `exec` in the registration.**
  `///repronim/containers` registers images with
  `cmdexec = {img_dspath}/scripts/singularity_cmd run {img} {cmd}`, and `run`
  hands the command to the image's own runscript. For the neurodesk images that
  runscript re-parses its arguments through a shell, so a Python entry point
  fails as `import: command not found` and a bare subject id fails as
  `sub-20919: command not found`. Re-register with `exec` (`datalad containers-add
  --call-fmt '… exec {img} {cmd}'`), or pass one argument that is a file the
  command reads.
- **A registered container's name takes only letters, digits and `-`.**
  `datalad containers-add synthstrip-7.4.1` is refused ("only alphanumeric and
  '-'"), so a version in the name becomes `synthstrip-7-4-1`.
- **Pin the image, not the dataset.**
  `///repronim/containers` ships `scripts/freeze_versions`, which rewrites the
  registration to a specific image version; without it the registration names a
  floating image and must/015 is `unmet`.
- **`-i` globs are evaluated against the whole input dataset.**
  `-i 'sourcedata/ds/sub-*/ses-1/anat/*T1w.nii.gz'` starts fetching every
  subject. Name the files, or the subjects, explicitly.
- **`datalad run` refuses a dirty tree** with "clean dataset required to detect
  changes from command", which does not say what is dirty: commit the scripts
  first, and keep logs and scratch output *outside* the dataset.
- **A shared host is shared.**
  Two recorded runs under one process table are indistinguishable to
  `pkill -f 'datalad run'`: in these evaluations one arm's cleanup killed
  another arm's jobs. Kill by pid.
- **A registered image has no file extension.**
  `datalad containers-add <name> --image <path>` copies the image to
  `.datalad/environments/<name>/image`, and `containers-run` records the
  *expanded* call, so the record names neither a `.sif` nor `containers-run`.
  This is the normal layout for a locally built image; a grader that looks for
  a suffix reports it as naming no environment (the probes here were fixed
  after a run hit exactly that).
- **`containers-add --url file://…` is refused.**
  git-annex's `annex.security.allowed-url-schemes` does not include `file`, so
  registering an image that is already on disk takes `--image <path>` (which
  copies it) rather than a URL.
- **A run whose outputs come out byte-identical makes no commit**, so it leaves
  no new record. Re-running the same step inside a container to *get* a record
  that names the container therefore records nothing: remove the output and
  re-derive it, and say in the message that the content was re-checked rather
  than overwritten.
- **Building an image inside a rootless container usually fails.**
  `apptainer build --fakeroot` needs setuid `newuidmap`/`newgidmap`, which a
  rootless podman session does not have (`newgidmap: Could not …`). Register a
  prebuilt image — `///repronim/containers` is the pinned route — rather than
  installing packages into an untracked bind mount, which leaves a fresh clone
  unable to reconstitute the environment.

## Version notes

- Pin `datalad` to a release carrying the concurrent-run fix ([datalad#7899](https://github.com/datalad/datalad/issues/7899), [#7901](https://github.com/datalad/datalad/pull/7901)) wherever runs may overlap.
- `datalad`, `datalad-container`, `git-annex` (its PyPI wheel ships a standalone build) and `con-duct` install from PyPI, so the project's own tooling can be pinned in the same tracked spec as everything else:
  ```console
  uv tool install datalad --with git-annex --with-executables-from git-annex
  ```
  must/010 and must/013 apply to that spec too, not only to the analysis containers.

## Laying out a new DataLad project

- `datalad create -c text2git` when the text files may be shared publicly (keeps text in git, content in the annex).
- Inputs as subdatasets (`datalad clone -d . <url> <path>`), never as copies and never as absolute paths.
- An entry point named in `README.md` that a stranger can run, and a `Makefile` or workflow that calls the recorded mechanism.
- CI that re-executes at least one unit, so A.2 and should/002 have evidence rather than intent.
- A sibling and a push as soon as there is anywhere to push to (`datalad siblings add --name published --url <url>` then `datalad push --to published`), with the URL in `README.md` and `git ls-remote` as the proof. A local bare repository is a target too: it exercises the same mechanism, and `datalad push` carries annexed content to it.
