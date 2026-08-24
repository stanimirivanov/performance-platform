.PHONY: help setup install dev-install test lint format clean

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

k6-smoke: ## Run k6 smoke test
	cd tests/k6 && k6 run --config ../../workloads/smoke/checkout.yaml checkout/scenario.js

k6-regression: ## Run k6 regression test
	cd tests/k6 && k6 run --config ../../workloads/regression/checkout.yaml checkout/scenario.js