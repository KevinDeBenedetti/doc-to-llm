PYTHONPATH=$(PWD)

.PHONY: help setup apps start dev build clean
.DEFAULT_GOAL := help

help: ## Show helper
	@echo "Usage: make <command>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

clean: ## Clean build files and dependencies
	@echo "Cleaning..."
	docker compose down

	@echo "Removing all..."
	@find . -type d -name "__pycache__" -prune -print -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -prune -print -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -prune -print -exec rm -rf {} +
	@find . -type d -name ".venv" -prune -print -exec rm -rf {} +
	@find . -type f -name "server.log" -prune -print -exec rm -r {} +

	@echo "Removing all..."
	@find . -type d -name "node_modules" -prune -print -exec rm -rf {} +
	@find . -type d -name ".nuxt" -prune -print -exec rm -rf {} +

	@echo "Clean cache all..."
	cd apps/server && \
		uv cache clean

setup: ## Start the development api
	@echo "Setting up server..."
	cd apps/server && \
		uv venv --clear && \
		uv sync --no-cache

setup-docus: ## Setup docus
	@echo "Setting up docus..."
	cd apps/docus && \
		pnpm install

start: setup setup-docus ## Start the development environment
	@echo "Start dev environment..."
	docker compose build --no-cache
	docker compose up -d

	@echo "Start docus..."
	cd apps/docus && \
		pnpm run dev

upgrade: clean setup ## Upgrade api dependencies
	@echo "Upgrade api..."
	cd apps/server && \
		uv run python upgrade_pyproject.py

	cd apps/docus && \
		pnpm up --latest

lint: ## Lint code
	@echo "Linting code..."
	cd apps/server && \
		uv run ruff check --fix && \
		uv run ruff format
