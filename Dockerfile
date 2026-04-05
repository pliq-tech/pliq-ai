# Stage 1: Builder
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    protobuf-compiler \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Cached dependency layer
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy project and install
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# Generate gRPC stubs from proto files
RUN if [ -d src/grpc/proto ] && ls src/grpc/proto/*.proto 1>/dev/null 2>&1; then \
    .venv/bin/python -m grpc_tools.protoc \
        -Isrc/grpc/proto \
        --python_out=src \
        --grpc_python_out=src \
        src/grpc/proto/*.proto 2>/dev/null || true; \
    fi

# Stage 2: Runtime
FROM python:3.14-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    libpng16-16t64 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1001 pliq && \
    useradd --system --uid 1001 --gid pliq pliqai

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH"

USER pliqai
EXPOSE 50051
CMD ["python", "-m", "src.main"]
