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