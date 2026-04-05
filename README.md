# pliq-ai

Python AI service for the Pliq platform. Provides fraud detection, tenant-listing matching, lease analysis, condition report comparison, and property search via gRPC. Uses Google ADK for agent orchestration and Gemini models for reasoning, classification, and vision tasks.

## Prerequisites

- [Python](https://www.python.org/) >= 3.14
- [uv](https://docs.astral.sh/uv/) >= 0.7.12

## Setup

```bash
cd pliq-ai

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
uv sync

# Generate protobuf stubs (required before first run)
bash scripts/generate_proto.sh

# Run the service
uv run python -m src.main
```

## Environment Variables

See `.env.example` for the full list with defaults. Required variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google AI API key for Gemini models |
| `GOOGLE_CLOUD_PROJECT` | No | GCP project ID |
| `GRPC_HOST` | No | Bind host (default: `0.0.0.0`) |
| `GRPC_PORT` | No | gRPC port (default: `50051`) |
| `LOG_LEVEL` | No | Logging level (default: `info`) |

## Project Structure

```
src/
├── __init__.py
├── main.py                  # gRPC server entry point
├── config.py                # Pydantic settings from environment
├── exceptions.py            # Custom exception hierarchy
├── logging.py               # Structured JSON logging
├── agents/
│   ├── fraud_agent.py       # Google ADK fraud detection agent
│   ├── search_agent.py      # Property search agent
│   ├── matching_agent.py    # Lifestyle matching agent
│   └── orchestrator.py      # Agent orchestration utilities
├── models/
│   ├── fraud_detection.py   # ELA, FFT, EXIF analysis, price anomaly
│   ├── duplication_detection.py  # Listing duplication detection
│   ├── matching.py          # Multi-criteria lifestyle matching
│   ├── lease_analysis.py    # Lease clause extraction and risk analysis
│   └── condition_report.py  # Check-in/check-out photo comparison
├── grpc/
│   ├── server.py            # Async gRPC server setup
│   ├── handlers/
│   │   ├── fraud_handler.py
│   │   ├── matching_handler.py
│   │   ├── lease_handler.py
│   │   └── search_handler.py
│   └── proto/
│       ├── fraud_detection.proto
│       ├── matching.proto
│       ├── lease_analysis.proto
│       └── search.proto
├── domain/                  # Core domain models and protocols
├── infrastructure/          # External service adapters
└── crypto/                  # PQ cryptography (roadmap)
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

## Proto Generation

gRPC stubs are generated during Docker build. For local development:

```bash
bash scripts/generate_proto.sh
```

## Docker

```bash
# Build
docker build -t pliq-ai .

# Run
docker run -p 50051:50051 --env-file .env pliq-ai
```
