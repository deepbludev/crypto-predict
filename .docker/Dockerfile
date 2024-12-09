## --- BASE
FROM python:3.12-slim-bookworm AS base

# Install build dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  build-essential \
  wget \
  && rm -rf /var/lib/apt/lists/*

# Install ta-lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
  tar -xzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr --build=aarch64-unknown-linux-gnu && \
  make && \
  make install && \
  cd .. && \
  rm -rf ta-lib*

FROM base AS builder
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

# Copy and services & libs to build the workspace
COPY services /app/services
COPY libs /app/libs

# Install the project's dependencies using the lockfile and settings
# only selecting the default dep groups and the specific service dep group
ARG SERVICE_NAME
ENV SERVICE_NAME=${SERVICE_NAME}
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --no-install-project

# Add the rest of the project source code
COPY . /app
# Install project separately from its dependencies to optimize layer caching
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev 

# Copy the entrypoint script and make it executable
RUN chmod +x /app/.docker/entrypoint.sh

## --- RUNNER
FROM base AS runner

# Copy the application from the builder
COPY --from=builder --chown=app:app /app /app
# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

ARG SERVICE_NAME
ENV SERVICE_NAME=${SERVICE_NAME}

ARG PORT
ENV PORT=${PORT}

EXPOSE ${PORT}
ENTRYPOINT ["/app/.docker/entrypoint.sh"]
