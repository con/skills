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
the frontend, scripts, downstream packages). For a library, the language
guide you were given (`<language>-practices`) says how the
language marks internals, and so what is public.

## Checks

**Contracts** (blocking when it breaks callers without a path forward)
- A changed request or response shape, status code, error format, default
  value, command-line flag, exit code or function signature. Search for
  every caller, and check that the docs, schema and changelog say so.

**Deprecation** (tiers as in the brief's Deprecation section)
- Retiring any of those goes through the brief's steps, in the form the
  interface offers:
  - Library APIs: the old name, argument or default keeps working beside
    the new one, marked the language's way: in Python, PEP 702's
    `@deprecated` (`warnings.deprecated` from Python 3.13,
    `typing_extensions.deprecated` before) or `warnings.warn(…,
    DeprecationWarning, stacklevel=2)`, with `FutureWarning` where end
    users rather than developers should see it; a `Deprecated:`
    paragraph in a Go doc comment; `#[deprecated(since, note)]` in Rust;
    a `@deprecated` JSDoc tag in TypeScript; a `DEPRECATED` pragma in
    Haskell. The language guide's Verification section names the tool
    that lists breaking API changes (`griffe check`, `gorelease` or
    `apidiff`, `cargo semver-checks`, a declaration diff); it is not
    **static**, so only CI's run of it counts here.
  - Command-line tools: an old flag stays as an alias that warns on stderr
    and leaves the exit status alone.
  - Web APIs: `deprecated: true` in OpenAPI, `@deprecated(reason: …)` in
    GraphQL, `[deprecated = true]` in Protocol Buffers (a removed field's
    number and name then `reserved`); the `Deprecation` and `Sunset`
    response headers (RFC 9745, RFC 8594) announce the dates. Removal
    waits for a new API version.

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
  the migration file itself; the language guides' **static** tools on the
  changed files.
- **CI only**: the project's tests; printing a migration's SQL (`manage.py
  sqlmigrate`, `alembic upgrade --sql`) runs project code; starting the
  service.
