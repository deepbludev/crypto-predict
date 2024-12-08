## --- BUILDER
FROM python:3.12-slim-bookworm AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project into `/app`
WORKDIR /app

# Copy in pyproject.toml, uv.lock 
COPY pyproject.toml uv.lock /app/

# Get the service name from the build arg
ARG SERVICE_NAME
ENV SERVICE_NAME=${SERVICE_NAME}

# Copy and services & libs to build the workspace
COPY services /app/services
COPY libs /app/libs

# Install the project's dependencies using the lockfile and settings
# only selecting the default dep groups and the specific service dep group
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --extra ${SERVICE_NAME} --no-install-project

# Add the rest of the project source code
COPY . /app
# Install project separately from its dependencies to optimize layer caching
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev 

# Delete the rest of the services source code to optimize image size
RUN find /app/services -mindepth 1 -maxdepth 1 -type d ! -name "${SERVICE_NAME}" -exec rm -rf {} + 

# Copy the entrypoint script and make it executable
RUN chmod +x /app/.docker/entrypoint.sh

## --- RUNNER
# Then, use a final image without uv
FROM python:3.12-slim-bookworm AS runner

# Copy the application from the builder
COPY --from=builder --chown=app:app /app /app
# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

ARG SERVICE_NAME
ENV SERVICE_NAME=${SERVICE_NAME}

# Run the FastAPI application in production mode
EXPOSE 8000
ENTRYPOINT ["/app/.docker/entrypoint.sh"]