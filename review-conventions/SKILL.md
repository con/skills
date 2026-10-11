---
name: review-conventions
version: 1.0.0
description: Shared report conventions for the review skills (review-repo-code-quality, review-org-health) — where a dated review report goes, the provenance stamp recording which skill version produced it, evidence rules, handling of security-sensitive findings, re-review of a prior report, and confidence/status labels. Not invoked directly; install alongside any skill that references it.
allowed-tools: Read
user-invocable: false
---

# Review conventions

This directory holds one file, [`report-conventions.md`](report-conventions.md),
that the review skills in this collection read instead of each repeating
it. It is packaged as its own skill so that it can be installed, pinned,
and versioned on its own:

```console
apm install con/skills#<commit> --skill review-conventions --skill review-repo-code-quality [--skill review-org-health]
```

A skill that depends on it says so in its `SKILL.md` and reads
`../review-conventions/report-conventions.md` relative to its own
directory. If that file is not installed, the calling skill stops and asks
the user to install `review-conventions`; it does not proceed from memory.

Bump `version:` here when the report layout, the provenance stamp, or the
evidence rules change (see `AGENTS.md`, "Skill versions"); the skills that
read it do not need a bump for that.
