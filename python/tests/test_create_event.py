"""Tests for the create_event helper.

Verifies that create_event:
- Returns a BunkhouseEvent.
- Generates a valid UUID event_id (unique per call).
- Sets occurred_at to a recent UTC timestamp.
- Encodes entity_type and action into the source field.
- Allows source to be overridden via trace_context.
"""

import re
import uuid
from datetime import datetime, timezone

import bunkhouse_protobuf  # noqa: F401 – triggers monkey-patch
from bunkhouse_protobuf.helpers import create_event
from bunkhouse.events.envelope_pb2 import BunkhouseEvent

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


def test_create_event_returns_bunkhouse_event():
    evt = create_event("task", "created")
    assert isinstance(evt, BunkhouseEvent)


# ---------------------------------------------------------------------------
# event_id – UUID generation
# ---------------------------------------------------------------------------


def test_create_event_generates_uuid_event_id():
    evt = create_event("task", "created")
    assert UUID_RE.match(evt.event_id), f"event_id is not a UUID: {evt.event_id!r}"


def test_create_event_event_id_parseable_as_uuid():
    evt = create_event("step", "started")
    parsed = uuid.UUID(evt.event_id)
    assert str(parsed) == evt.event_id


def test_create_event_unique_event_ids():
    ids = {create_event("task", "created").event_id for _ in range(20)}
    assert len(ids) == 20, "create_event must generate a unique event_id on each call"


def test_create_event_event_id_length():
    evt = create_event("task", "created")
    assert len(evt.event_id) == 36


def test_create_event_event_id_dash_count():
    evt = create_event("task", "created")
    assert evt.event_id.count("-") == 4


# ---------------------------------------------------------------------------
# occurred_at – timestamp
# ---------------------------------------------------------------------------


def test_create_event_sets_occurred_at():
    evt = create_event("task", "created")
    assert evt.occurred_at.seconds > 0, "occurred_at must be set to a real timestamp"


def test_create_event_occurred_at_is_recent():
    before = int(datetime.now(timezone.utc).timestamp())
    evt = create_event("task", "created")
    after = int(datetime.now(timezone.utc).timestamp())
    assert before <= evt.occurred_at.seconds <= after + 1, (
        "occurred_at should be within the current second"
    )


# ---------------------------------------------------------------------------
# source field
# ---------------------------------------------------------------------------


def test_create_event_source_combines_entity_and_action():
    evt = create_event("task", "created")
    assert evt.source == "task.created"


def test_create_event_source_step_started():
    evt = create_event("step", "started")
    assert evt.source == "step.started"


def test_create_event_source_repo_updated():
    evt = create_event("repo", "updated")
    assert evt.source == "repo.updated"


def test_create_event_source_override_via_trace_context():
    evt = create_event("task", "created", trace_context={"source": "orchestrator"})
    assert evt.source == "orchestrator"


def test_create_event_trace_context_none():
    """trace_context=None should use the default source convention."""
    evt = create_event("deployment", "created", trace_context=None)
    assert evt.source == "deployment.created"


def test_create_event_trace_context_empty_dict():
    """An empty trace_context should use the default source convention."""
    evt = create_event("github", "opened", trace_context={})
    assert evt.source == "github.opened"


# ---------------------------------------------------------------------------
# Payload is unset after creation (caller's responsibility)
# ---------------------------------------------------------------------------


def test_create_event_no_payload_set():
    evt = create_event("task", "created")
    assert evt.WhichOneof("payload") is None
