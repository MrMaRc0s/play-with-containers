#!/bin/bash
set -euo pipefail

: "${BILLING_DB_USER:?BILLING_DB_USER is required}"
: "${BILLING_DB_PASSWORD:?BILLING_DB_PASSWORD is required}"
: "${BILLING_DB_NAME:?BILLING_DB_NAME is required}"

pg_ctlcluster 15 main start

until runuser -u postgres -- pg_isready -q; do
  sleep 1
done

if runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${BILLING_DB_USER}'" | grep -q 1; then
  runuser -u postgres -- psql -c "ALTER ROLE ${BILLING_DB_USER} WITH LOGIN PASSWORD '${BILLING_DB_PASSWORD}'"
else
  runuser -u postgres -- psql -c "CREATE ROLE ${BILLING_DB_USER} WITH LOGIN PASSWORD '${BILLING_DB_PASSWORD}'"
fi

if ! runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_database WHERE datname='${BILLING_DB_NAME}'" | grep -q 1; then
  runuser -u postgres -- createdb --owner="${BILLING_DB_USER}" "${BILLING_DB_NAME}"
fi

pg_ctlcluster 15 main stop

exec pg_ctlcluster 15 main start --foreground
