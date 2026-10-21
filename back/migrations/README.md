# Database migrations and reference data

The initial revision explicitly creates 14 InnoDB tables for MySQL 8.4 with
`utf8mb4` character support. Email is normalized by the application and uses
`utf8mb4_bin` for uniqueness without accent folding. External identity subjects
also use binary collation. The default-address foreign key is added after both
users and addresses exist, and removed first on downgrade.

Use the same `APP_ENV` for migrations, seed commands, workers and the API:

```sh
APP_ENV=development .venv/bin/alembic upgrade head
APP_ENV=development .venv/bin/python -m scripts.seed
```

`test` and `production` select their own `.env.<environment>` configuration.
These commands never run automatically on application startup. Seed is
idempotent: it creates missing predefined roles, permissions and token types,
updates predefined display names, and fills missing predefined role-permission
links. It preserves custom definitions and existing additional permission links.
Removing permissions therefore requires an explicit reviewed data migration.
It never creates users, administrators, demo passwords or delivery data.

To render the DDL without connecting to MySQL:

```sh
APP_ENV=development .venv/bin/alembic upgrade head --sql > /tmp/foodify-schema.sql
```

Existing installations need a separate reviewed migration of their data; this
revision creates a new schema. MySQL DDL is not transactional. Back up existing
data before an upgrade and review generated migrations. `downgrade base` drops
these tables and their contents; it is destructive and is not a data recovery
mechanism.

## Retention

```sh
APP_ENV=production .venv/bin/python -m scripts.cleanup --days-retention 30
APP_ENV=production .venv/bin/python -m scripts.cleanup --days-retention 30 --apply
```

The first command prints candidate counts without deleting rows. The second
deletes sent outbox entries and expired/consumed action tokens, OAuth attempts
and completion tickets only after the retention period. It prunes sessions only
after their expiry or revocation has aged beyond the retention period; their
refresh-token history is removed by the database cascade. Refresh histories for
live sessions are never deleted because reused tokens must remain detectable.
Pending email outbox entries are preserved and require operational review if
delivery continues failing. Choose retention according to operational and data
retention requirements; the default is 30 days. Schedule this explicit command
through the deployment's job runner if recurring cleanup is desired.
