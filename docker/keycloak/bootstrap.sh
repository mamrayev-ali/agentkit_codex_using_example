#!/usr/bin/env bash
set -euo pipefail

KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
REALM="${DECIDER_KEYCLOAK_REALM:-decider-local}"
ADMIN_USER="${DECIDER_KEYCLOAK_ADMIN_USER:?DECIDER_KEYCLOAK_ADMIN_USER is required}"
ADMIN_PASSWORD="${DECIDER_KEYCLOAK_ADMIN_PASSWORD:?DECIDER_KEYCLOAK_ADMIN_PASSWORD is required}"
DEMO_USER_PASSWORD="${DECIDER_KEYCLOAK_DEMO_USER_PASSWORD:?DECIDER_KEYCLOAK_DEMO_USER_PASSWORD is required}"
DEMO_ADMIN_PASSWORD="${DECIDER_KEYCLOAK_DEMO_ADMIN_PASSWORD:?DECIDER_KEYCLOAK_DEMO_ADMIN_PASSWORD is required}"

KCADM="/opt/keycloak/bin/kcadm.sh"

wait_for_admin_login() {
  local attempt=1
  local max_attempts=40
  while (( attempt <= max_attempts )); do
    if "$KCADM" config credentials --server "$KEYCLOAK_URL" --realm master --user "$ADMIN_USER" --password "$ADMIN_PASSWORD" >/dev/null 2>&1; then
      return 0
    fi
    echo "[keycloak-bootstrap] waiting for keycloak admin API (attempt ${attempt}/${max_attempts})"
    sleep 2
    ((attempt++))
  done
  echo "[keycloak-bootstrap] unable to authenticate to Keycloak admin API"
  return 1
}

resolve_user_id() {
  local username="$1"
  "$KCADM" get users -r "$REALM" -q "username=${username}" --fields id --format csv --noquotes | tail -n 1
}

set_user_password() {
  local username="$1"
  local password="$2"
  local user_id
  user_id="$(resolve_user_id "$username")"

  if [[ -z "$user_id" ]]; then
    echo "[keycloak-bootstrap] user not found in realm '${REALM}': ${username}"
    return 1
  fi

  "$KCADM" set-password -r "$REALM" --userid "$user_id" --new-password "$password" >/dev/null
  echo "[keycloak-bootstrap] password updated for user '${username}'"
}

wait_for_admin_login
set_user_password "analyst@acme.decider.local" "$DEMO_USER_PASSWORD"
set_user_password "admin@acme.decider.local" "$DEMO_ADMIN_PASSWORD"

echo "[keycloak-bootstrap] realm '${REALM}' bootstrap completed"
