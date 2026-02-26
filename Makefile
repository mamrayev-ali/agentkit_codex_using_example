# Makefile (AgentKit verification contract)
#
# This Makefile defines stable verification entrypoints:
# - make detect
# - make verify-smoke
# - make verify-local
# - make verify-ci
# - make verify-api-e2e
# - make verify-ui-e2e
#
# Behavior is profile-aware:
# - scaffold-only: DOC-gate + placeholder-ban + detect + scaffold contract checks
# - backend-present: scaffold checks + backend toolchain checks
# - frontend-present: scaffold checks + frontend toolchain checks
# - backend+frontend: scaffold checks + backend + frontend toolchain checks

CONTRACT_SCRIPT := .agentkit/scripts/verification_contract.py

BACKEND_MARKERS := services/api/pyproject.toml services/backend/pyproject.toml backend/pyproject.toml
FRONTEND_MARKERS := frontend/package.json web/package.json ui/package.json

BACKEND_MARKER_HIT := $(firstword $(wildcard $(BACKEND_MARKERS)))
FRONTEND_MARKER_HIT := $(firstword $(wildcard $(FRONTEND_MARKERS)))

HAS_BACKEND := $(if $(BACKEND_MARKER_HIT),1,0)
HAS_FRONTEND := $(if $(FRONTEND_MARKER_HIT),1,0)

PROFILE := scaffold-only
ifeq ($(HAS_BACKEND)$(HAS_FRONTEND),10)
PROFILE := backend-present
endif
ifeq ($(HAS_BACKEND)$(HAS_FRONTEND),01)
PROFILE := frontend-present
endif
ifeq ($(HAS_BACKEND)$(HAS_FRONTEND),11)
PROFILE := backend+frontend
endif

# Future tickets can adjust these commands when backend/frontend are introduced.
BACKEND_SMOKE_CMD ?= uv run --directory services/api pytest -q -m smoke
BACKEND_LOCAL_CMD ?= uv run --directory services/api pytest -q
BACKEND_CI_CMD ?= uv run --directory services/api pytest -q --maxfail=1 --disable-warnings
BACKEND_API_E2E_CMD ?= uv run --directory services/api pytest -q -m e2e_api

FRONTEND_SMOKE_CMD ?= pnpm --dir frontend test -- --run
FRONTEND_LOCAL_CMD ?= pnpm --dir frontend lint && pnpm --dir frontend test -- --run
FRONTEND_CI_CMD ?= pnpm --dir frontend lint && pnpm --dir frontend test -- --run && pnpm --dir frontend build
FRONTEND_UI_E2E_INSTALL_CMD ?= pnpm --dir frontend dlx @playwright/test@1.52.0 install chromium
FRONTEND_UI_E2E_TEST_CMD ?= pnpm --dir frontend dlx @playwright/test@1.52.0 test --config frontend/playwright.config.ts

.PHONY: help detect verify-smoke verify-local verify-ci verify-preflight \
	verify-profile-smoke verify-profile-local verify-profile-ci \
	verify-scaffold-smoke verify-scaffold-local verify-scaffold-ci \
	verify-backend-smoke verify-backend-local verify-backend-ci \
	verify-frontend-smoke verify-frontend-local verify-frontend-ci \
	verify-api-e2e verify-ui-e2e

help:
	@echo AgentKit verification targets:
	@echo   make detect        - print verification profile
	@echo   make verify-smoke  - fast verification checks for current profile
	@echo   make verify-local  - local DoD checks for current profile
	@echo   make verify-ci     - CI DoD checks for current profile
	@echo   make verify-api-e2e - API e2e checks (backend only)
	@echo   make verify-ui-e2e  - UI e2e checks (frontend only)
	@echo
	@echo Detected profile: $(PROFILE)

detect:
	@python $(CONTRACT_SCRIPT) detect
	@echo make profile: $(PROFILE)

verify-preflight:
	@python $(CONTRACT_SCRIPT) verify --mode $(MODE)

verify-scaffold-smoke:
	@echo scaffold-only smoke checks completed.

verify-scaffold-local:
	@echo scaffold-only local checks completed.

verify-scaffold-ci:
	@echo scaffold-only ci checks completed.

verify-backend-smoke:
	@echo "==> backend smoke checks"
	@$(BACKEND_SMOKE_CMD)

verify-backend-local:
	@echo "==> backend local checks"
	@$(BACKEND_LOCAL_CMD)

verify-backend-ci:
	@echo "==> backend ci checks"
	@$(BACKEND_CI_CMD)

verify-frontend-smoke:
	@echo "==> frontend smoke checks"
	@$(FRONTEND_SMOKE_CMD)

verify-frontend-local:
	@echo "==> frontend local checks"
	@$(FRONTEND_LOCAL_CMD)

verify-frontend-ci:
	@echo "==> frontend ci checks"
	@$(FRONTEND_CI_CMD)

verify-profile-smoke: verify-scaffold-smoke
ifeq ($(HAS_BACKEND),1)
verify-profile-smoke: verify-backend-smoke
endif
ifeq ($(HAS_FRONTEND),1)
verify-profile-smoke: verify-frontend-smoke
endif

verify-profile-local: verify-scaffold-local
ifeq ($(HAS_BACKEND),1)
verify-profile-local: verify-backend-local
endif
ifeq ($(HAS_FRONTEND),1)
verify-profile-local: verify-frontend-local
endif

verify-profile-ci: verify-scaffold-ci
ifeq ($(HAS_BACKEND),1)
verify-profile-ci: verify-backend-ci
endif
ifeq ($(HAS_FRONTEND),1)
verify-profile-ci: verify-frontend-ci
endif

verify-smoke: MODE := smoke
verify-smoke: verify-preflight verify-profile-smoke
	@echo verify-smoke passed for profile: $(PROFILE)

verify-local: MODE := local
verify-local: verify-preflight verify-profile-local
	@echo verify-local passed for profile: $(PROFILE)

verify-ci: MODE := ci
verify-ci: verify-preflight verify-profile-ci
	@echo verify-ci passed for profile: $(PROFILE)

verify-api-e2e:
ifeq ($(HAS_BACKEND),0)
	@echo "ERROR: verify-api-e2e requires backend marker (services/api/pyproject.toml)." >&2
	@exit 1
endif
	@echo "==> api e2e checks"
	@$(BACKEND_API_E2E_CMD)
	@echo verify-api-e2e passed for profile: $(PROFILE)

verify-ui-e2e:
ifeq ($(HAS_FRONTEND),0)
	@echo "ERROR: verify-ui-e2e requires frontend marker (frontend/package.json)." >&2
	@exit 1
endif
ifeq ($(PLAYWRIGHT_SKIP_INSTALL),1)
	@echo "==> ui e2e checks (browser install skipped)"
	@$(FRONTEND_UI_E2E_TEST_CMD)
else
	@echo "==> ui e2e checks"
	@$(FRONTEND_UI_E2E_INSTALL_CMD) && $(FRONTEND_UI_E2E_TEST_CMD)
endif
	@echo verify-ui-e2e passed for profile: $(PROFILE)
