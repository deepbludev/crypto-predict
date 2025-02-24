CLUSTERS = messagebus indicators indicators_historical sentiment_signals
SERVICES = trades candles ta features news news_signals price_predictions
SERVICES_PATH = services/$(svc)/$(svc)
PORTS = trades=8001 candles=8002 ta=8003 features=8004 news=8005 news_signals=8006 price_predictions=8007

# Get the port for a service from the PORTS variable
port_for_service = $(word 2,$(subst =, ,$(filter $(1)=%,$(PORTS))))

# ----------------------------------------
# Infrastructure
# ----------------------------------------
# Commands for running services in docker compose as clusters.
#
# Available clusters:
# - messagebus
# - indicators
# - indicators_historical
# - sentiment_signals
# - sentiment_signals_historical
#
# Build a service in a cluster
# Usage: make build cluster=cryptopredict-messagebus svc=trades
# Available services: $(SERVICES)

build:
	docker compose -f .docker/$(cluster).compose.yaml up $(svc) --build -d 

up:
	docker compose -f .docker/$(cluster).compose.yaml up $(svc) -d

down:
	docker compose -f .docker/$(cluster).compose.yaml down $(svc)

stop:
	docker compose -f .docker/$(cluster).compose.yaml stop $(svc)

backfill:
	$(eval NOW := $(shell date +%s))
	@echo "Starting backfill with Job ID: $(NOW)"
	BACKFILL_JOB_ID=$(NOW) docker compose -f .docker/$(cluster)_historical.compose.yaml up -d $(if $(build),--build,) 

clean-backfill:
	@echo "Cleaning historical topics..."
	docker compose -f .docker/messagebus.compose.yaml exec redpanda rpk topic delete -r ".*historical.*"
	@echo "Fetching historical consumer groups..."
	docker compose -f .docker/messagebus.compose.yaml exec redpanda rpk group list | grep historical | xargs -r docker compose -f .docker/messagebus.compose.yaml exec redpanda rpk group delete


# ----------------------------------------
# Services
# ----------------------------------------
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

# ----------------------------------------
# ETLs
# ----------------------------------------
etl:
	uv run python -m services.$(svc).etl.$(name)

# ----------------------------------------
# Training Pipelines
# ----------------------------------------
train:
	uv run python -m services.price_predictions.training.train_model

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



