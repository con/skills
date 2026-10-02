# When pull requests come from forks

The template workflows run `on: push`, which fires for every branch pushed to the repository itself, where the two project tokens are available as secrets.
That is the right trigger for a repository whose contributors all push branches to it, and it is what Chromatic needs: a build for every commit on a branch, or there is no baseline to compare the next one with.

A pull request from a fork is different.
Its commits are pushed to the fork, where the `on: push` run has no access to this repository's secrets, and the `pull_request` event it raises in this repository runs with secrets withheld, by GitHub's design.
Either way the token is missing and the upload cannot happen, so a repository that takes outside contributions splits each workflow in two, as [dandi/usage-page](https://github.com/dandi/usage-page) does:

- `chromatic.yml` and `chromatic-playwright.yml` run on `push` and `pull_request`, build with no token (Storybook via `build-storybook`; the Playwright archives via `build-archive-storybook --output-dir=storybook-static`), and upload `storybook-static/` as a one-day artifact.
- `chromatic-publish.yml` runs on `workflow_run`, from `main` and therefore with the tokens.
  It checks out the built commit by hash (for the git history Chromatic reads baselines from), downloads the artifact, and runs the CLI with `--storybook-build-dir`, `--exit-zero-on-changes`, `CHROMATIC_SHA`/`CHROMATIC_BRANCH`/`CHROMATIC_SLUG` set from the triggering run, and `--auto-accept-changes` only for a push to the repository's own `main`.

Copy those three files from that repository when this applies, and keep the two-workflow form from the templates otherwise.
Ask the user which case the repository is in (step 0 of SKILL.md) rather than inferring it from the current contributors.
