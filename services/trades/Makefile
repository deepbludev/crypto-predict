# Run Trades service
run:
	uv run fastapi run trades

dev:
	uv run fastapi dev trades

# Run docker image
build:
	docker build -f Dockerfile -t cryptopredict-trades .

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
