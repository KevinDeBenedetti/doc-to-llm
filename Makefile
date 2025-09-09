PYTHONPATH=$(PWD)

.PHONY: help setup apps start dev build clean
.DEFAULT_GOAL := help

help: ## Show helper
	@echo "Usage: make <command>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

lint: ## Lint Code
	@echo "Linting code..."

clean: ## Clean build files and dependencies
	@echo "Cleaning dev environment..."
	docker compose down
	rm -rf .ruff_cache .venv uv.lock server.log
	uv cache clean

setup: ## Start the development api
	@echo "Setup api..."
	uv venv --clear && \
	source .venv/bin/activate && \
	uv sync --no-cache

start-dev: clean setup ## Start the development environment with upgrade
	@echo "Start dev environment (with upgrade)..."
	uv run fastapi dev src/main.py

start: clean setup ## Start the development environment
	@echo "Start dev environment (no upgrade)..."
	docker compose build --no-cache
	docker compose up -d

upgrade: clean setup ## Upgrade api dependencies
	@echo "Upgrade api..."
	uv run python upgrade_pyproject.py
