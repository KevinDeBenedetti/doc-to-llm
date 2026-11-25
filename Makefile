.PHONY: help clean setup start upgrade lint test
.DEFAULT_GOAL := help

help: ## Show helper
	@echo "Usage: make <command>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

clean: ## Clean build files and dependencies
	@echo "Cleaning..."
	docker compose down

	@echo "Removing python environment..."
	@find . -type d -name "__pycache__" -prune -print -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -prune -print -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -prune -print -exec rm -rf {} +
	@find . -type d -name ".venv" -prune -print -exec rm -rf {} +
	@find . -type f -name "server.log" -prune -print -exec rm -r {} +

	@echo "Removing node environment..."
	@find . -type d -name "node_modules" -prune -print -exec rm -rf {} +

	@echo "Clean cache all..."
	cd apps/server && \
		uv cache clean

setup: ## Create the local venv and install the server dependencies
	@echo "Setting up server..."
	cd apps/server && \
		uv venv --clear && \
		uv sync --no-cache

start: ## Build and start the development container
	@echo "Start dev environment..."
	docker compose up -d --build

upgrade: clean setup ## Upgrade the server dependencies
	@echo "Upgrade api..."
	cd apps/server && \
		uv run python upgrade_pyproject.py

lint: ## Lint code
	@echo "Linting code..."
	cd apps/server && \
		uv run ruff check --fix && \
		uv run ruff format

test: ## Run the server tests
	@echo "Running tests..."
	cd apps/server && \
		uv run pytest
