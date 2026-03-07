"""Helpers for building and transporting BunkhouseEvent messages via SNS."""

import base64
import uuid
from datetime import datetime, timezone
from typing import Optional

from bunkhouse.events.envelope_pb2 import BunkhouseEvent
from bunkhouse_protobuf._version import __version__


def create_event(
    entity_type: str,
    action: str,
    trace_context: Optional[dict] = None,
) -> BunkhouseEvent:
    """Build a BunkhouseEvent shell with envelope fields auto-populated.

    The caller is responsible for setting the appropriate payload field
    (e.g. ``evt.task.CopyFrom(task_event)``).

    Args:
        entity_type: Logical entity type, e.g. ``"task"``, ``"step"``.
        action:      Lifecycle action, e.g. ``"created"``, ``"updated"``.
        trace_context: Optional dict with extra context.  Supported keys:
            ``source`` – overrides the ``BunkhouseEvent.source`` field.

    Returns:
        A partially-populated :class:`BunkhouseEvent`.
    """
    ctx = trace_context or {}
    evt = BunkhouseEvent()
    evt.event_id = str(uuid.uuid4())
    evt.occurred_at.FromDatetime(datetime.now(timezone.utc))
    # Encode entity_type and action into source so to_sns_attributes can
    # surface them as SNS filter attributes.  A caller-supplied source
    # from trace_context takes precedence.
    evt.source = ctx.get("source", f"{entity_type}.{action}")
    return evt


def to_sns_attributes(event: BunkhouseEvent) -> dict:
    """Return an SNS ``MessageAttributes`` dict for *event*.

    The returned dict can be passed directly to ``boto3``'s
    ``SNS.publish(MessageAttributes=...)``.

    Derived attributes:
    - ``entity_type`` – from the set oneof payload field name; falls back to
      the first component of ``source`` if no payload is set.
    - ``action``       – second component of ``source`` when it has the form
      ``"entity_type.action"``.
    - ``schema_version`` – from the installed package version.
    - ``event_id``     – envelope UUID.
    - ``source``       – raw ``source`` field value.
    """
    payload_kind = event.WhichOneof("payload") or ""

    # Parse entity_type / action from the source field convention.
    source_parts = event.source.split(".", 1) if "." in event.source else []
    inferred_entity = source_parts[0] if source_parts else event.source
    inferred_action = source_parts[1] if len(source_parts) > 1 else ""

    entity_type = payload_kind or inferred_entity

    attrs: dict = {
        "entity_type": {"DataType": "String", "StringValue": entity_type},
        "schema_version": {"DataType": "String", "StringValue": __version__},
        "event_id": {"DataType": "String", "StringValue": event.event_id},
        "source": {"DataType": "String", "StringValue": event.source},
    }
    if inferred_action:
        attrs["action"] = {"DataType": "String", "StringValue": inferred_action}

    # Extract payload-specific fields for SNS filter routing.
    if payload_kind == "task":
        payload = event.task
        if payload.task_id:
            attrs["task_id"] = {"DataType": "String", "StringValue": payload.task_id}
        if payload.repo:
            attrs["repo"] = {"DataType": "String", "StringValue": payload.repo}
    elif payload_kind == "step":
        payload = event.step
        if payload.task_id:
            attrs["task_id"] = {"DataType": "String", "StringValue": payload.task_id}
        if payload.repo:
            attrs["repo"] = {"DataType": "String", "StringValue": payload.repo}
        if payload.compute_type:
            attrs["compute_type"] = {"DataType": "String", "StringValue": payload.compute_type}
    elif payload_kind == "deployment":
        payload = event.deployment
        if payload.repo:
            attrs["repo"] = {"DataType": "String", "StringValue": payload.repo}

    return attrs


def serialize_for_sns(event: BunkhouseEvent) -> str:
    """Serialize *event* to a base64-encoded string suitable for SNS.

    Calls :meth:`BunkhouseEvent.SerializeToString` (which auto-stamps
    ``schema_version``) and base64-encodes the result.
    """
    return base64.b64encode(event.SerializeToString()).decode("ascii")


def deserialize_from_sns(body: str) -> BunkhouseEvent:
    """Deserialize a :class:`BunkhouseEvent` from a base64-encoded SNS body.

    Args:
        body: The base64-encoded protobuf bytes (as produced by
              :func:`serialize_for_sns`).

    Returns:
        The deserialized :class:`BunkhouseEvent`.
    """
    raw = base64.b64decode(body)
    evt = BunkhouseEvent()
    evt.ParseFromString(raw)
    return evt
