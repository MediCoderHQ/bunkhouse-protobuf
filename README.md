# bunkhouse-protobuf

Protobuf event schemas for the [Bunkhouse](https://github.com/joeLepper/bunkhouse) worker orchestration system.

Event schema `.proto` files live in `proto/bunkhouse/events/`. A CI pipeline lints, compiles, and publishes the generated Python package to AWS CodeArtifact on every merge to `main`.

## Quick start

```bash
# Compile protos -> python/bunkhouse_protobuf/*_pb2.py
bash scripts/compile.sh

# Lint with buf
buf lint

# Install the package locally
pip install -e python/
```

See [CLAUDE.md](CLAUDE.md) for full development and CI documentation.
