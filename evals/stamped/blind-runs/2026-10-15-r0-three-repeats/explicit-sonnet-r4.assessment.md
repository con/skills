# STAMPED assessment: ds007116 brain volume vs age (kind: study, assumed, unconfirmed: no user)

MUST: 14 met / 3 partial (must/009, must/016, must/017) / 0 unmet / 0 not-checked of 17. SHOULD: 2 met (should/001, should/003) / 1 partial / 2 unmet (should/005, should/007) ... see response JSON for the full table (`python3 encode_response.py table 2026-10-15-response.json`). should/002 and should/006 were answered by the probe before the CI workflow was added (probe re-run: partial); should/004 not-checked.

What to fix first (known gaps handed to me, not chosen):
1. must/016: the only publishing target is a local bare repository path, not a URL others can reach; needs a forge remote.
2. must/009: the README names that host path (the publish target); unavoidable until (1).
3. must/017/should/002/should/006: CI workflow `.github/workflows/rerun.yml` is written but has never run; needs a runner.

Already good: every derived file has a datalad run record naming the lockfile (must/006, must/015); input is a subdataset with a resolvable URL; lockfile pins the tooling too.

Where products went: this directory, outside the project (the project tree stays clean for must/004).
Probe output: 2026-10-15-probes.json; response: 2026-10-15-response.json; app URL: 2026-10-15-url.txt.
Produced by assess-alignment-with-stamped-principles 0.1.0 with stamped-conventions 0.1.0, checklist 0.3.1, claude-code/claude-sonnet-5-5, 2026-10-15.
