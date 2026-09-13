#!/bin/bash
set -euo pipefail

: "${INVENTORY_DB_USER:?INVENTORY_DB_USER is required}"
: "${INVENTORY_DB_PASSWORD:?INVENTORY_DB_PASSWORD is required}"
: "${INVENTORY_DB_NAME:?INVENTORY_DB_NAME is required}"

pg_ctlcluster 15 main start

until runuser -u postgres -- pg_isready -q; do
  sleep 1
done

if runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${INVENTORY_DB_USER}'" | grep -q 1; then
  runuser -u postgres -- psql -c "ALTER ROLE ${INVENTORY_DB_USER} WITH LOGIN PASSWORD '${INVENTORY_DB_PASSWORD}'"
else
  runuser -u postgres -- psql -c "CREATE ROLE ${INVENTORY_DB_USER} WITH LOGIN PASSWORD '${INVENTORY_DB_PASSWORD}'"
fi

if ! runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_database WHERE datname='${INVENTORY_DB_NAME}'" | grep -q 1; then
  runuser -u postgres -- createdb --owner="${INVENTORY_DB_USER}" "${INVENTORY_DB_NAME}"
fi

pg_ctlcluster 15 main stop

exec pg_ctlcluster 15 main start --foreground
