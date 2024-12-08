# ----------------------------------------
# Infrastructure
# ----------------------------------------
build:
	docker compose up --build -d

up:
	docker compose up -d

down:
	docker compose down

stop:
	docker compose stop

messagebus-up:
	docker compose up -d redpanda-console

# ----------------------------------------
# Development
# ----------------------------------------
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

# ----------------------------------------
# Services
# ----------------------------------------
run:
ifeq ($(svc), trades)
	uv run fastapi run services/trades/trades --port 8001
else ifeq ($(svc), candles)
	uv run fastapi run services/candles/candles --port 8002
else ifeq ($(svc), ta)
	uv run fastapi run services/ta/ta --port 8003
else
	@echo "Invalid service: $(svc)"
endif

dev:
ifeq ($(svc), trades)
	uv run fastapi dev services/trades/trades --port 8001
else ifeq ($(svc), candles)
	uv run fastapi dev services/candles/candles --port 8002
else ifeq ($(svc), ta)
	uv run fastapi dev services/ta/ta --port 8003
else
	@echo "Invalid service: $(svc)"
endif
