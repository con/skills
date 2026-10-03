# When pull requests come from forks

The template workflows run `on: push`, which fires for every branch pushed to the repository itself, where the two project tokens are available as secrets.
That is the right trigger for a repository whose contributors all push branches to it, and it is what Chromatic needs: a build for every commit on a branch, or there is no baseline to compare the next one with.

A pull request from a fork is different.
Its commits are pushed to the fork, so the `on: push` run happens there, without this repository's secrets; in this repository nothing runs, since the templates do not listen to `pull_request`, and adding that trigger would not help on its own, because GitHub withholds secrets from the runs it starts for a fork's pull request.
That is why a repository that takes outside contributions splits each workflow in two, as [dandi/usage-page](https://github.com/dandi/usage-page) does:

- `chromatic.yml` and `chromatic-playwright.yml` run on `push` and `pull_request`, build with no token (Storybook via `build-storybook`; the Playwright archives via `build-archive-storybook --output-dir=storybook-static`), and upload `storybook-static/` as a one-day artifact.
- `chromatic-publish.yml` runs on `workflow_run`, from `main` and therefore with the tokens.
  It checks out the built commit by hash (for the git history Chromatic reads baselines from), downloads the artifact, and runs the CLI with `--storybook-build-dir`, `--exit-zero-on-changes`, `CHROMATIC_SHA`/`CHROMATIC_BRANCH`/`CHROMATIC_SLUG` set from the triggering run, and `--auto-accept-changes` only for a push to the repository's own `main`.

Copy those three files from that repository (`.github/workflows/` on its default branch) when the user said forks contribute, and adapt them, since they predate parts of this skill:

- Save the Storybook one as `chromatic-storybook.yml`, the name the README badges and step 11 use, and keep the two `name:` values exactly as `chromatic-publish.yml` lists them under `workflow_run.workflows`.
- Replace `dandi/usage-page` in the publish workflow's `if:` guard with the repository's own `<org>/<repo>`.
- Pin `runs-on` to `ubuntu-24.04` and `node-version` to 22, and add the two report steps from the templates, for the reasons the templates give.
- Add `CHROMATIC_STATIC_VERSION: "true"` to the `env` of the Storybook build step and the Playwright test step, or the version pin from step 8 never applies in CI.

In the README section, say that a fork's pull request is built without a token and uploaded by `chromatic-publish.yml`, which runs from `main` with the tokens, so its Chromatic checks appear once the build workflow has finished.
