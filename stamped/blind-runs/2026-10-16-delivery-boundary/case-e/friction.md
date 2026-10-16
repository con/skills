# Assessment friction

- **Probe scope required a second inventory.** The skill says, “The probes cover 13 of the 17 MUST items” and later, “Start with the supplied delivery inventory and documentation; use Git history and tracked-path probes where applicable, then inspect artifacts and execution records they omit.” The entry-point and module probes saw only the two tracked seed paths, while the original delivery also had untracked `analysis.py`, `requirements.txt`, and ignored `products/estimate.json`. I ran the probes, then checked the receipt and the complete supplied file inventory and read those files. This correctly changed the entry-point and module judgements.

- **Three checklist items divide software requirements differently.** The checklist asks whether external software is included or linked (must/003), all dependencies are specified (must/010), and dependencies are linked as modules (may/001). The conventions clarify that packages are not project modules, but do not fully define whether a requirements declaration alone counts as inclusion for must/003. I treated NumPy as an external package dependency: no environment supplies it (must/003 unmet), its lower bound is declared but incomplete (must/010 partial), and it is not a project module (may/001 N/A). A one-sentence boundary rule here would reduce assessor variation.

- **The reason/evidence workflow is exacting but understandable.** The skill says, “Write every reason under 250 characters from the start” and “Every one of the 31 items gets your answer.” I kept rationales short and used evidence entries for the specifics, then validated all 31 answers. The workflow required separate in-place `set` calls for judgements and flags; the prescribed encoder works, though it makes a small object fairly laborious.

## What I checked

I confirmed the vendored checklist pin with `vendor_checklist.py --check`, ran the supplied probes, and read the original stop receipt, Git status/history/remotes, `input.csv`, `analysis.py`, `requirements.txt`, `.gitignore`, and `products/estimate.json`. I manually recomputed the finite count and mean. I validated the response and generated the checklist URL. No object instruction-like text was present.

## What remains unchecked

No remote is configured, so no external issue tracker or publication route could be inspected. There was no evidence in the supplied delivery of external test history or a fresh-environment run; those remain not-checked in the report. I did not execute or replay the analysis, inspect outside this case's object/receipt/skill snapshot, modify the source, commit, or publish anything.
