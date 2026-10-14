# ReproNim implementation choices

Select tooling for the scientific question and execution environment.
These defaults implement this adapter; they do not amend STAMPED's principles.

## Dataset and environment boundary

Retain the exact upstream dataset revision, selected files/subjects/sessions, metadata descriptions, content identifiers, retrieval routes, access terms, and licenses.
Public metadata does not imply unrestricted access to all data.
Install only needed dataset content initially.
Keep unrelated upstream history and licenses intact; make derived outputs a separate identified component.

DataLad/git-annex can combine code/text identity with large-data identity and retrieval.
A superdataset should pin subdataset states; an unrecorded dirty subdataset is not captured by a parent commit alone.
Do not confuse repository metadata availability with actual annex-content availability.
Verify retrieval of needed content and preserve a supported alternate route if one exists.

Declare the Python/data/provenance tools in the project's environment manager, such as Pixi.
Use its lock and recorded platform support; an activated global environment is not the project specification.
Keep package-cache retention separate from a documented restoration procedure.
Record explicit host-only requirements such as Apptainer, Docker, scheduler commands, or GPU drivers.

## BIDS-aware outputs

Use the applicable [BIDS specification](https://bids-specification.readthedocs.io/) and its version when choosing metadata and layout.
Keep raw data immutable; identify generated datasets as derivatives where the specification applies, retain source dataset links and generating-software metadata, and keep figures and tabular analyses in a documented output boundary.
Validate inputs/outputs at the appropriate level; a successful validator does not verify the scientific meaning of columns or labels.
Preserve event-code semantics and units.

## Executable provenance and replay

Use the project's established DataLad run or containers-run mechanism for transformations, with explicit inputs, outputs, command, parameters, and environment identity.
Record the exact commands supported by the installed versions.
DataLad rerun replays a command; it does not by itself rebuild the historical software environment.
Restore that environment explicitly before calling the result a historical replay.
Compare the recorded target outputs, not merely whether Git produced a new commit.

For BIDS Apps, MechaBABS or another already selected orchestrator can manage job isolation, containers, inputs, and result collection.
Discover its current official command/API and configuration from the installed package and linked documentation.
Begin with a bounded one-job pilot that verifies the entire collection path.
Derive batch size and walltime from measurements and policy, preserving failed jobs and interventions.
No fixed cluster or dataset is required by this adapter.

## Examples as design inputs

[ORINOCO Lite](https://github.com/ORINOCO-Lite/orinoco-lite-dev) and [the STAMPED morphometrics project](https://github.com/STAMPED-dl-morphometrics-biases/STAMPED-dl_morphometrics_biases) provide examples of composing versioned data with declared environments.
Inspect and pin the relevant source before adapting a pattern.
Do not import their scientific assumptions, paths, credentials, or tool installation quirks as universal requirements.
An expensive imaging pipeline is not necessary for a tabular scientific question.
