#!/usr/bin/env bash
set -euo pipefail

# AgentKit verify.sh
# - Enforces DOC-gate: PROJECT_MAP.md must be updated on every ticket that changes repo files.
# - Runs Makefile contract targets (detect / verify-local / verify-smoke / verify-ci).
#
# Usage:
#   ./.agentkit/scripts/verify.sh detect
#   ./.agentkit/scripts/verify.sh local
#   ./.agentkit/scripts/verify.sh ci
#   ./.agentkit/scripts/verify.sh smoke

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_MAP="$ROOT_DIR/.agentkit/docs/PROJECT_MAP.md"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

require_git_repo() {
  git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || die "Not a git repository (expected at $ROOT_DIR)."
}

require_project_map_exists() {
  [[ -f "$PROJECT_MAP" ]] || die "Missing PROJECT_MAP.md at: $PROJECT_MAP"
}

enforce_doc_gate() {
  local status
  status="$(git -C "$ROOT_DIR" status --porcelain)"

  # No changes at all -> nothing to enforce.
  if [[ -z "$status" ]]; then
    echo "OK: DOC-gate: no changes detected."
    return 0
  fi

  # Identify changes excluding PROJECT_MAP.
  local non_doc_changes
  non_doc_changes="$(echo "$status" | awk '{print $2}' | grep -vE '^\.agentkit/docs/PROJECT_MAP\.md$' || true)"

  # If only PROJECT_MAP changed, that is valid.
  if [[ -z "$non_doc_changes" ]]; then
    echo "OK: DOC-gate: only PROJECT_MAP.md changed."
    return 0
  fi

  # If other files changed, PROJECT_MAP must also be changed.
  local project_map_changed
  project_map_changed="$(echo "$status" | awk '{print $2}' | grep -E '^\.agentkit/docs/PROJECT_MAP\.md$' || true)"

  if [[ -z "$project_map_changed" ]]; then
    echo "ERROR: DOC-gate failed."
    echo ""
    echo "You changed repository files but did NOT update:"
    echo "  .agentkit/docs/PROJECT_MAP.md"
    echo ""
    echo "Changed files (excluding PROJECT_MAP):"
    echo "$non_doc_changes" | sed 's/^/  - /'
    echo ""
    die "Update PROJECT_MAP.md and rerun verification."
  fi

  echo "OK: DOC-gate: PROJECT_MAP.md updated alongside code changes."
}

run_make_target() {
  local target="$1"
  echo ""
  echo "==> Running: make $target"
  echo ""
  make -C "$ROOT_DIR" "$target"
}

usage() {
  cat <<EOF
Usage:
  ./.agentkit/scripts/verify.sh <mode>

Modes:
  detect  -> make detect
  local   -> make verify-local
  smoke   -> make verify-smoke
  ci      -> make verify-ci
EOF
  exit 2
}

main() {
  require_git_repo
  require_project_map_exists

  local mode="${1:-}"
  [[ -n "$mode" ]] || usage

  case "$mode" in
    detect)
      run_make_target "detect"
      ;;
    local)
      enforce_doc_gate
      run_make_target "verify-local"
      ;;
    smoke)
      enforce_doc_gate
      run_make_target "verify-smoke"
      ;;
    ci)
      enforce_doc_gate
      run_make_target "verify-ci"
      ;;
    *)
      usage
      ;;
  esac

  echo ""
  echo "OK: Verification complete: $mode"
}

main "$@"
