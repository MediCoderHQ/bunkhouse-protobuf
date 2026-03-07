"""Tests for schema_version auto-stamping behaviour.

Verifies that:
- schema_version is automatically stamped as an integer on SerializeToString.
- The integer for version 1.0.0 is exactly 10000.
- A manually pre-set schema_version is preserved (not overwritten).
- The version survives a full serialize/deserialize round-trip.
"""

import bunkhouse_protobuf  # noqa: F401 – triggers monkey-patch
from bunkhouse_protobuf._version import __version__
from bunkhouse_protobuf.helpers import (
    create_event,
    deserialize_from_sns,
    serialize_for_sns,
)
from bunkhouse.events.envelope_pb2 import BunkhouseEvent
from bunkhouse.events.task_pb2 import TaskEvent


def _version_int(version_str: str) -> int:
    major, minor, patch = (int(p) for p in version_str.split("."))
    return major * 10000 + minor * 100 + patch


# ---------------------------------------------------------------------------
# Auto-stamping
# ---------------------------------------------------------------------------


def test_schema_version_stamped_on_serialize():
    """schema_version should be set automatically when SerializeToString is called."""
    evt = create_event("task", "created")
    assert evt.schema_version == 0, "should be unset before serialization"
    evt.SerializeToString()
    assert evt.schema_version == _version_int(__version__)


def test_schema_version_is_integer():
    evt = create_event("step", "started")
    evt.SerializeToString()
    assert isinstance(evt.schema_version, int)


def test_schema_version_for_1_0_0_is_10000():
    """For package version 1.0.0 the encoded integer must be 10000."""
    assert __version__ == "1.0.0"
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-1"))
    evt.SerializeToString()
    assert evt.schema_version == 10000


def test_schema_version_stamped_via_serialize_for_sns():
    """serialize_for_sns (which calls SerializeToString) also stamps the version."""
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-2"))
    serialize_for_sns(evt)
    assert evt.schema_version == _version_int(__version__)


# ---------------------------------------------------------------------------
# Manual pre-set is preserved
# ---------------------------------------------------------------------------


def test_manual_schema_version_not_overwritten():
    """If schema_version is set before serialization it must be preserved."""
    evt = create_event("task", "created")
    evt.schema_version = 99999
    evt.SerializeToString()
    assert evt.schema_version == 99999, (
        "Auto-stamping must not overwrite a manually-set schema_version"
    )


def test_manual_schema_version_survives_roundtrip():
    """A manually-set schema_version should persist through serialize/deserialize."""
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-3"))
    evt.schema_version = 20100  # simulate 2.1.0
    body = serialize_for_sns(evt)

    recovered = deserialize_from_sns(body)
    assert recovered.schema_version == 20100


# ---------------------------------------------------------------------------
# Round-trip preserves auto-stamped version
# ---------------------------------------------------------------------------


def test_auto_stamped_version_survives_roundtrip():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-4"))
    body = serialize_for_sns(evt)

    recovered = deserialize_from_sns(body)
    assert recovered.schema_version == _version_int(__version__)


def test_schema_version_is_uint32():
    """schema_version field should fit in a uint32 (>= 0)."""
    evt = create_event("task", "created")
    evt.SerializeToString()
    assert 0 <= evt.schema_version <= 2**32 - 1
