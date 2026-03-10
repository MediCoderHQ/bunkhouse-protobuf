"""Tests for bunkhouse_protobuf helpers and auto-version stamping."""

import base64

import pytest

import bunkhouse_protobuf  # noqa: F401 – triggers monkey-patch
from bunkhouse_protobuf._version import __version__
from bunkhouse_protobuf.helpers import (
    create_event,
    deserialize_from_sns,
    serialize_for_sns,
    to_sns_attributes,
)
from bunkhouse.events.envelope_pb2 import BunkhouseEvent
from bunkhouse.events.task_pb2 import TaskEvent


# ---------------------------------------------------------------------------
# Helpers: create_event
# ---------------------------------------------------------------------------


def test_create_event_returns_bunkhouse_event():
    evt = create_event("task", "created")
    assert isinstance(evt, BunkhouseEvent)


def test_create_event_generates_uuid():
    evt = create_event("task", "created")
    assert len(evt.event_id) == 36, "event_id should be a UUID string"
    assert evt.event_id.count("-") == 4


def test_create_event_sets_occurred_at():
    evt = create_event("task", "created")
    assert evt.occurred_at.seconds > 0


def test_create_event_source_default():
    evt = create_event("task", "created")
    assert evt.source == "task.created"


def test_create_event_source_from_trace_context():
    ctx = {"source": "orchestrator"}
    evt = create_event("task", "created", trace_context=ctx)
    assert evt.source == "orchestrator"


def test_create_event_unique_event_ids():
    ids = {create_event("step", "updated").event_id for _ in range(10)}
    assert len(ids) == 10, "Each event should have a unique event_id"


# ---------------------------------------------------------------------------
# Helpers: to_sns_attributes
# ---------------------------------------------------------------------------


def test_to_sns_attributes_basic():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-123"))
    attrs = to_sns_attributes(evt)
    assert attrs["entity_type"]["StringValue"] == "task"
    assert attrs["action"]["StringValue"] == "created"
    assert attrs["schema_version"]["StringValue"] == __version__
    assert attrs["event_id"]["StringValue"] == evt.event_id


def test_to_sns_attributes_schema_version():
    evt = create_event("step", "started")
    attrs = to_sns_attributes(evt)
    assert attrs["schema_version"]["StringValue"] == __version__


def test_to_sns_attributes_no_payload():
    evt = create_event("repo", "updated")
    attrs = to_sns_attributes(evt)
    # entity_type should fall back to source prefix
    assert attrs["entity_type"]["StringValue"] == "repo"
    assert attrs["action"]["StringValue"] == "updated"


def test_to_sns_attributes_all_string_data_types():
    evt = create_event("task", "created")
    attrs = to_sns_attributes(evt)
    for key, val in attrs.items():
        assert val.get("DataType") in ("String", "Number"), (
            f"Unexpected DataType for {key}: {val}"
        )


# ---------------------------------------------------------------------------
# Helpers: serialize_for_sns / deserialize_from_sns
# ---------------------------------------------------------------------------


def test_serialize_returns_base64_string():
    evt = create_event("task", "created")
    serialized = serialize_for_sns(evt)
    assert isinstance(serialized, str)
    # Should be valid base64
    decoded = base64.b64decode(serialized)
    assert len(decoded) > 0


def test_roundtrip_serialize_deserialize():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-999", repo="owner/repo"))

    body = serialize_for_sns(evt)
    recovered = deserialize_from_sns(body)

    assert recovered.event_id == evt.event_id
    assert recovered.source == evt.source
    assert recovered.task.task_id == "t-999"
    assert recovered.task.repo == "owner/repo"


def test_deserialize_from_sns_returns_bunkhouse_event():
    evt = create_event("step", "completed")
    body = serialize_for_sns(evt)
    result = deserialize_from_sns(body)
    assert isinstance(result, BunkhouseEvent)


# ---------------------------------------------------------------------------
# Auto-version stamping
# ---------------------------------------------------------------------------


def _version_int(version_str: str) -> int:
    major, minor, patch = (int(p) for p in version_str.split("."))
    return major * 10000 + minor * 100 + patch


def test_serialize_stamps_schema_version():
    evt = create_event("task", "created")
    evt.SerializeToString()
    assert evt.schema_version == _version_int(__version__)


def test_schema_version_survives_roundtrip():
    evt = create_event("task", "created")
    body = serialize_for_sns(evt)
    recovered = deserialize_from_sns(body)
    assert recovered.schema_version == _version_int(__version__)


def test_schema_version_is_1_1_0():
    assert __version__ == "1.1.0"
    evt = create_event("task", "created")
    evt.SerializeToString()
    assert evt.schema_version == 10100
