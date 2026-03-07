"""Bunkhouse protobuf event schemas."""

from bunkhouse_protobuf._version import __version__
from bunkhouse.events.envelope_pb2 import BunkhouseEvent

__all__ = ["__version__", "BunkhouseEvent"]

# ---------------------------------------------------------------------------
# Auto-version stamping
#
# Patch BunkhouseEvent.SerializeToString so that every outbound event
# automatically carries the package's schema_version (derived from
# _version.__version__).  The version is encoded as a single uint32 whose
# value is the concatenation of major*10000 + minor*100 + patch, so that
# 1.0.0 → 10000, 1.2.3 → 10203, etc.
# ---------------------------------------------------------------------------

def _version_int() -> int:
    parts = __version__.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    return major * 10000 + minor * 100 + patch


_SCHEMA_VERSION_INT: int = _version_int()
_original_serialize = BunkhouseEvent.SerializeToString


def _patched_serialize(self, deterministic=None):  # type: ignore[override]
    self.schema_version = _SCHEMA_VERSION_INT
    if deterministic is not None:
        return _original_serialize(self, deterministic=deterministic)
    return _original_serialize(self)


BunkhouseEvent.SerializeToString = _patched_serialize  # type: ignore[method-assign]
