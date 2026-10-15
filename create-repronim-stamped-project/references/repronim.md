# ReproNim implementation reference

Use only the sections relevant to the chosen workflow.
Preserve the user's existing tooling and instructions.

## Data and modules

Install upstream datasets at exact revisions; fetch the subset needed for the pilot.
DataLad/git-annex can preserve large-content identities and retrieval routes while parent gitlinks identify child states.
Each concurrent writer needs its own checkout and writable submodules.
Keep source metadata, licenses and access terms; an annex key or Git commit does not prove content is retrievable.

Follow the applicable [BIDS specification](https://bids-specification.readthedocs.io/) and derivative conventions.
Keep raw inputs unchanged; identify derivative source links, generating software and subject/session/run exclusions.
Use the community BIDS validator for conformance and separate checks for event semantics, units and scientific suitability.

## Task environments

Use a project-local environment manager such as Pixi; add dependencies as work develops.
Prefer maintained scientific packages and domain tools over custom substitutes.
Keep host runtimes, scheduler interfaces and credential providers explicit and replaceable.

Honor the project's lock policy.
When it calls for loosely pinned manifests and locks outside normal history: ignore task locks, preserve the exact final-validation bytes without re-solving, and commit them as ordinary Git blobs on a snapshot branch one commit above the final task commit.
Install ignore/annex exclusions before that task commit. Record immutable code/snapshot IDs, hashes and platform; do not merge the snapshot into main.
Replay must restore the matching lock and manifest, including when DataLad selects an earlier code revision.

## Recorded execution and retrieval

Use the project's DataLad `run`/`containers-run` mechanism with explicit inputs, outputs and environment identity.
Use the project's `datalad-annex` skill when available for operational details.
Confirm native record discovery through the actual commit hooks; a retained record is not proof that native rerun recognizes it.
Compose hooks rather than replacing existing capture, formatting or attribution behavior.

Restore the recorded environment explicitly; DataLad rerun alone does not reconstruct it.
Replay declared generated outputs in a disposable checkout with those outputs absent; compare their content with a separate expected result.
Do not delete inputs or mutate shared annex objects.
For delivery, publish/retrieve child commits and required annex bytes before relying on parent gitlinks.
A cluster-to-local-to-remote relay is valid when both hops preserve identities and permit independent retrieval.

## BIDS Apps and scaling

Use the selected community BIDS App and orchestrator; MechaBABS when requested.
Consult official installed-version usage/configuration rather than inventing commands. Pin container identity and record host/runtime requirements.
Before a batch, verify one inexpensive job through submission, output collection, QC and requested provenance.
Size the batch from measured resources and scheduler policy; retain failed attempts separately.

Native agent history, computational logs and transformation records establish different facts.
Link requested records by run identity and retain them with the owning module; do not enable account-level collectors as a side effect.
