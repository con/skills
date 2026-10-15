# Host notes

Facts about the machine this run happens on. They are *environment*, not
*method*: an identical copy of this file is placed in the sandbox of every
condition — `bare`, `pointer` and both skill arms — so no arm is helped more
than another, and nothing here says anything about how to organise a project.

- 32 CPU cores, ~1 TB RAM, **no GPU**; a few hundred GB free on this
  filesystem.
- `datalad`, `git-annex` and `apptainer` are on `PATH`; `python3` has `nibabel`,
  `numpy`, `pandas` and `matplotlib` available through `uv` if not directly.
- **Network:** general HTTPS works, but `datasets.datalad.org` resolves and
  then refuses the connection from here, so the DataLad registry shortcuts
  (`///repronim/containers`, `///openneuro/dsXXXXXX`) cannot be cloned through
  it. The same datasets are reachable from their GitHub mirrors, e.g.
  `https://github.com/ReproNim/containers` and
  `https://github.com/OpenNeuroDatasets/ds007116`.
- Container images are 0.5–9 GB each. For the neurodesk images git-annex knows
  a second web source, which works here. Point `APPTAINER_CACHEDIR` at a
  directory with room: `$STAMPED_SHARED_CACHE` is one, shared between the arms
  of this evaluation, so an image another arm already pulled is free.
- **Fetch only the files you need.** The input dataset is large, and a previous
  run pulled several GB by accident with a too-broad `datalad run -i` glob.
- `gh` is not authenticated, and there is no push access to anything. Nothing
  here needs to be published.
- Wall-clock guidance: skull-stripping one T1w takes seconds to a couple of
  minutes on this host, so ten subjects is minutes, not hours. If something
  looks like it will take an hour, it is the wrong approach.
