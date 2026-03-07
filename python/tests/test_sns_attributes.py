"""Tests for to_sns_attributes helper.

Verifies that:
- entity_type, action, repo, task_id, compute_type are correctly extracted
  for task, step, and deployment events.
- DataType is "String" for all returned attributes.
- Attributes not applicable to an event type are absent.
"""

import bunkhouse_protobuf  # noqa: F401 – triggers monkey-patch
from bunkhouse_protobuf._version import __version__
from bunkhouse_protobuf.helpers import create_event, to_sns_attributes
from bunkhouse.events.task_pb2 import TaskEvent
from bunkhouse.events.step_pb2 import StepEvent
from bunkhouse.events.deployment_pb2 import DeploymentEvent


# ---------------------------------------------------------------------------
# TaskEvent attributes
# ---------------------------------------------------------------------------


def test_task_event_entity_type():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-100", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert attrs["entity_type"]["StringValue"] == "task"


def test_task_event_action():
    evt = create_event("task", "completed")
    evt.task.CopyFrom(TaskEvent(task_id="t-101"))
    attrs = to_sns_attributes(evt)
    assert attrs["action"]["StringValue"] == "completed"


def test_task_event_task_id():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="task-xyz", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert "task_id" in attrs
    assert attrs["task_id"]["StringValue"] == "task-xyz"


def test_task_event_repo():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-102", repo="myorg/myrepo"))
    attrs = to_sns_attributes(evt)
    assert "repo" in attrs
    assert attrs["repo"]["StringValue"] == "myorg/myrepo"


def test_task_event_no_compute_type():
    """Tasks do not have a compute_type field."""
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-103"))
    attrs = to_sns_attributes(evt)
    assert "compute_type" not in attrs


def test_task_event_schema_version():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-104"))
    attrs = to_sns_attributes(evt)
    assert attrs["schema_version"]["StringValue"] == __version__


def test_task_event_event_id():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-105"))
    attrs = to_sns_attributes(evt)
    assert attrs["event_id"]["StringValue"] == evt.event_id


# ---------------------------------------------------------------------------
# StepEvent attributes
# ---------------------------------------------------------------------------


def test_step_event_entity_type():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(task_id="t-200", compute_type="claude", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert attrs["entity_type"]["StringValue"] == "step"


def test_step_event_action():
    evt = create_event("step", "completed")
    evt.step.CopyFrom(StepEvent(step_id="s-1"))
    attrs = to_sns_attributes(evt)
    assert attrs["action"]["StringValue"] == "completed"


def test_step_event_task_id():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(task_id="task-step-1", compute_type="bash", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert "task_id" in attrs
    assert attrs["task_id"]["StringValue"] == "task-step-1"


def test_step_event_compute_type():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(task_id="t-201", compute_type="docker", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert "compute_type" in attrs
    assert attrs["compute_type"]["StringValue"] == "docker"


def test_step_event_repo():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(task_id="t-202", repo="myorg/myrepo", compute_type="claude"))
    attrs = to_sns_attributes(evt)
    assert "repo" in attrs
    assert attrs["repo"]["StringValue"] == "myorg/myrepo"


def test_step_event_no_compute_type_when_empty():
    """compute_type attribute is absent when StepEvent.compute_type is not set."""
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(task_id="t-203"))
    attrs = to_sns_attributes(evt)
    assert "compute_type" not in attrs


# ---------------------------------------------------------------------------
# DeploymentEvent attributes
# ---------------------------------------------------------------------------


def test_deployment_event_entity_type():
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-1", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert attrs["entity_type"]["StringValue"] == "deployment"


def test_deployment_event_action():
    evt = create_event("deployment", "updated")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-2"))
    attrs = to_sns_attributes(evt)
    assert attrs["action"]["StringValue"] == "updated"


def test_deployment_event_repo():
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-3", repo="owner/deploy-repo"))
    attrs = to_sns_attributes(evt)
    assert "repo" in attrs
    assert attrs["repo"]["StringValue"] == "owner/deploy-repo"


def test_deployment_event_no_task_id():
    """DeploymentEvent does not have a task_id attribute."""
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-4", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert "task_id" not in attrs


def test_deployment_event_no_compute_type():
    """DeploymentEvent does not have a compute_type attribute."""
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-5", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert "compute_type" not in attrs


# ---------------------------------------------------------------------------
# All DataType values must be "String"
# ---------------------------------------------------------------------------


def _assert_all_string(attrs: dict) -> None:
    for key, val in attrs.items():
        assert val.get("DataType") == "String", (
            f"Expected DataType='String' for attribute '{key}', got {val!r}"
        )


def test_task_event_all_string_data_types():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-300", repo="owner/repo"))
    _assert_all_string(to_sns_attributes(evt))


def test_step_event_all_string_data_types():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(task_id="t-301", compute_type="claude", repo="owner/repo"))
    _assert_all_string(to_sns_attributes(evt))


def test_deployment_event_all_string_data_types():
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-300", repo="owner/repo"))
    _assert_all_string(to_sns_attributes(evt))
