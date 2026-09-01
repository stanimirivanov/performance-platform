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

generate-models: ## Generate Pydantic models from JSON schemas and SQL migrations
	cd platform && uv run python scripts/generate_models.py && uv run python scripts/generate_sqlalchemy_models.py

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

clean-pycache: ## Clean "__pycache__" directories
	Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" |
    	Remove-Item -Recurse -Force

	Get-ChildItem -Path . -File -Recurse -Filter "*.pyc" |
    	Remove-Item -Force

# --- k8s Infrastructure ---
.PHONY: cluster-up cluster-down infra-install infra-upgrade infra-uninstall

# Detect OS for script execution
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

infra-install: ## Install infrastructure via Helm
	helm dependency update infra/charts/perfeng-infra
	helm install perfeng-infra infra/charts/perfeng-infra --wait --timeout 10m

infra-upgrade: ## Upgrade infrastructure
	helm dependency update infra/charts/perfeng-infra
	helm upgrade perfeng-infra infra/charts/perfeng-infra --wait --timeout 10m

infra-uninstall: ## Uninstall infrastructure
	helm uninstall perfeng-infra

.PHONY: port-forward apply-migrations reset-migrations

port-forward:
	kubectl port-forward -n metadata-db svc/postgres-service 5432:5432

apply-migrations: ## Apply database migrations
	@echo "Make sure PostgreSQL is port-forwarded (run 'make port-forward' in another terminal)"
	cd platform && uv run python scripts/run_migrations.py

reset-migrations: ## Reset database migrations
	@echo "Make sure PostgreSQL is port-forwarded (run 'make port-forward' in another terminal)"
	cd platform && uv run python scripts/run_migrations.py --reset

# --- k6 Tests ---
.PHONY: sut-install sut-uninstall sut-status k6-test k6-smoke k6-search-smoke k6-account-smoke k6-regression k6-build-image k6-uninstall k6-list perf-test perf-smoke

# SUT (System Under Test)
sut-install: ## Install sample SUT
	helm upgrade --install sample-sut infra/charts/sample-sut --namespace perf-sut --wait --timeout 5m

sut-uninstall: ## Uninstall sample SUT
	helm uninstall sample-sut -n perf-sut

sut-status: ## Show SUT status
	kubectl get pods -n perf-sut
	kubectl get svc -n perf-sut

# k6 Test Runner
k6-build-image: ## Build and load k6 test Docker image
	docker build -t perfeng-k6-tests:latest tests/k6
	kind load docker-image perfeng-k6-tests:latest --name perfeng-local

k6-smoke: k6-build-image ## Run k6 checkout smoke test
	helm upgrade --install k6-checkout-smoke infra/charts/k6-runner --namespace perf-generators --set test.name=checkout --set test.profile=smoke --set sut.baseUrl="http://perf-sut-service.perf-sut:8080" --wait --timeout 15m

k6-search-smoke: k6-build-image ## Run k6 search smoke test
	helm upgrade --install k6-search-smoke infra/charts/k6-runner --namespace perf-generators --set test.name=search --set test.profile=smoke --set sut.baseUrl="http://perf-sut-service.perf-sut:8080" --wait --timeout 15m

k6-account-smoke: k6-build-image ## Run k6 account smoke test
	helm upgrade --install k6-account-smoke infra/charts/k6-runner --namespace perf-generators --set test.name=account --set test.profile=smoke --set sut.baseUrl="http://perf-sut-service.perf-sut:8080" --wait --timeout 15m

k6-regression: k6-build-image ## Run k6 checkout regression test
	helm upgrade --install k6-checkout-regression infra/charts/k6-runner --namespace perf-generators --set test.name=checkout --set test.profile=regression --set sut.baseUrl="http://perf-sut-service.perf-sut:8080" --wait --timeout 20m

k6-test: k6-build-image ## Run k6 test (usage: make k6-test TEST=checkout PROFILE=smoke)
	helm upgrade --install k6-$(TEST)-$(PROFILE) infra/charts/k6-runner --namespace perf-generators --set test.name=$(TEST) --set test.profile=$(PROFILE) --set sut.baseUrl="http://perf-sut-service.perf-sut:8080" --wait --timeout 20m

k6-uninstall: ## Uninstall k6 test (usage: make k6-uninstall TEST=checkout PROFILE=smoke)
	helm uninstall k6-$(TEST)-$(PROFILE) -n perf-generators

k6-list: ## List k6 test releases
	helm list -n perf-generators

# Combined Targets
perf-test: ## Install SUT and run test (usage: make perf-test TEST=search PROFILE=smoke)
	sut-install k6-test 

perf-smoke: ## Install SUT and run search smoke test
	sut-install k6-search-smoke 

perf-all-smoke: ## Install SUT and run all smoke tests 
	sut-install k6-smoke k6-search-smoke k6-account-smoke