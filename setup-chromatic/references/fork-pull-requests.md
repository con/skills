# When pull requests come from forks

The template workflows run `on: push` (step 7 says why), which fires for every branch pushed to the repository itself, where the two project tokens are available as secrets.
That is the right trigger for a repository whose contributors all push branches to it.

A pull request from a fork is different.
Its commits are pushed to the fork, so the `on: push` run happens there, without this repository's secrets.
In this repository nothing runs, since the templates do not listen to `pull_request`.
Adding that trigger would not help on its own: GitHub withholds secrets from the runs it starts for a fork's pull request.
That is why a repository that takes outside contributions splits each workflow in two, as [dandi/usage-page](https://github.com/dandi/usage-page) does:

- `chromatic.yml` and `chromatic-playwright.yml` run on `push` and `pull_request`, build with no token (Storybook via `build-storybook`; the Playwright archives via `build-archive-storybook --output-dir=storybook-static`), and upload `storybook-static/` as a one-day artifact.
- `chromatic-publish.yml` runs on `workflow_run`, from `main` and therefore with the tokens.
  It downloads the artifact, fetches the built commit by hash (for the git history Chromatic reads baselines from), and runs the CLI with `--storybook-build-dir`, `--exit-zero-on-changes`, `CHROMATIC_SHA`/`CHROMATIC_BRANCH`/`CHROMATIC_SLUG` set from the triggering run, and `--auto-accept-changes` only for a push to the repository's own `main`.

Use those three files (`.github/workflows/` on that repository's default branch) as the model when the user said forks contribute, and review each before adopting it, since they predate parts of this skill.

The publish workflow holds the tokens while handling a commit from a fork, so these are the properties to keep, all present in dandi's file except the first:

- Add `persist-credentials: false` to the checkout of `main`, so the job's token is not left in that checkout's `.git/config`.
- Nothing from the built commit executes: the Chromatic CLI is installed from the `main` checkout with `npm ci --ignore-scripts` and run from there; the built commit is fetched by hash into a separate directory, read only for its git history; the Storybook comes from the artifact. No `npm`, `npx` or workspace script runs against the commit.
- The CLI gets `--config-file` pointing at an explicit empty file, so a `chromatic.config.json` in the commit is not read.
- The head SHA, branch and repository from the triggering run reach the shell only through `env:`, never inline in `run:`.
- `--auto-accept-changes` is added only when `workflow_run.event == 'push'`, `workflow_run.head_branch == 'main'` and `workflow_run.head_repository.full_name == github.repository`, since a fork's branch may be named `main` too.

Adaptations the files need:

- Save the Storybook one as `chromatic-storybook.yml`, the name the layout in SKILL.md and the README badges use, and keep the two `name:` values exactly as `chromatic-publish.yml` lists them under `workflow_run.workflows`.
- Replace `dandi/usage-page` in the publish workflow's `if:` guard with the repository's own `<org>/<repo>`.
- Pin `runs-on` to `ubuntu-24.04` and `node-version` to 22, and add the two report steps from the templates, for the reasons the templates give.
- Add `CHROMATIC_STATIC_VERSION: "true"` to the `env` of the Storybook build step and the Playwright test step, or the version pin from step 8 never applies in CI.

In the README section, say that a fork's pull request is built without a token and uploaded by `chromatic-publish.yml`, which runs from `main` with the tokens, so its Chromatic checks appear once the build workflow has finished.
