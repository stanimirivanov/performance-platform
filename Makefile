# --- Setup & Installation ---
.PHONY: help setup install generate-models dev-install test lint format clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

setup: ## Initialize development environment
	@echo "Installing Python dependencies..."
	cd platform && uv sync
	@echo "Installing JavaScript dependencies..."
	pnpm install
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "Setup complete!"

install: ## Install all dependencies
	cd platform && uv sync
	pnpm install

generate-models: ## Generate Pydantic models from JSON schemas
	cd platform && uv run python scripts/generate_models.py

test: ## Run all tests
	cd platform && uv run pytest
	pnpm test

lint: ## Run linting
	cd platform && uv run ruff check .
	cd platform && uv run mypy .
	pnpm lint

format: ## Format code
	cd platform && uv run ruff format .
	cd platform && uv run ruff check --fix .
	pnpm format

api: ## Start API server
	cd platform && uv run perfeng-api --reload

cli: ## Run CLI
	cd platform && uv run python -m perfeng.cli

clean: ## Clean build artifacts
	rm -rf platform/.pytest_cache
	rm -rf platform/.mypy_cache
	rm -rf platform/.ruff_cache
	rm -rf platform/htmlcov
	rm -rf node_modules
	rm -rf tests/playwright/node_modules
	rm -rf results/
	rm -rf artifacts/
	@echo "Clean complete!"

# --- k6 Test ---
.PHONY: k6-smoke k6-regression

k6-smoke: ## Run k6 smoke test
	cd tests/k6 && k6 run --config ../../workloads/smoke/checkout.yaml checkout/scenario.js

k6-regression: ## Run k6 regression test
	cd tests/k6 && k6 run --config ../../workloads/regression/checkout.yaml checkout/scenario.js

# --- k8s Infrastructure ---
.PHONY: cluster-up cluster-down cluster-status cluster-health install-metrics install-namespaces

# Detect OS and set appropriate script runner
ifeq ($(OS),Windows_NT)
    SCRIPT_RUNNER = powershell -ExecutionPolicy Bypass -File
    SCRIPT_EXT = .ps1
else
    SCRIPT_RUNNER = bash
    SCRIPT_EXT = .sh
endif

cluster-up: ## Create local kind cluster
	$(SCRIPT_RUNNER) infra/local/scripts/cluster-up$(SCRIPT_EXT)

cluster-down: ## Delete local kind cluster
	$(SCRIPT_RUNNER) infra/local/scripts/cluster-down$(SCRIPT_EXT)

cluster-status: ## Show cluster status
	$(SCRIPT_RUNNER) infra/local/scripts/cluster-status$(SCRIPT_EXT)

cluster-health: ## Run cluster health check
	$(SCRIPT_RUNNER) infra/local/scripts/cluster-health-check$(SCRIPT_EXT)

install-metrics: ## Install metrics-server
	$(SCRIPT_RUNNER) infra/local/scripts/install-metrics-server$(SCRIPT_EXT)

install-namespaces: ## Install perfeng namespaces and RBAC
	$(SCRIPT_RUNNER) infra/local/scripts/install-namespaces$(SCRIPT_EXT)

# --- Monitoring ---
.PHONY: monitoring-up monitoring-down

monitoring-up: ## Install monitoring stack
	$(SCRIPT_RUNNER) infra/local/scripts/install-monitoring$(SCRIPT_EXT)

monitoring-down: ## Uninstall monitoring stack
	$(SCRIPT_RUNNER) infra/local/scripts/uninstall-monitoring$(SCRIPT_EXT)


# --- k6 Infrastructure ---
.PHONY: install-minio

install-minio: ## Install MinIO for artifact storage
	$(SCRIPT_RUNNER) infra/local/scripts/install-minio$(SCRIPT_EXT)

# --- k6 Tests ---
.PHONY: run-k6-test run-k6-smoke run-k6-regression


run-k6-smoke: ## Run k6 smoke test as Kubernetes job
	$(SCRIPT_RUNNER) infra/local/kind/k6-jobs/scripts/run-k6-test$(SCRIPT_EXT) -TestName checkout -Profile smoke

run-k6-regression: ## Run k6 regression test as Kubernetes job
	$(SCRIPT_RUNNER) infra/local/kind/k6-jobs/scripts/run-k6-test$(SCRIPT_EXT) -TestName checkout -Profile regression

run-k6-test: ## Run k6 test as Kubernetes job (usage: make run-k6-test TEST=checkout PROFILE=smoke)
	$(SCRIPT_RUNNER) infra/local/kind/k6-jobs/scripts/run-k6-test$(SCRIPT_EXT) -TestName $(TEST) -Profile $(PROFILE)