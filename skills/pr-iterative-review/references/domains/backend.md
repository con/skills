# Lens: backend

Services, web APIs, command-line tools and the public interfaces of
libraries: the code other programs and people call.

## Recognize

Request handlers, routes, views and controllers; `api/`, `server/`,
`services/`, `handlers/`; ORM models and migrations (`migrations/`,
`alembic/`, `*.sql`); API schemas (OpenAPI, GraphQL, protobuf); command-line
entry points (`cli.py`, `__main__.py`, `cmd/`, `console_scripts` and `bin`
entries); a library's public modules (what `__init__.py`, `index.ts` or the
package's exports expose); background jobs and queues.

## Context to read

The compatibility promise: semantic versioning, a deprecation policy, a
changelog, API documentation. The authentication and authorization model;
the database and migration tooling and how the project deploys (rolling
deploys mean old and new code run against one schema); the error-handling
and logging conventions; who calls the changed interface (other services,
the frontend, scripts, downstream packages).

## Checks

**Contracts** (blocking when it breaks callers without a path forward)
- A changed request or response shape, status code, error format, default
  value, command-line flag, exit code or function signature. Search for
  every caller, and check that the docs, schema and changelog say so and a
  deprecation path exists where the project promises one.

**Input and trust boundaries** (usually blocking)
- External input checked for type, size and range before use.
- Paths: `os.path.join(base, user_value)` returns `user_value` when it is
  absolute, and `..` escapes `base`; resolve the path and check it stays
  under `base`.
- Fetching a URL the caller supplies (server-side request forgery).

**Authorization** (blocking)
- New endpoints and commands require authentication where their neighbours
  do, and check that the caller may act on the specific object (not only
  that they are logged in).

**Data and migrations** (usually blocking)
- Migrations: reversible or documented as one-way; safe on large tables
  (index builds without locking writes, such as `CREATE INDEX
  CONCURRENTLY` on PostgreSQL; backfills in batches); compatible with the
  previous release running during a rolling deploy (add, then migrate, then
  remove, across releases).
- Writes that must succeed or fail together run in one transaction; an
  operation that may be retried is idempotent.

**Resources and concurrency** (should-fix; blocking on a hot path)
- Outbound calls without a timeout (`requests` has none by default);
  unbounded queries without pagination; one query per row where one query
  would do.

**Errors and configuration** (should-fix)
- Status codes and error bodies follow the API's conventions; new settings
  are documented with their defaults and read secrets from the environment
  or a secret store; feature flags have a removal plan.

## Not findings

- Missing caching with no measurement.
- Internal helpers whose signature changed together with every caller.

## Verification

- **static**: search for every caller of a changed function,
  endpoint, flag or setting, in tests, scripts, docs and configuration; read
  the migration file itself.
- **consent**: the project's tests; printing a migration's SQL (`manage.py
  sqlmigrate`, `alembic upgrade --sql`) runs project code; starting the
  service.
