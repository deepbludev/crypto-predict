# Run Trades service
run:
	uvicorn trades.main:app --port 8000 --host 0.0.0.0

dev:
	uvicorn trades.main:app --port 8000 --host 0.0.0.0 --reload

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
