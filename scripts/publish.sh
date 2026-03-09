#!/usr/bin/env bash
# Build wheel and publish to AWS CodeArtifact
# Usage: ./scripts/publish.sh [VERSION]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_DIR="${REPO_ROOT}/python"

DOMAIN="${DOMAIN:-medicoder}"
REPO="${REPOSITORY:-packages}"
REGION="${REGION:-us-east-1}"
ACCOUNT_ID="${ACCOUNT_ID:?Must set ACCOUNT_ID}"

VERSION="${1:-}"

echo "=== Bunkhouse Protobuf Publish ==="
echo "Domain:  ${DOMAIN}"
echo "Repo:    ${REPO}"
echo "Region:  ${REGION}"
echo "Account: ${ACCOUNT_ID}"

# Get CodeArtifact auth token
echo "Fetching CodeArtifact token..."
CODEARTIFACT_TOKEN=$(aws codeartifact get-authorization-token \
    --domain "${DOMAIN}" \
    --domain-owner "${ACCOUNT_ID}" \
    --region "${REGION}" \
    --query authorizationToken \
    --output text)

ENDPOINT="https://${DOMAIN}-${ACCOUNT_ID}.d.codeartifact.${REGION}.amazonaws.com/pypi/${REPO}/"

# Optionally bump version
if [ -n "${VERSION}" ]; then
    echo "Setting version to ${VERSION}..."
    sed -i "s/__version__ = .*/__version__ = \"${VERSION}\"/" \
        "${PYTHON_DIR}/bunkhouse_protobuf/_version.py"
fi

# Build the wheel
echo "Building wheel..."
cd "${PYTHON_DIR}"
rm -rf dist/
python3 -m pip install --quiet build twine
python3 -m build --wheel --outdir dist/

# Publish
echo "Publishing to CodeArtifact..."
python3 -m twine upload \
    --repository-url "${ENDPOINT}" \
    --username aws \
    --password "${CODEARTIFACT_TOKEN}" \
    dist/*.whl

echo "Published successfully."
