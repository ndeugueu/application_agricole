#!/bin/bash
set -e

# Script to create multiple PostgreSQL databases
# Usage: set POSTGRES_MULTIPLE_DATABASES environment variable

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE identity_db;
    CREATE DATABASE farm_db;
    CREATE DATABASE inventory_db;
    CREATE DATABASE sales_db;
    CREATE DATABASE accounting_db;
    CREATE DATABASE reporting_db;

    GRANT ALL PRIVILEGES ON DATABASE identity_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE farm_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE inventory_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE sales_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE accounting_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE reporting_db TO $POSTGRES_USER;
EOSQL

echo "Multiple databases created successfully!"
