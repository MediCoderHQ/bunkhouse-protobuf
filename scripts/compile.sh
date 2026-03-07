#!/usr/bin/env bash
# Compile proto files -> Python _pb2.py files using grpcio-tools
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROTO_DIR="${REPO_ROOT}/proto"
OUT_DIR="${REPO_ROOT}/python"

echo "Compiling protos from ${PROTO_DIR} -> ${OUT_DIR}/bunkhouse/events/"

# Install codegen tools if not present
python3 -m pip install --quiet "grpcio-tools>=1.62.0" "protobuf>=5.26.0"

# Find all .proto files
PROTO_FILES=$(find "${PROTO_DIR}" -name "*.proto")

if [ -z "${PROTO_FILES}" ]; then
    echo "No .proto files found in ${PROTO_DIR}. Skipping compilation."
    exit 0
fi

mkdir -p "${OUT_DIR}"

# Generate Python protobuf stubs.
# Output goes to python/bunkhouse/events/ matching the proto package path.
# shellcheck disable=SC2086
python3 -m grpc_tools.protoc \
    -I "${PROTO_DIR}" \
    --python_out="${OUT_DIR}" \
    --grpc_python_out="${OUT_DIR}" \
    ${PROTO_FILES}

# Ensure __init__.py files exist so the generated code is importable as packages
touch "${OUT_DIR}/bunkhouse/__init__.py"
touch "${OUT_DIR}/bunkhouse/events/__init__.py"

echo "Generated files:"
ls -l "${OUT_DIR}/bunkhouse/events/"*_pb2*.py 2>/dev/null || echo "  (none yet)"

echo "Done."
