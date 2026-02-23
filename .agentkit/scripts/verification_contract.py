#!/usr/bin/env python3
"""Shared verification contract checks for AgentKit repositories.

This script provides:
- profile detection (scaffold-only / backend-present / frontend-present / backend+frontend)
- placeholder-ban checks
- DOC-gate checks (PROJECT_MAP must change with any repo change)
- scaffold contract checks used by make verify targets
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_MAP = Path(".agentkit/docs/PROJECT_MAP.md")

FORBIDDEN_PLACEHOLDER_FILES = (
    Path(".agentkit/scripts/verify_contract.py"),
    Path("services/api/scripts/placeholder_checks.py"),
    Path("frontend/scripts/placeholder-task.cjs"),
)

BACKEND_MARKERS = (
    Path("services/api/pyproject.toml"),
    Path("services/backend/pyproject.toml"),
    Path("backend/pyproject.toml"),
)

FRONTEND_MARKERS = (
    Path("frontend/package.json"),
    Path("web/package.json"),
    Path("ui/package.json"),
)

REQUIRED_SCAFFOLD_FILES = (
    Path("AGENTS.md"),
    Path("Makefile"),
    Path(".agentkit/docs/ROADMAP.md"),
    Path(".agentkit/docs/PROJECT_MAP.md"),
    Path(".agentkit/scripts/verify.sh"),
    Path(".agentkit/scripts/verify.ps1"),
)


def _print(msg: str) -> None:
    print(msg, flush=True)


def _run_git(args: list[str]) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(ROOT_DIR), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git command failed")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def detect_profile() -> str:
    has_backend = any((ROOT_DIR / marker).exists() for marker in BACKEND_MARKERS)
    has_frontend = any((ROOT_DIR / marker).exists() for marker in FRONTEND_MARKERS)
    if has_backend and has_frontend:
        return "backend+frontend"
    if has_backend:
        return "backend-present"
    if has_frontend:
        return "frontend-present"
    return "scaffold-only"


def check_placeholder_ban() -> int:
    violations: list[str] = []
    for rel_path in FORBIDDEN_PLACEHOLDER_FILES:
        if (ROOT_DIR / rel_path).exists():
            violations.append(str(rel_path).replace("\\", "/"))

    makefile = ROOT_DIR / "Makefile"
    if makefile.exists():
        text = makefile.read_text(encoding="utf-8")
        forbidden_markers = (
            "ERROR: verify-local is not implemented for this repo yet.",
            "ERROR: verify-smoke is not implemented for this repo yet.",
            "ERROR: verify-ci is not implemented for this repo yet.",
        )
        for marker in forbidden_markers:
            if marker in text:
                violations.append("Makefile contains placeholder verification marker")
                break

    if violations:
        _print("ERROR: placeholder-ban failed. Remove forbidden placeholder artifacts:")
        for violation in violations:
            _print(f"  - {violation}")
        return 1

    _print("OK: placeholder-ban passed.")
    return 0


def _collect_changed_files() -> set[str]:
    changed: set[str] = set()
    changed.update(_run_git(["diff", "--name-only"]))
    changed.update(_run_git(["diff", "--cached", "--name-only"]))
    changed.update(_run_git(["ls-files", "--others", "--exclude-standard"]))
    return {path.replace("\\", "/") for path in changed}


def check_doc_gate() -> int:
    project_map = str(PROJECT_MAP).replace("\\", "/")
    changed = _collect_changed_files()

    if not changed:
        _print("OK: DOC-gate passed (no changes detected).")
        return 0

    non_doc_changes = sorted(path for path in changed if path != project_map)
    if not non_doc_changes:
        _print("OK: DOC-gate passed (only PROJECT_MAP changed).")
        return 0

    if project_map not in changed:
        _print("ERROR: DOC-gate failed. PROJECT_MAP.md was not updated.")
        _print("Changed files excluding PROJECT_MAP:")
        for path in non_doc_changes:
            _print(f"  - {path}")
        return 1

    _print("OK: DOC-gate passed (PROJECT_MAP updated with other changes).")
    return 0


def check_scaffold_contract() -> int:
    missing = [
        str(path).replace("\\", "/")
        for path in REQUIRED_SCAFFOLD_FILES
        if not (ROOT_DIR / path).exists()
    ]
    if missing:
        _print("ERROR: scaffold contract check failed. Missing required files:")
        for rel in missing:
            _print(f"  - {rel}")
        return 1

    makefile = ROOT_DIR / "Makefile"
    required_targets = ("detect:", "verify-smoke:", "verify-local:", "verify-ci:")
    makefile_text = makefile.read_text(encoding="utf-8")
    missing_targets = [target for target in required_targets if target not in makefile_text]
    if missing_targets:
        _print("ERROR: Makefile is missing required verification targets:")
        for target in missing_targets:
            _print(f"  - {target}")
        return 1

    _print("OK: scaffold contract check passed.")
    return 0


def verify_mode(mode: str) -> int:
    profile = detect_profile()
    _print(f"Detected verification profile: {profile}")
    _print(f"Verification mode: {mode}")

    checks = (check_doc_gate, check_placeholder_ban, check_scaffold_contract)
    for check_fn in checks:
        rc = check_fn()
        if rc != 0:
            return rc
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AgentKit verification contract helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("detect", help="Print detected repository verification profile.")
    subparsers.add_parser("doc-gate", help="Run DOC-gate check.")
    subparsers.add_parser("placeholder-ban", help="Run placeholder-ban check.")
    subparsers.add_parser("scaffold-contract", help="Run scaffold contract checks.")

    verify = subparsers.add_parser("verify", help="Run shared verification preflight checks.")
    verify.add_argument(
        "--mode",
        choices=("smoke", "local", "ci"),
        required=True,
        help="Verification mode for reporting.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "detect":
            _print(detect_profile())
            return 0
        if args.command == "doc-gate":
            return check_doc_gate()
        if args.command == "placeholder-ban":
            return check_placeholder_ban()
        if args.command == "scaffold-contract":
            return check_scaffold_contract()
        if args.command == "verify":
            return verify_mode(args.mode)
    except RuntimeError as err:
        _print(f"ERROR: {err}")
        return 1

    _print(f"ERROR: unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
