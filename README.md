# pliq-ai

Python AI service for the Pliq platform. Provides fraud detection, tenant-listing matching, and document analysis via gRPC.

## Prerequisites

- [Python](https://www.python.org/) >= 3.14
- [uv](https://docs.astral.sh/uv/) >= 0.11.3

## Setup

```bash
# Clone and enter the repo
cd pliq-ai

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
uv sync

# Run the service
uv run python -m src.main
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GRPC_HOST` | No | Bind host (default: `0.0.0.0`) |
| `GRPC_PORT` | No | gRPC port (default: `50051`) |
| `MAX_WORKERS` | No | gRPC server workers (default: `10`) |
| `GOOGLE_API_KEY` | Yes | Google AI API key for Gemini |
| `GOOGLE_CLOUD_PROJECT` | No | GCP project ID |
| `GEMINI_PRO_MODEL` | No | Gemini Pro model name |
| `GEMINI_FLASH_MODEL` | No | Gemini Flash model name |
| `FRAUD_DETECTION_THRESHOLD` | No | Fraud score threshold (default: `0.7`) |
| `LOG_LEVEL` | No | Logging level (default: `info`) |

## Project Structure

```
src/
├── __init__.py
├── main.py              # gRPC server entry point
├── config.py            # Pydantic settings from environment
├── exceptions.py        # Custom exception hierarchy
├── agents/              # AI agent implementations
├── api/                 # gRPC endpoint handlers
├── application/         # Orchestration services
├── domain/              # Core models and protocols
│   ├── models.py        # FraudResult, MatchResult, DocumentResult
│   └── protocols.py     # FraudDetector, TenantMatcher interfaces
├── infrastructure/      # External service adapters (Gemini client)
├── models/              # Fraud detection and matching algorithms
│   ├── fraud_detection.py  # ELA, FFT, EXIF analysis, price anomaly
│   └── matching.py         # Multi-criteria lifestyle matching
├── crypto/              # Cryptographic utilities
└── grpc/
    ├── handlers/        # gRPC service implementations
    └── proto/           # Protocol Buffer definitions
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Lint
uv run ruff check

# Format
uv run ruff format

# Type check
uv run mypy src/
```

## Docker

```bash
# Build
docker build -t pliq-ai .

# Run
docker run -p 50051:50051 --env-file .env pliq-ai
```

## Proto Regeneration

gRPC stubs are generated during Docker build. For local regeneration:

```bash
# From root project
make proto-sync

# Or manually
scripts/generate_proto.sh
```
