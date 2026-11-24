# Lens: ci-infra

Continuous integration and delivery, release automation, containers and
infrastructure as code: what runs with the project's credentials.

## Recognize

`.github/workflows/*.yml`, `.github/actions/`, `.gitlab-ci.yml`,
`.circleci/`, `azure-pipelines.yml`, `Jenkinsfile`; `Dockerfile`,
`Containerfile`, `docker-compose*.yml`, `.dockerignore`; Kubernetes
manifests and Helm charts; Terraform (`*.tf`), Ansible and other
infrastructure code; `dependabot.yml`, `renovate.json`,
`.pre-commit-config.yaml`; release configuration (`.autorc`,
`.goreleaser.yaml`, publishing jobs).

## Context to read

Which checks are required for merging, which secrets and environments the
workflows use, where the project deploys or publishes, and the reusable
workflows or actions it shares with other repositories.

## Checks

**GitHub Actions security** (usually blocking)
- Script injection: `${{ … }}` expressions holding text an outsider controls
  inside a `run:` script or an `actions/github-script` body, such as the
  title, body or branch name of a pull request (`github.head_ref` too), an
  issue or comment body, or a commit message. Pass them through `env:` and
  quote the variable.
- `pull_request_target` or `workflow_run` workflows that check out or run
  code from the pull request, or use its artifacts or caches, while holding
  secrets or a write token.
- `permissions:` missing (the default token may be read-write) or broader
  than the job needs; set `contents: read` at the top and widen per job.
- Third-party actions not pinned to a full commit SHA; `actions/checkout`
  without `persist-credentials: false` in jobs that do not push.
- Secrets printed, passed on the command line, or given to steps that run
  pull request code.

**Workflow correctness** (should-fix; blocking when a required check can no
longer pass)
- Triggers and `paths` filters: a required check that is skipped by a path
  filter never reports, and the pull request waits forever.
- `if:` conditions: one that mixes `${{ }}` with text outside it is a
  non-empty string, so it is always true.
- `continue-on-error`, `|| true` or a missing `set -e` that hides failures;
  a shell without `pipefail` where a pipeline's failure matters.
- The matrix covers the versions and platforms the project says it
  supports; cache keys include the lockfile's hash; `concurrency` with
  `cancel-in-progress` on a release or deploy job can stop it half way.
- Timeouts on jobs that can hang.

**Release and deploy** (blocking when it can publish the wrong thing)
- The version and tag are computed as the release process expects; publishing
  is idempotent or guarded; deploys go through protected environments;
  there is a way back.

**Containers** (should-fix; blocking for leaked secrets)
- Base images pinned to a version or digest; the process does not run as
  root without a reason; secrets never land in a layer (`ARG`, `ENV`, a
  copied file); `.dockerignore` keeps `.git`, `.env` and local data out;
  package caches are cleaned in the layer that creates them.

**Infrastructure code** (usually blocking)
- Changes that replace or destroy a resource (data stores especially);
  public exposure (`0.0.0.0/0`, public buckets); access rights wider than
  the task.

**Automation configuration** (optional)
- Dependabot or Renovate scope, grouping and schedule; pre-commit hooks
  pinned to a revision.

## Not findings

- YAML formatting and key order.
- Minor version bumps of actions with no reason given, when pinned to a SHA.
- The choice of CI provider.

## Verification

- **static**: `actionlint` on copies of the workflow files in a scratch
  directory (it reads the repository's own configuration otherwise), a
  workflow security linter such as `zizmor` run the same way and offline,
  and `hadolint` on a copied `Dockerfile`; read the workflow run of the pull
  request itself.
- **consent**: building the container, `terraform plan` (it also needs
  credentials), running the workflow locally.
- If your companion skills include `code-quality-review-shell`, apply its
  checks to the shell inside `run:` steps.
