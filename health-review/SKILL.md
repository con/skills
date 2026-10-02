---
name: health-review
description: Audit code health across an org-wide ecosystem of similarly styled, interconnected data/ML/ETL pipelines. Focuses on systemic risk (drift, contract fragility, duplication, blast radius) rather than single-repo code smells. Use when asked to review, audit or assess the health of a set of related pipelines.
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, Agent
user-invocable: true
---

# Skill: Pipeline Ecosystem Health Audit

## When to use
Auditing a set of related data/ML/ETL pipelines that (a) follow a common template or style, and (b) are connected via shared data, schemas, libraries, or orchestration. Works for 5 pipelines or 150.

## Core prompt

```
You are auditing the code health of an ecosystem of connected pipelines, not a single codebase.
Your goal is to find risk that emerges from the *system*: convention drift, fragile contracts
between pipelines, duplicated logic, and single points of failure. Individual code smells matter
only insofar as they are systemic or sit on a critical path.

Inputs you have:
- Repos / monorepo paths / org: {FILL}
- Orchestrator (Airflow / Dagster / dbt / Prefect / other): {FILL}
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
- Output: a one-page "Reference Pattern" doc. All drift is measured against this, not against generic best practice.

## Phase 1 — Map the graph
- Build an inventory: pipeline name, owner/team, orchestrator, last meaningful commit, shared-lib version, upstream inputs, downstream consumers, SLA/criticality if known.
- Derive edges from: orchestrator dependencies, table/topic/bucket reads and writes, import graphs, cross-repo API calls.
- Compute for each node: **fan-in, fan-out, depth**, and whether it's on the path to anything business-critical.
- Flag: orphaned pipelines (no consumers, still running), hub nodes (high fan-out), long chains (depth well above the ecosystem median; state the threshold you used), cycles.

## Phase 2 — Per-pipeline scan (breadth)
Run the same checklist on every pipeline and record results in a matrix. Score each dimension 0–3 (0 = absent/broken, 3 = works and is covered by tests or gates). Record template conformance separately from correctness, so a pipeline that faithfully copies a flawed template is not scored 3 on everything.

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
| **Dead code & config** | Unused DAG tasks, feature flags stuck on, commented-out blocks, stale env-specific branches. |
| **Change velocity** | Commit recency, PR review depth, whether it's a "nobody touches it" pipeline. |

## Phase 3 — Cross-cutting analysis (this is where the value is)
Look across the matrix for **systemic** issues:

1. **Drift clusters.** Which pipelines have diverged from the template, in what direction, and did divergences propagate by copy-paste? Group by "generation" — pipelines forked from the same ancestor often share the same bug.
2. **Contract fragility.** For every edge in the graph: is the schema enforced on both sides, one side, or neither? Rank edges by (criticality × lack of enforcement).
3. **Copy-paste logic.** Find near-duplicate functions across repos (date parsing, dedup, partition logic, client wrappers). Each duplicate is a place a fix won't land.
4. **Shared library blast radius.** What breaks if the shared lib ships a breaking change? Which pipelines are N versions behind and why?
5. **Failure propagation.** Trace a failure from a hub node downstream: does it cascade, stall, or silently produce stale data? Where are the circuit breakers?
6. **Convention gaps.** Things the template *doesn't* specify that everyone solved differently (e.g. timezone handling, null semantics, late-arriving data).
7. **Bus factor.** Overlay ownership on the graph: critical paths owned by one person or an orphaned team.

## Phase 4 — Prioritize and report
Score each finding: **Impact** (blast radius via graph) × **Likelihood** (evidence of recurrence, test coverage, change frequency), then rank by that score relative to **Effort to fix**. Separate into:

- **Fix now** — critical path + silent failure mode + no test.
- **Fix systemically** — push into the template/shared lib so it lands everywhere.
- **Accept & document** — intentional divergence, low criticality.
- **Retire** — orphaned pipelines, dead DAG branches.

## Where to write the report

Write the report to a file, not just to chat: `docs/health-reviews/YYYY-MM-DD-health-review.md`
(`date +%F`), or a path the user gives. Never overwrite an existing report (use `-2`, `-3`, …
before `.md`). For a multi-repo audit, ask where if unclear, and never place findings in a
public repo without asking. If an earlier report exists there, read it once Phase 0 has
established the reference pattern, re-verify each of its findings against the current code
(a prior report alone can't show something is fixed), and fill in "Since last review".
Record the commit SHA(s) reviewed so cited lines stay meaningful. Do not commit or push
unless asked; tell the user the path.

## Output template

```markdown
# Pipeline Ecosystem Health Audit — {org/domain} — {YYYY-MM-DD}

Reviewed at: {repo}@{short SHA}[, ...]
Previous review: {link to prior report, or "none"}

## 1. Executive summary (≤ 10 lines)
Overall health grade, top 3 systemic risks, top 3 quick wins, what was out of scope.

## 1b. Since last review
Fixed / still open / new vs. the previous report, re-verified at the current SHA (omit if first review).

## 2. Reference pattern
What "good" looks like here, and its known gaps.

## 3. Ecosystem map
Graph or table: nodes, edges, criticality, owners. Call out hubs, orphans, long chains.

## 4. Health matrix
Pipelines × dimensions, scored 0–3, with color/heat. Link each cell to evidence.

## 5. Systemic findings
One section per cross-cutting issue: evidence, affected pipelines, blast radius,
recommended fix (and whether it belongs in the template/shared lib).

## 6. Per-pipeline notes
Only notable deviations; don't repeat the matrix.

## 7. Prioritized action plan
Fix now / Fix systemically / Accept / Retire — each with owner suggestion and effort estimate.

## 8. Method & limits
What was scanned, what was sampled, what couldn't be verified, confidence level.
```

## Operating rules
- **Evidence or it didn't happen.** Every finding cites paths, line ranges, or run IDs. Mark inferences as inferences.
- **Sample honestly.** If you deep-read 12 of 80 pipelines, say which and why. Use automated scans (grep, AST, dep manifests) for the rest.
- **Judge against the house pattern first, generic best practice second.** "Doesn't use X framework" isn't a finding if the template doesn't either — but "the template lacks any DQ gate" is.
- **Prefer fixes that land in one place.** If the same issue appears in 5+ pipelines, the recommendation is a template/shared-lib change plus a migration, not 5 tickets.
- **Distinguish intentional from accidental divergence.** Ask, or check commit messages/ADRs, before flagging.
- **Don't audit the data itself** unless asked — this is code health. Note where data-quality tooling is missing; don't run it.

## Suggested mechanical helpers
- **Dependency/version matrix:** parse every `requirements*.txt` / `pyproject.toml` / `package.json` and pivot by shared-lib version.
- **Drift diff:** `diff -r` each pipeline against the template, filtered to structural files.
- **Duplicate detection:** run the `analyze-duplicates` skill (jscpd-based) over the repos and fold the clusters into Phase 3 item 3.
- **Edge extraction:** grep for table/topic/bucket identifiers in read/write calls; join with orchestrator DAG definitions.
- **Staleness:** `git log -1 --format=%cd` per repo, plus PR count in last 90 days.

## Tailoring notes
- If you already have a lineage tool (OpenLineage, Marquez, dbt docs, Dagster asset graph), feed it in at Phase 1 and skip edge extraction.
- If the ecosystem is a monorepo, collapse Phase 2 into a single script run and spend the saved time on Phase 3.
- The 0–3 scoring is deliberately coarse; finer scales invite arguments about 6 vs. 7 rather than action.
