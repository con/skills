# Preserve captured evidence while assessing it

Two independent assessments tested a captured delivery response with the revised skill.
The probe command now refuses to replace a response carrying capture identity; judges use a separate probe draft and review answers into the original response.
Both judges completed the 31-item response while preserving its capture and Git identifiers.
This is a metadata and workflow check, not evidence that their grades are correct or reliable.

Case A found that `stamp` left a template's date empty.
The next snapshot fills a missing date, preserving an existing date and every verdict; case B used that revision.
Case A used Astra/ultra and case B Luna/high, established from the retained native sessions.
Different fixtures and sequential revisions prevent a model-tier comparison.

Case B also exposed a read-only violation: the remote module probe fetched into the assessed repository and added an empty `.git/FETCH_HEAD`.
Its response, report and post-trial capture are retained unchanged; the failed integrity check was not repaired.
The original fixture remains intact; none of its scientific files, Git objects, references or recorded entries changed.
The prospective fix fetches into a temporary bare repository.
Regression tests cover both retrievable and missing revisions and require the assessed tree to remain byte-for-byte unchanged.
A fresh reader then ran the remote check on a new copy of case B and independently confirmed the missing pin without changing the capture.
This narrow case C is a regression check, not another full assessment or held-out object.
Its comparator called the empty `content/external` wrapper unexpected; the canonical capture validator requires that wrapper and passes.
Both the original finding and the coordinator's mechanical verification are retained.

| Finding | Classification | Action |
| --- | --- | --- |
| Probe draft replaced original capture identity | Missing helper safeguard | Refuse the overwrite; use a separate probe draft |
| `stamp` left template date empty | Missing helper behavior | Fill only a missing UTC date |
| Remote check wrote into the assessed object | Helper defect | Fetch in a disposable bare repository |
| Report example omitted N/A and misspelled the license key | Skill wording | Correct the two examples |
| Assignment's response name differed from the default | Handoff wording | Retain the supplied canonical response; no added generic rule |
| Probe missed dirty files and supplied a false annex citation | Probe limitation | Preserve manual overrides and the finding; not resolved here |
| Case B mislabeled host/runtime versions | Host evidence and model interpretation | Retain the incorrect report; external native receipt establishes actual runtime |
| Duct removed quick failure logs by default | Execution harness | Retain observed failure in native records; use `--fail-time 0` in subsequent checks |

The [record](record.json) identifies snapshots, original object commits, exact prompts, native identities, final source hashes and automated validation.
Reports and responses are the agents' original products, not corrected examples.
The [complete iteration evidence](https://github.com/leej3/stamped-in-practice/tree/codex/iteration-narps-neutral-v1/skill-reflection/assessment-capture-skill-01) retains the object histories, snapshots, command logs, raw sessions and failed attempts.
No original NARPS result was regraded and no scientific analysis was replayed in these skill-use trials.
