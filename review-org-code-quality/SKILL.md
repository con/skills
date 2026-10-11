---
name: review-org-code-quality
version: 1.0.0
description: Audit code health across an organization-wide ecosystem of similarly styled, interconnected data/ML/ETL pipelines or repositories. Focuses on systemic risk (template drift, contract fragility, cross-repo duplication, blast radius, bus factor) rather than single-repo code smells, and writes a dated report. Use when asked to review, audit, or assess the health of a set of related repositories or pipelines. For one repository use review-repo-code-quality instead.
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, Agent
user-invocable: true
---

# Skill: Organization-wide code quality review

Modelled on
[dandi-cache/dandi-cache-utils `docs/healthstatus-review/2026-09-19.md`](https://github.com/dandi-cache/dandi-cache-utils/blob/main/docs/healthstatus-review/2026-09-19.md)
(example only): a point-in-time picture of an organization of related repositories, where
the findings are about the *system* — what one mistake in a shared layer
reaches, which contracts nobody checks, where the template itself is the
root cause.

## Relationship to `review-repo-code-quality`

This skill builds on the single-repository `review-repo-code-quality` skill
and the shared `code-quality-report-conventions` skill, and expects both installed
alongside (in APM, select all three; in a `con/skills` checkout they are
sibling directories). Two things are delegated rather than repeated here:

- **Per-repository scanning (Phase 2)** runs `review-repo-code-quality` on each
  repository in its **Breadth mode** (defined in that skill: no inputs
  prompt, no per-repo report, no changes, no jscpd; returns
  `{repo}@{short SHA}`, baseline status, and `DC` / `DUP` / `NV`
  findings) and feeds the results into this skill's health matrix.
- **Report conventions** — where the report goes for a multi-repository
  review, the provenance stamp recording which version of the skill
  produced it, evidence rules, security-sensitive findings, re-review of
  a prior report, and confidence/status labels — are defined once in the
  sibling `code-quality-report-conventions` skill
  (`../code-quality-report-conventions/report-conventions.md`). Read it first; it is
  part of this skill's contract. If that file is not installed, stop and
  ask the user to install `code-quality-report-conventions`; do not proceed from
  memory.

## When to use

A set of repositories that (a) follow a common template or style and
(b) are connected via shared data, schemas, libraries, or orchestration.
Works for a handful of pipelines or a few dozen; beyond that, sample the
per-repository scan and say so in Method & limits. For a single
repository, use `review-repo-code-quality` directly.

## Core prompt

```
You are auditing the code health of an ecosystem of connected pipelines, not a single codebase.
Your goal is to find risk that emerges from the *system*: convention drift, fragile contracts
between pipelines, duplicated logic, and single points of failure. Individual code smells matter
only insofar as they are systemic or sit on a critical path.

Inputs you have:
- Repos / monorepo paths / org: {FILL}
- Orchestrator (Airflow / Dagster / dbt / Prefect / GitHub Actions / other): {FILL}
- Shared library or template name + current version: {FILL}
- Lineage or DAG dependency source, if any: {FILL}
- Known incidents or pain points: {FILL}
- Out of scope: {FILL}

Work in the phases below. At each phase, distinguish between what you OBSERVED (with file paths /
line refs), what you INFERRED, and what you could NOT determine. Never fabricate a file reference.
Prefer breadth first, then depth on the highest-risk nodes.
```

## Phase 0 — Establish the reference pattern

Before judging anything, define what "correct" looks like in this ecosystem.

- Locate the canonical template, cookiecutter, or the 2–3 pipelines everyone copies from.
- Extract the **house pattern**: directory layout, config approach, entrypoint shape, logging, retry/error handling, testing layout, how secrets are read, how schemas are declared, how outputs are written.
- Identify the **shared library versions** in play and what the "current" version is.
- Output: a one-page "Reference pattern" section. All drift is measured against this, not against generic best practice.
- Note the template's **own** gaps (no DQ gate, no test scaffold, no `CODEOWNERS`, …): these are why the same issue recurs everywhere, and they are findings in their own right.

## Phase 1 — Map the graph

- Build an inventory: pipeline name, owner/team, orchestrator, last meaningful commit, shared-lib version, upstream inputs, downstream consumers, SLA/criticality if known.
- Derive edges from: orchestrator dependencies, table/topic/bucket reads and writes, import graphs, cross-repo API calls, machine-readable declarations (`cache.toml`, `dbt` sources, …) when they exist — prefer declared edges to guessed ones and say which you used.
- Compute for each node: **fan-in, fan-out, depth**, and whether it's on the path to anything business-critical.
- Flag: orphaned pipelines (no consumers, still running), hub nodes (high fan-out), long chains (depth well above the ecosystem median; state the threshold you used), cycles. Distinguish an orphan from a *product* — a leaf with external consumers is not a candidate for retirement.

## Phase 2 — Per-pipeline scan (breadth)

Run `review-repo-code-quality` in Breadth mode on every repository (use
`Agent` to parallelize when there are many), then score each repository
0–3 per dimension below (0 = absent/broken, 3 = works and is covered by
tests or gates). Breadth mode feeds the **Dead code**, **Testing**
(baseline status), and duplication inputs; the other dimensions are
**scored from configuration and workflows directly** (orchestrator
definitions, schema declarations, CI, IAM/secrets wiring), not from the
repo skill. Record **template conformance separately from correctness**,
so a pipeline that faithfully copies a flawed template is not scored 3 on
everything. Keep the per-repository evidence in an **evidence appendix**
of the report (or a sibling `…-evidence/<repo>.md` per repository when it
is long); each matrix cell links to it.

| Dimension | What to check |
|---|---|
| **Template conformance** | Structure, naming, config, entrypoint match the reference pattern. Note *which* deviations and whether they look intentional. |
| **Contract definition** | Input/output schemas explicitly declared and versioned? Or implicitly "whatever the upstream produced"? |
| **Idempotency & reruns** | Safe to re-run a partition/day? Overwrites vs. appends. Backfill story. |
| **Failure handling** | Retries, dead-lettering, partial-failure behavior, alerting target. Does it fail loud or fail silent? |
| **Data quality gates** | Row-count, null, freshness, schema checks — present, and do they block or just log? |
| **Observability** | Structured logs, metrics, lineage emission, run metadata. Can you tell from outside why a run failed? |
| **Testing** | Unit tests on transforms, contract/fixture tests on I/O, any integration test. Test-to-logic ratio. |
| **Dependency health** | Shared-lib version lag, pinned vs. floating deps, known CVEs, EOL runtimes. |
| **Secrets & access** | Hardcoded credentials, over-broad IAM/service accounts, secrets in logs. |
| **Ownership & docs** | CODEOWNERS / on-call, README accuracy, runbook exists. |
| **Dead code & config** | From the `review-repo-code-quality` DC sweep: unused tasks, stuck feature flags, stale env branches. |
| **Change velocity** | Commit recency, PR review depth, whether it's a "nobody touches it" pipeline. |

## Phase 3 — Cross-cutting analysis (this is where the value is)

Look across the matrix for **systemic** issues:

1. **Drift clusters.** Which pipelines have diverged from the template, in what direction, and did divergences propagate by copy-paste? Group by "generation" — pipelines forked from the same ancestor often share the same bug.
2. **Contract fragility.** For every edge in the graph: is the schema enforced on both sides, one side, or neither? Rank edges by (criticality × lack of enforcement).
3. **Copy-paste logic across repos.** Fold the `DUP` findings from Phase 2 and, where available, one `analyze-duplicates` run over all repositories with `--cross-project` (from a scratch directory, `--output <scratch>/jscpd.md`, so nothing is written into the reviewed repos) into clusters. Each duplicate is a place a fix won't land; the recommendation is a shared-library helper plus a migration, not N tickets.
4. **Shared library blast radius.** What breaks if the shared lib ships a breaking change? Which pipelines are N versions behind and why? Does the shared layer itself have CI?
5. **Failure propagation.** Trace a failure from a hub node downstream: does it cascade, stall, or silently produce stale data? Where are the circuit breakers?
6. **Convention gaps.** Things the template *doesn't* specify that everyone solved differently (e.g. timezone handling, null semantics, late-arriving data, what a `limit` parameter means).
7. **Bus factor.** Overlay ownership on the graph: critical paths owned by one person or an orphaned team.

## Phase 4 — Prioritize and report

Score each finding: **Impact** (blast radius via graph) × **Likelihood** (evidence of recurrence, test coverage, change frequency), then rank by that score relative to **Effort to fix**. Separate into:

- **Fix now** — critical path + silent failure mode + no test.
- **Fix systemically** — push into the template/shared lib so it lands everywhere.
- **Accept & document** — intentional divergence, low criticality.
- **Retire** — orphaned pipelines, dead DAG branches.

## Where to write the report

Follow `report-conventions.md` §2 with `{reviews dir}` = `code-reviews`
and `{kind}` = `org-code-quality-review`. A multi-repository review has no single
natural home, so ask the user where it goes — the organization's utility
or template repository is the usual answer — and record the choice in
"Method & limits". The provenance stamp (§1) cites this skill's `name:`
and `version:` frontmatter and the `con/skills` commit it was installed
from.

## Output template

```markdown
# Organization code quality review — {org/domain} — {YYYY-MM-DD}

Reviewed at: {repo}@{short SHA}[, ...]
Generated by: con/skills `review-org-code-quality` v{version} ({skill source}); conventions v{version}; using `review-repo-code-quality` v{version}
Previous review: {link to prior report, or "none"}

{One paragraph: what was reviewed — N repositories plus the template and shared
layers — and the headline in two sentences.}

## Summary
Top 3 systemic risks in order, top 3 quick wins, what was out of scope.

## Since last review
Fixed / still open / new vs. the previous report, re-verified at the current SHA (omit if first review).

## Reference pattern
What "good" looks like here (a table of concern → house pattern), and the template's own gaps.

## Ecosystem map
Graph or table: nodes, edges, criticality, owners. Call out hubs, orphans, products, long chains.

## Health matrix
Repositories × dimensions, scored 0–3, with column means. Link each cell to the
evidence appendix. Say in one sentence what the shape of the matrix means.

## Findings
One section per cross-cutting issue: evidence (quoted, cited), affected repositories,
blast radius, whether it has ever fired, recommended fix and whether it belongs in the
template / shared lib.

## Per-repository notes
Only notable deviations; don't repeat the matrix.

## Prioritized action plan
Fix now / Fix systemically / Accept / Retire — each with owner suggestion and effort estimate.

## Method & limits
What was scanned, what was sampled, what was verified empirically vs. inferred,
confidence level, where this report lives for the next run.

## Evidence appendix
Per repository: the Breadth-mode findings (locations, baseline status) and the
config/workflow facts each matrix cell was scored from.
```

## Operating rules

- Follow `../code-quality-report-conventions/report-conventions.md` for
  evidence, location, provenance, security-sensitive findings, and
  re-review. For the **Secrets & access** and **Dependency health**
  dimensions, the matrix and the evidence appendix cite `file:line` only
  and link to the private location (§2) that holds the detail; the
  report often lands in a utility repository that may be public.
- **Judge against the house pattern first, generic best practice second.** "Doesn't use X framework" isn't a finding if the template doesn't either — but "the template lacks any DQ gate" is.
- **Prefer fixes that land in one place.** If the same issue appears in 5+ pipelines, the recommendation is a template/shared-lib change plus a migration, not 5 tickets.
- **Distinguish intentional from accidental divergence.** Ask, or check commit messages/ADRs, before flagging.
- **Say whether a risk has ever fired.** "Never triggered; fully armed" is a different finding from "has bitten twice". Check run history where it exists.
- **Don't audit the data itself** unless asked — this is code health. Note where data-quality tooling is missing; don't run it.

## Suggested mechanical helpers

- **Dependency/version matrix:** parse every `requirements*.txt` / `pyproject.toml` / `package.json` and pivot by shared-lib version.
- **Drift diff:** `diff -r` each pipeline against the template, filtered to structural files.
- **Edge extraction:** grep for table/topic/bucket identifiers in read/write calls; join with orchestrator DAG definitions.
- **Staleness:** `git log -1 --format=%cd` per repo, plus PR count in last 90 days.

## Tailoring notes

- If you already have a lineage tool (OpenLineage, Marquez, dbt docs, Dagster asset graph), feed it in at Phase 1 and skip edge extraction.
- If the ecosystem is a monorepo, run Breadth mode once per package (same checkout, different scope) and spend the saved time on Phase 3.
- The 0–3 scoring is deliberately coarse; finer scales invite arguments about 6 vs. 7 rather than action.
