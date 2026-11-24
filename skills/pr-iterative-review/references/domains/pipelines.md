# Lens: pipelines

Data, ETL and machine-learning pipelines, and the workflow definitions and
schedules that run them: code whose output other stages, repositories or
people consume later.

## Recognize

Workflow definitions (`Snakefile`, `*.smk`, `*.nf`, Airflow DAGs, Prefect or
Dagster flows, Luigi tasks, CWL or WDL files, Makefiles that produce data);
dbt models and their YAML; scheduled jobs (cron entries, scheduled
workflows); extraction, transformation and loading scripts; record schemas
(JSON Schema, Avro, Parquet schemas, pydantic or dataclass models of
records); data validation suites; ML training and evaluation configuration
(Hydra, YAML experiment files); DVC files and DataLad `run` records.

## Context to read

The stages and what consumes each output: later stages, other repositories,
dashboards, published datasets. The schedule, the data volumes, how a
failed run is resumed and a backfill is done, where outputs are stored and
how they are versioned; for an organization of similar pipelines, the
pattern the others follow.

## Checks

**Contracts between stages** (blocking when a consumer breaks)
- A changed output schema, column, file name, path layout, partitioning or
  encoding: find who reads it, here and in sibling repositories. Is the
  schema versioned? Are existing outputs migrated, or can readers still read
  them?
- Retiring a column, field, path or configuration key goes through the
  brief's Deprecation steps: the new one is written beside the old, readers
  accept both, a renamed configuration key is still read and warns, and the
  old one goes only after its consumers have moved. A schema that carries a
  version gets a new one for an incompatible change.

**Re-runs and failure** (usually blocking)
- Running a stage twice gives the same result: no duplicated rows, no
  appended copies.
- A crash leaves no half-written output that a later stage would accept:
  write to a temporary name, then rename.
- Incremental processing: watermarks or state advance only after success;
  late-arriving and out-of-order data are handled; a run can resume.

**Validation** (should-fix)
- Inputs are checked where they enter (schema, missing values, ranges,
  duplicate keys); bad records fail loudly or are counted and logged, not
  dropped in silence; row counts in and out are logged.

**Time** (usually should-fix; blocking when it shifts data)
- Naive versus time-zone-aware datetimes, daylight-saving changes, date
  boundaries in partitioning, and assumptions about sort order.

**Scale and cost** (should-fix)
- Memory with real volumes rather than the sample in the tests; streaming
  or chunking; API rate limits, pagination and retries with backoff during
  extraction; cloud egress and storage cost.

**Provenance** (should-fix)
- Outputs record their inputs, code version and parameters; random seeds
  are fixed and recorded; scheduled jobs run in a pinned environment.

**Operations** (should-fix)
- Overlapping runs (a lock, or a schedule longer than the run); failure
  alerts; a backfill plan when changed logic affects outputs already
  published.

**Machine learning** (blocking for leakage)
- Information leaking from test to training data; evaluation on the wrong
  split; metrics computed differently from before without saying so; model
  artifacts without a version.

**Tests** (should-fix)
- Fixtures with the quirks of real data, empty input, and malformed
  records.

## Not findings

- The choice of orchestrator or storage format.

## Verification

- **static**: search for every reader of a changed output (paths,
  column names, schema names); read the workflow definition to trace inputs
  to outputs.
- **CI only**: dry runs (`snakemake -n`, `dbt compile`, `nextflow run
  -preview`) evaluate the project's code; running a stage on sample data.
