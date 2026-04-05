#!/usr/bin/env bash
set -euo pipefail

PROTO_DIR="src/grpc/proto"
OUT_DIR="src"

# Compile the 4 domain-specific proto files (ai_service.proto and common.proto
# are legacy files kept for reference but excluded to avoid package conflicts).
PROTOS=(
  "${PROTO_DIR}/fraud_detection.proto"
  "${PROTO_DIR}/matching.proto"
  "${PROTO_DIR}/lease_analysis.proto"
  "${PROTO_DIR}/search.proto"
)

uv run python -m grpc_tools.protoc \
  -I"${PROTO_DIR}" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  "${PROTOS[@]}"

# Fix imports for package mode (macOS + Linux compatible)
if [[ "$(uname)" == "Darwin" ]]; then
  find "${OUT_DIR}" -name '*_pb2_grpc.py' -exec sed -i '' 's/^import \(.*\)_pb2/from src import \1_pb2/' {} +
else
  find "${OUT_DIR}" -name '*_pb2_grpc.py' -exec sed -i 's/^import \(.*\)_pb2/from src import \1_pb2/' {} +
fi

echo "Proto stubs generated successfully."
