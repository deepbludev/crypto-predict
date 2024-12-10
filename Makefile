# ----------------------------------------
# Infrastructure
# ----------------------------------------
build:
	docker compose up  --build -d $(svc)

up:
	docker compose up -d $(svc)

down:
	docker compose down $(svc)

stop:
	docker compose stop $(svc)

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
SERVICES = trades candles ta features
SERVICES_PATH = services/$(svc)/$(svc)
PORTS = trades=8001 candles=8002 ta=8003 features=8004
# Get the port for a service from the PORTS variable
port_for_service = $(word 2,$(subst =, ,$(filter $(1)=%,$(PORTS))))

run:
ifeq ($(filter $(svc),$(SERVICES)),$(svc))
	uv run fastapi run $(SERVICES_PATH) --port $(call port_for_service,$(svc))
else
	@echo "Invalid service: $(svc)"
endif

dev:
ifeq ($(filter $(svc),$(SERVICES)),$(svc))
	uv run fastapi dev $(SERVICES_PATH) --port $(call port_for_service,$(svc))
else
	@echo "Invalid service: $(svc)"
endif
