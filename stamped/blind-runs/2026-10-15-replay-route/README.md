# Local-source annex routes for fresh replay

Source tested: `89374d7727efd2bccc48cfa917d7751ff95f497e`, based on working skills `c90252a7b9072a4828e9c0b1fa6e5f48409a9cfa`.
The helper is byte-identical to the coordinator candidate: SHA256 `2f9a66a52dfdc81a48a7950f3df9ae556d104bf16c1171294532bac3ddf7adbd`.
`source.bundle` contains this source commit and requires the base commit.

A fresh local clone loses ordinary Git remote configuration.
In the observed failure, the source retained locked annex pointers but lacked those payloads; independent recipient checks had already retrieved the published bytes.
The candidate copies only explicitly configured local-source URL, annex URL, and annex UUID fields into named scratch-clone remotes.
It rejects incomplete, ambiguous, command-bearing and embedded-credential addresses, and records the route origin and same-host scope.
It does not change the original repository, URL-based cloning, the scientific rubric, or formal pins.

## Retained evidence

- `original-candidate/`: exact coordinator handoff patch, manifest, fixture script and distinct-key native summary.
  The coordinator's earlier test-01 used aliased keys and is inadequate as an independent missing-content control; test-02 replaces that control without erasing its history.
- `test_replay_route.py`: independent rerun of the native fixture; arguments are a new output directory, candidate helper and old helper.
  It requires DataLad/git-annex in the operational Pixi environment and the user-level provenance resolver for its fixture commit.
  It contains no scientific data.
- `native/`: exact command/stream records, old/candidate/no-route reports, source before/after state, and summary.
  Distinct input, locked-output and unlocked-output keys prevent one retrieval from satisfying another key.
- `primary-prompt.txt`, `small-prompt.txt`: verbatim blind prompts.
  The primary reviewer requested a clarification about native scratch-clone commits; `primary-clarification.txt` preserves the response.
  Source/skill commits were prohibited; helper housekeeping commits were permitted.
- `primary/`, `small/`: independent replay products and friction reports.
  The small tier was gpt-6-luna/high.
  No reference answers or earlier reports were provided.
  Both assessed the exact pinned snapshot.
- `checks/`: commands and complete output for 147 ordinary tests, 26 eval cases, 18/18 detected mutants, and lint of 27 skills with zero errors and ten pre-existing warnings.
  Ten new Git-config tests exercise route filtering and source preservation.
  `first-suite-failure.json` retains the earlier mocked-source harness failure and its correction.

## Findings and limits

The old helper cannot check the mixed locked/unlocked object. The candidate retrieves the missing content, removes the shipped outputs, executes the entry point, and reproduces both outputs byte-for-byte. Source HEAD, status, configuration and file availability/hashes remain unchanged.
Without a route, the mixed fixture remains not checked and stops before execution.
Both blind reviewers independently distinguish this from a failed scientific replay.

These checks establish same-host replay with explicitly configured access.
They do not establish public access, cross-host portability, arbitrary remote transports, subdataset route propagation, or scientific validity.
Supported address forms are deliberately narrower than all Git transports.

The small-tier reviewer noted that the skill's example uses `--url` while this request uses `--path`; the helper's existing help resolved the distinction.
This is nonblocking wording friction, not evidence for adding a new universal rule.
The primary review identified an existing missing-artifact defect: `_sha256` can hash an unavailable unlocked annex pointer as output content.
The mixed no-route target still returns not checked because its locked output is missing, so it is not a complete unlocked-only boundary regression.

`unlocked-only.json` confirms that a no-route, unlocked-only comparator lets the entry execute before returning not checked via the failed-get fallback.
`unlocked-only-keep.json` remains not checked because `--keep-outputs` cannot prove recreation, but also records a pointer hash rather than unavailable content.
These controls do not establish a false met result; they establish an invalid comparator and unnecessary execution.
This pre-existing defect is a separate development follow-up, reported to the formal coordinator.
No comparator correction is included in this route-only source commit.

The formal coordinator owns any explicit assessment/protocol amendment and consistent reassessment.
Preserve original formal objects and judgments; this development candidate alone does not authorize a formal repin.
