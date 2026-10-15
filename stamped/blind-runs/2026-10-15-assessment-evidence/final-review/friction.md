# Followability notes

The frozen skills were sufficient to resolve these cases without consulting
repository tests, another report, or an older snapshot. The instruction to
compare the actual execution route against declarations was essential: filenames
and a quiet host-tool scan would not separate the two numerical cases. The
retrieval guidance correctly separates location metadata from payload access.

Observed friction and bounded improvement suggestions:

1. `env-spec-tracked` prints one aggregate status (`unmet` for both numerical
   objects), even though its item statuses differ by question. Read the JSON
   item_status table; the summary cannot be treated as must/010's verdict.
2. `--only env-spec-tracked` still emits all three mapped items. A scoped reviewer
   must explicitly leave unwanted suggestions unassessed. An item-scope display
   or explanatory summary would make this safer.
3. With remote checking disabled, the annex probe reports `partial` rather than
   `not-checked` on access. The prose warns that access is unverified, so it does
   not falsely pass, but a recorded remote alone is not evidence of some actual
   access. Clarifying the partial/not-checked boundary would align the automated
   status with the verdict vocabulary.
4. The execution receipt omits the documented pip-install phase and its venv was
   created without pip. It supports the import failure but is not an exact
   documented-route replay. Future receipts should record setup, installation,
   command environment, timestamps and outputs together, without credentials.
5. The retrieval receipt clones Git history from the source fixture and fetches
   payload bytes from a subsequently configured local store. It should not be
   described as complete publication retrieval from that store or public access.
   Explicitly naming the source of history separately from the source of payload
   bytes makes the scope clear.
6. The skill's formal full-response validation and four-product instructions
   exceed this explicitly scoped engineering task. The request intentionally
   overrides those packaging requirements; no incomplete full-checklist response
   or URL was produced.

No skill edits were made. These are followability observations and suggestions,
not additional checklist judgments.
