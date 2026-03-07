# bunkhouse-protobuf

Protobuf event schemas for the Bunkhouse worker orchestration system.
Generated Python package is published to AWS CodeArtifact.

## Repository layout

```
proto/                        # Protobuf source files
  bunkhouse/
    events/                   # Event schema .proto files (added in T1+)

python/                       # Python package
  pyproject.toml
  bunkhouse_protobuf/
    __init__.py
    _version.py
    *_pb2.py                  # Generated – do NOT edit by hand

scripts/
  compile.sh                  # proto → _pb2.py codegen
  publish.sh                  # Build wheel + upload to CodeArtifact

buf.yaml                      # buf module config (linting)
buf.gen.yaml                  # buf code-generation config
.github/workflows/ci.yml      # CI: lint → compile/test → publish
```

## Adding a new proto schema

1. Create `proto/bunkhouse/events/<name>.proto`
2. Run `bash scripts/compile.sh` locally to verify it compiles
3. Run `buf lint` to check style
4. Open a PR — CI will lint, compile, and test automatically
5. Merge to `main` triggers versioned publish to CodeArtifact

## Local development

### Prerequisites

- Python ≥ 3.9
- `buf` CLI (https://buf.build/docs/installation)
- AWS credentials (for publish only)

### Compile protos locally

```bash
bash scripts/compile.sh
```

This installs `grpcio-tools` into the active venv (or system Python) and
generates `*_pb2.py` files into `python/bunkhouse_protobuf/`.

### Lint with buf

```bash
buf lint
```

### Run tests

```bash
pip install -e python/
pytest python/tests/ -v
```

### Publish manually

```bash
export ACCOUNT_ID=<aws-account-id>
export REGION=us-east-1          # optional, defaults to us-east-1
export DOMAIN=medicoder           # optional, defaults to medicoder
export REPOSITORY=packages        # optional, defaults to packages
bash scripts/publish.sh [VERSION]
```

## CI / CD

| Job | Trigger | Steps |
|-----|---------|-------|
| `lint` | every push / PR | `buf lint` |
| `compile-and-test` | after lint passes | `compile.sh`, `pip install`, `pytest` |
| `publish` | push to `main` only | compile, bump version, `publish.sh` |

Secrets / variables required in GitHub Actions:
- `AWS_OIDC_ROLE` – IAM role ARN for OIDC auth
- `vars.ACCOUNT_ID` – AWS account ID
- `vars.REGION` – AWS region
- `vars.DOMAIN` – CodeArtifact domain (default: `medicoder`)
- `vars.REPOSITORY` – CodeArtifact repo (default: `packages`)
