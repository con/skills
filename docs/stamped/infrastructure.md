# STAMPED skills evals: infrastructure

Companion to [PLAN.md](PLAN.md) §6.8 and §7: where eval results live, how they are published, and how a session on typhon starts.

## Results dataset

[`con/stamped-skills-evals`](https://hub.centerforopenneuroscience.org/con/stamped-skills-evals) is a DataLad dataset on the CON Forgejo-aneksajo hub.
Aneksajo is the git-annex-aware Forgejo, so git history and annexed content go to the same remote with no separate special remote.

- **Layout:**
  - each run is a subdataset (the produced object), plus `transcript.jsonl` (annexed), `grading.json` and stamped-assessment records;
  - grading steps are `datalad run` records;
  - con/skills is a subdataset pinned per iteration.
- **Pushing:** from typhon, as `yarikoptic-gitmate` (`datalad push --to hub`).
- **Mirroring:** optional, read-only, to GitHub for visibility; the hub stays authoritative.

This keeps con/skills small and makes every number in a report or a talk re-executable.

## Publishing and privacy

Agent-produced objects can contain things that must not go public by accident: transcripts, absolute paths, host names, environment dumps, and anything a run read from the host.

- **Private first.** Produced objects and transcripts are pushed to a **private** namespace on the hub.
  A human promotes a run to public only after a scan, for secrets (for example `gitleaks`) and for paths (the `no-abs-paths` probe).
  The public `con/stamped-skills-evals` superdataset links only promoted subdatasets, so `subdatasets-resolvable` and `fresh-rerun` test public URLs.
- **What is known about access today** (2026-10-13):
  - `con/stamped-skills-evals` is a **public** repository;
  - the `HUB_TOKEN` network secret authenticates as an account with `push` on it, and lacks `read:user`;
  - its full scope is not recorded here (open question 13 in [PLAN §10](PLAN.md#10-open-questions)); it should be limited to repository write on the evals namespaces, with no admin or organization scopes.
- **The Apache egress allow-list is network gating, not authentication.**
  It admits Anthropic's egress network as a whole, so it says nothing about who is calling; only the token does.

## Cloud sessions

A cloud session in the environment used for this plan can reach the hub.
A dry-run push of a probe branch was accepted (nothing was written); a real push has not been tried.
Three things make that work:

- **Network:** `*.centerforopenneuroscience.org` and `*.stamped-principles.org` (plus the bare domains) are under Allowed domains, with the package-manager defaults kept.
- **Hub access control:** the hub's Apache admits Anthropic's egress network.
- **Credentials:** a `HUB_TOKEN` network secret scoped to `hub.centerforopenneuroscience.org`, so the proxy adds the `Authorization: Bearer` header and the session never sees the token.

`datalad` and `git-annex` are not preinstalled in cloud sessions, but both come from PyPI (the `git-annex` wheel ships a standalone build).
Either of these works (tested: datalad 1.7.1, git-annex 10.20260901):

```sh
uv tool install datalad --with git-annex --with-executables-from git-annex
# or, in a venv:
pip install datalad git-annex
```

Put that line in the environment's setup script so the environment cache keeps it.
Pin versions there, and pin datalad to a release with the concurrent-run fix (gh-7899/#7901).

## Starting on typhon

For a Claude Code session on typhon (under Remote Control) picking this up:

1. Continue from branch `claude/ecstatic-cerf-nh4j6w` of con/skills ([#24](https://github.com/con/skills/pull/24)), or branch off it.
2. **Check the host:**
   - `apptainer --version`;
   - free scratch space (R1 needs a few GB per container image);
   - `claude --version`, for headless outer-loop runs;
   - `uv`.
3. **Install pinned tooling** for the outer-loop runner: `datalad`, `datalad-container`, `git-annex` (PyPI wheel) and `con-duct`, recorded in `evals/stamped/` as a requirements or lock file.
4. **Bootstrap `con/stamped-skills-evals`** (phase 2 of the plan):
   1. `datalad create -c text2git`;
   2. add con/skills as a subdataset;
   3. add the hub as a sibling, plus a private namespace for unpromoted runs;
   4. `datalad push`.
5. **Then follow [PLAN §7](PLAN.md#7-roadmap)** from the current phase.
