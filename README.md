# pliq-ai

Python gRPC service for AI-powered fraud detection, tenant-listing matching, lease analysis, and property search. Uses Google ADK for agent orchestration and Gemini models for reasoning, classification, and vision tasks.

## Prerequisites

- [Python](https://www.python.org/) >= 3.14
- [uv](https://docs.astral.sh/uv/) >= 0.11.3

## Installation

```bash
# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
uv sync

# Install dev dependencies (testing, linting, type checking)
uv sync --dev
```

## Configuration

All configuration is loaded from environment variables via Pydantic Settings (`src/config.py`). Copy `.env.example` and fill in required values.

### Required

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google AI API key for Gemini models |

### Optional (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_HOST` | `0.0.0.0` | gRPC server bind host |
| `GRPC_PORT` | `50051` | gRPC server port |
| `MAX_WORKERS` | `10` | Maximum gRPC server workers |
| `GOOGLE_CLOUD_PROJECT` | (empty) | GCP project ID |
| `GOOGLE_LOCATION` | `us-central1` | GCP region |
| `GEMINI_PRO_MODEL` | `gemini-2.5-pro-preview-05-06` | Gemini Pro model ID (reasoning tasks) |
| `GEMINI_FLASH_MODEL` | `gemini-2.5-flash-preview-05-20` | Gemini Flash model ID (fast tasks) |
| `EMBEDDING_MODEL` | `text-embedding-005` | Text embedding model ID |
| `FRAUD_DETECTION_THRESHOLD` | `0.7` | Overall fraud detection threshold |
| `FRAUD_ELA_WEIGHT` | `0.35` | Error Level Analysis weight |
| `FRAUD_FFT_WEIGHT` | `0.25` | FFT frequency analysis weight |
| `FRAUD_EXIF_WEIGHT` | `0.20` | EXIF metadata analysis weight |
| `FRAUD_REVERSE_WEIGHT` | `0.20` | Reverse image search weight |
| `PRICE_ANOMALY_Z_THRESHOLD` | `2.0` | Z-score threshold for price anomaly |
| `DUPLICATION_TEXT_THRESHOLD` | `0.85` | Text similarity threshold for duplication |
| `DUPLICATION_PHASH_THRESHOLD` | `10` | Perceptual hash distance threshold |
| `COMMUTE_WEIGHT` | `0.25` | Matching: commute score weight |
| `NOISE_WEIGHT` | `0.15` | Matching: noise tolerance weight |
| `AMENITY_WEIGHT` | `0.15` | Matching: amenity score weight |
| `SOCIAL_WEIGHT` | `0.10` | Matching: social preference weight |
| `BUDGET_WEIGHT` | `0.25` | Matching: budget score weight |
| `PET_WEIGHT` | `0.10` | Matching: pet policy weight |
| `LOG_LEVEL` | `info` | Logging level |

## Running the Service

```bash
uv run python -m src.main
```

The gRPC server starts on `GRPC_HOST:GRPC_PORT` (default `0.0.0.0:50051`).

## Proto Files

gRPC service definitions live in `src/grpc/proto/`:

| File | Package | Services |
|------|---------|----------|
| `ai_service.proto` | `pliq.ai.v1` | `FraudDetectionService` (AnalyzeImage, AnalyzeListing, CheckPriceReasonability), `MatchingService` (RankListings, RecommendListings) |
| `fraud_detection.proto` | `pliq.fraud` | `FraudDetectionService` (AnalyzeUserBehavior, AnalyzeImages) |
| `matching.proto` | `pliq.matching` | `MatchingService` (FindMatches, ScoreCompatibility) |
| `lease_analysis.proto` | `pliq.ai.v1` | `LeaseAnalysisService` (AnalyzeClauses, CompareConditionReports) |
| `search.proto` | `pliq.ai.v1` | `SearchService` (SearchProperties, GetSearchSuggestions) |
| `common.proto` | `pliq.common.v1` | Shared types: `ListingData`, `ImageData`, `FraudScore`, `MatchScore`, `UserPreferences` |

### Regenerating Protobuf Stubs

Stubs are generated automatically during Docker build. For local development, run:

```bash
uv run python -m grpc_tools.protoc \
  -Isrc/grpc/proto \
  --python_out=src \
  --grpc_python_out=src \
  src/grpc/proto/fraud_detection.proto \
  src/grpc/proto/matching.proto \
  src/grpc/proto/lease_analysis.proto \
  src/grpc/proto/search.proto \
  src/grpc/proto/ai_service.proto \
  src/grpc/proto/common.proto
```

After generation, fix bare imports in `*_pb2_grpc.py` files so they work as a package:

```bash
# Linux
find src -name '*_pb2_grpc.py' -exec sed -i 's/^import \(.*\)_pb2/from src import \1_pb2/' {} +

# macOS
find src -name '*_pb2_grpc.py' -exec sed -i '' 's/^import \(.*\)_pb2/from src import \1_pb2/' {} +
```

## Docker

```bash
# Build
docker build -t pliq-ai .

# Run
docker run -p 50051:50051 --env-file .env pliq-ai
```

The Dockerfile uses a multi-stage build: the builder stage installs dependencies with uv and generates protobuf stubs, then the runtime stage copies only the virtual environment and source code.

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
│       ├── ai_service.proto
│       ├── common.proto
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
