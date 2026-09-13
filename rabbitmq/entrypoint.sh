#!/bin/bash
set -euo pipefail

: "${RABBITMQ_USER:?RABBITMQ_USER is required}"
: "${RABBITMQ_PASSWORD:?RABBITMQ_PASSWORD is required}"

rabbitmq-server -detached

until rabbitmq-diagnostics -q ping >/dev/null 2>&1; do
  sleep 1
done
rabbitmqctl await_startup

if rabbitmqctl list_users --silent | awk '{print $1}' | grep -Fxq "${RABBITMQ_USER}"; then
  rabbitmqctl change_password "${RABBITMQ_USER}" "${RABBITMQ_PASSWORD}"
else
  rabbitmqctl add_user "${RABBITMQ_USER}" "${RABBITMQ_PASSWORD}"
fi
rabbitmqctl set_permissions -p / "${RABBITMQ_USER}" '.*' '.*' '.*'

rabbitmqctl stop

exec rabbitmq-server
