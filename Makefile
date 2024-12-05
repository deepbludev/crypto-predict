# Infrastructure
up:
	docker compose up -d

messagebus-up:
	docker compose up -d redpanda-console

# Run linter
lint:
	uv run ruff check .

# Run formatter
format:
	uv run ruff check --fix .

# Run type checker
typecheck:
	uv run pyright

test:
	uv run pytest

# Run CI
ci: lint typecheck test

# Clean up build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

## Trades service
run:
ifeq ($(svc), trades)
	uv run fastapi run services/trades/trades
endif

dev:
ifeq ($(svc), trades)
	uv run fastapi dev services/trades/trades
endif
