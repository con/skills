# Why the upload has a workflow of its own

The two build workflows capture and build with no token; `chromatic-publish.yml` uploads what they built, on `workflow_run`, from the default branch, which holds the two project tokens.
[dandi/usage-page](https://github.com/dandi/usage-page) settled on this form, for two reasons that hold for every repository:

- **Pull requests from forks.** A fork's commits are pushed to the fork, so an `on: push` run happens there, without this repository's secrets, and GitHub withholds secrets from the runs it starts here for a fork's pull request as well.
  A workflow that uploads with the token itself cannot snapshot such a pull request at all.
  Building without the token works in either place, and `workflow_run` always runs the publish workflow as it is on the default branch, with the secrets.
- **Merges.** The default branch's build after a merge holds changes that were already reviewed on their pull request.
  Uploaded from one place, it can be accepted as the new baseline on its own (`--auto-accept-changes`); uploaded from each build workflow, every merge leaves a build waiting for review in Chromatic, and a notification about it.

## What the publish workflow must keep

It holds the tokens while handling a commit that may come from a fork, so these are the properties to keep when editing it, each already in the template:

- `persist-credentials: false` on the checkout of the default branch, so the job's token is not left in that checkout's `.git/config`.
- Nothing from the built commit executes: the Chromatic CLI is installed in the default-branch checkout with `npm ci --ignore-scripts`, and the Storybook comes from the artifact.
- The built commit is fetched by hash into a separate directory and never checked out: `git update-ref --no-deref HEAD` points `HEAD` at it, and a stub `package.json` is the only file on disk.
  The CLI runs inside that directory (it needs the commit's git history, not its files) through the default branch's `node_modules/.bin/chromatic`.
  Run inside a checkout, it loads the Storybook config the commit's `build-storybook` script names and starts the package manager it detects there, which honours repository-local configuration: chromatic 18.9.4 ran a script a `.yarnrc` named, with the token in its environment, before it had even authenticated.
- `--config-file` points the CLI at an explicit empty file written outside that directory (`$RUNNER_TEMP`), so it looks for no `chromatic.config.json` there.
- The token is chosen by the secret's name (`secrets[... && 'CHROMATIC_PLAYWRIGHT_PROJECT_TOKEN' || 'CHROMATIC_STORYBOOK_PROJECT_TOKEN']`), so a missing secret stays empty and the CLI stops; choosing between the two secrets' values would fall through to the Storybook token and upload the Playwright archive into that project's baseline.
- The head SHA, branch and repository from the triggering run reach the shell only through `env:`, never inline in `run:`.
- `--auto-accept-changes` is added only when `workflow_run.event == 'push'` (no pull request, from a fork or not), `workflow_run.head_branch` is the default branch (`github.event.repository.default_branch` rather than a literal `main`, so no other branch becomes the baseline), and `workflow_run.head_repository.full_name == github.repository` as a second guard.
- `--exit-zero-on-changes`: changes are reviewed in Chromatic, from its status check, not by failing this run.

## What the three files rely on

- The `workflows:` list in `chromatic-publish.yml` names the two build workflows by their `name:` values, exactly; renaming one without the other silently stops its uploads.
- Both build workflows upload an artifact named `chromatic-build`, which the publish workflow downloads from the triggering run.
- A build workflow skips `pull_request` for a branch of this repository, which its `push` already built, so each commit is built once.
- The job names stay `Run Chromatic (Storybook)` and `Run Chromatic (Playwright)` where branch protection requires them; the upload's result reaches the commit as Chromatic's own status checks, once per project.
- The publish workflow first runs once it is on the default branch: on the pull request that adds it, only the two build workflows run, and the first upload comes from the merge.
- The Chromatic CLI is the `chromatic` devDependency, so its version moves with the lockfile (Dependabot's npm updates), not with an action tag.
- TurboSnap (`onlyChanged`) is not used: it would mean trusting a stats file from the artifact and reading the commit's tree in the job that holds the tokens, and usage-page does without it.
  The cost is that every push snapshots every story in every mode of the Storybook project, which counts against the account's snapshot quota.
