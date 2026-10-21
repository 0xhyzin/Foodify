#!/bin/sh
set -eu

# Render generates base64 secrets. Validate before using the SQL string literal.
case "${MYSQL_MIGRATION_PASSWORD:-}" in
  ''|*[!A-Za-z0-9+/=_-]*) echo 'A generated migration password is required.' >&2; exit 1 ;;
esac

# Root remains local to MySQL. FastAPI never receives this password.
MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --protocol=socket --user=root <<SQL
CREATE USER 'foodify_migrator'@'%' IDENTIFIED BY '${MYSQL_MIGRATION_PASSWORD}';
GRANT ALL PRIVILEGES ON foodify.* TO 'foodify_migrator'@'%';
REVOKE ALL PRIVILEGES ON foodify.* FROM 'foodify'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON foodify.* TO 'foodify'@'%';
SQL
