---
name: code-quality-report-conventions
version: 0.1.0
description: Shared report conventions for the review skills (review-repo-code-quality, review-org-code-quality) — where a dated review report goes, the provenance stamp recording which skill version produced it, evidence rules, handling of security-sensitive findings, re-review of a prior report, and confidence/status labels. Not invoked directly. Use when a review skill (review-repo-code-quality, review-org-code-quality) tells you to read it, or when asked what format those reports follow.
allowed-tools: Read
user-invocable: false
---

# Code quality report conventions

This skill's payload is [`report-conventions.md`](report-conventions.md),
that the review skills in this collection read instead of each repeating
it. It is packaged as its own skill so that it can be installed, pinned,
and versioned on its own:

```console
apm install con/skills#<commit> --skill code-quality-report-conventions --skill review-repo-code-quality [--skill review-org-code-quality]
```

A skill that depends on it says so in its `SKILL.md` and reads
`../code-quality-report-conventions/report-conventions.md` relative to its own
directory. If that file is not installed, the calling skill stops and asks
the user to install `code-quality-report-conventions`; it does not proceed from memory.

Bump `version:` here when the report layout, the provenance stamp, or the
evidence rules change (see `AGENTS.md`, "Skill versions"); the skills that
read it do not need a bump for that.
