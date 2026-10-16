# Skill-use friction

- The skill says to fill metadata “with `stamp` rather than a snippet of your
  own” and to use the UTC assessment date. However `stamp` leaves the supplied
  `assessor.date: null` unchanged and has no date option. Validation failed with
  `assessor/date: None is not of type 'string'`. I retained the failed duct log,
  added the UTC date with a metadata-only edit, and revalidated successfully.
- The assignment says “Complete the supplied response.json”, while the skill
  requires “`<date>-response.json`”. I completed the supplied file and retained
  a byte-identical dated copy, explicitly naming the supplied file canonical.
- “The probes cover 13 of the 17 MUST items” is coverage of tracked-path
  heuristics, not delivered-file coverage. This case required many overrides:
  the probes missed the untracked README, script, environment and results.
  The skill does warn about this, but per-item reconciliation was the slowest
  part. Its separate probe-draft instruction prevented capture identity loss.
- `large-in-annex` claimed “git-annex carries the binary content” and cited
  `.datalad/config`, although that path does not exist and the only annexed file
  is a supplied 167-byte CSV. The complete delivery has no large binary subject;
  the final answer is N/A with the mismatch flagged.
- “Exact environment specifications” and “all software dependencies” need
  separate treatment when only direct package pins and an original interpreter
  path are retained. The allowed capture has no resolved transitive metadata;
  I marked completeness not-checked and exactness partial, rather than treating
  an untracked specification as absent or using assessor packages as evidence.
- The manifest says “symlinks: preserved without following” and records no
  omissions, while external skill links point outside the permitted case.
  I verified link text and regular-file hashes without following those links,
  and reported their unmaterialized targets as a capture limitation rather than
  a worker defect. They are not required for the scientific analysis route.

No target change, replay, commit, publication or Workshop capture was made.
