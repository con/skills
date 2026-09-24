---
name: author-apm-skills
description: Create, update, package, and validate reusable skills specifically for distribution through APM, including maintenance in con/skills or another dedicated skill repository. Use when APM distribution or maintenance of that published collection is requested. Do not trigger for a generic request to create a skill, a project-local experiment, or a downstream installation alone.
---

# Author skills for APM distribution

Develop reusable skill source in a dedicated repository, normally `con/skills`.
Consumers receive ignored generated copies through APM and track dependency metadata.
Do not develop reusable skills inside an application repository and then commit their evolving content there.

## Source and scope

- Locate the actual canonical repository and read its AGENTS.md, contribution guide, CI, package manifest, and PR template.
  Use an isolated branch/worktree when needed.
  Do not edit an APM-deployed consumer copy as the source.
- Find existing skills before adding another.
  Keep the trigger specific to the workflow; generic skill creation does not imply APM distribution.
- Preserve existing source layout when APM can publish it.
  In `con/skills`, each `skills/<name>/` directory is canonical and the root `apm.yml` publishes `skills/`.
  Add a new skill directory there.
  In a new package, `.apm/skills/<name>/` is also a valid canonical layout.
  Track source in either layout; do not maintain duplicate editable trees.

## Author a portable skill

Create `SKILL.md` with `name` and a discriminating `description`.
Include only workflow-specific guidance; put substantial conditional detail in linked references.
Bundle required scripts, templates, and assets inside the skill.
Resolve their paths relative to the installed skill, not the consumer's cwd.
Declare real tool prerequisites.
Do not rely on a parent repository's AGENTS.md or a sibling skill to supply essential operating instructions after deployment.
In particular, PR-producing skills must carry the required template and contribution-guide checks within their own deployed content.

Specify how untrusted task inputs are handled when relevant.
Do not grant permissions, infer approval to post/publish, or expand a task's scope merely because the skill was invoked.
Test helpers in isolation using task-shaped inputs; review trigger examples that should and should not select the skill.

## Package and assess

Use the repository's existing checks.
In `con/skills`, run:

```console
tox -e validate,apm,security-static,security-deps
```

The package check must install into a disposable consumer, verify all selected skills and bundled resources, discard only that disposable deployment, restore from the same manifest/lock with `apm install --frozen`, and run `apm audit --ci`.
Confirm installed content is ignored and setup metadata stays unchanged.
A local-path test checks packaging; before adoption, also test the published Git repository at the exact commit consumers will pin.

For another repository, establish equivalent CI using its existing tooling: structural validation, helper tests, APM replay/integrity, skill-content static scanning, and known-vulnerability checks on declared Python/tool dependencies.
Use read-only CI permissions and pinned tools/actions.
Treat PR content as untrusted: do not execute it with privileged `pull_request_target` credentials.
Scheduled scans can catch advisories published after a merge.
Security checks identify findings, not proof that a skill is safe or useful.
Fix findings or record narrow, justified exceptions; do not blanket-disable scanning to pass.
LLM assessment is a separate, explicitly configured check with credentials, costs, and untrusted-input containment considered; it is not required to run a secret-free basic PR gate.

## Publish and consume

Inspect the actual diff and report test outcomes, including failures.
Follow repository commit and PR conventions; open a PR only when authorized.
Keep source content changes in the dedicated repository.
Do not claim a branch is available from `con/skills` until it exists there; an unmerged fork is a separately identified source.

After publication, downstream adoption changes the requested APM source/ref and generated lock.
Use the consumer's pinned APM environment, explicit target and skill selection, ignored deployment paths, setup task, AGENTS.md note, and fresh-checkout validation.
Do not copy source into downstream Git history.
