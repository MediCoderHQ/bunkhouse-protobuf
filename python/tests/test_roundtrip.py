"""Round-trip serialization tests for all 7 BunkhouseEvent payload types.

Each test builds an event with a representative payload, serializes it via
serialize_for_sns, deserializes via deserialize_from_sns, and verifies that
the envelope and payload fields survive the round-trip intact.
"""

import bunkhouse_protobuf  # noqa: F401 – triggers monkey-patch
from bunkhouse_protobuf.helpers import (
    create_event,
    deserialize_from_sns,
    serialize_for_sns,
)
from bunkhouse.events.task_pb2 import TaskEvent
from bunkhouse.events.step_pb2 import StepEvent
from bunkhouse.events.workflow_run_pb2 import WorkflowRunEvent
from bunkhouse.events.github_pb2 import GitHubEvent
from bunkhouse.events.deployment_pb2 import DeploymentEvent
from bunkhouse.events.workflow_def_pb2 import WorkflowDefinitionEvent
from bunkhouse.events.repo_pb2 import RepoEvent


# ---------------------------------------------------------------------------
# TaskEvent
# ---------------------------------------------------------------------------


def test_roundtrip_task_event():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(
        task_id="task-abc123",
        repo="owner/repo",
        epic_id="epic-1",
        workflow_id="wf-xyz",
        created_by="user-1",
    ))

    recovered = deserialize_from_sns(serialize_for_sns(evt))

    assert recovered.event_id == evt.event_id
    assert recovered.source == "task.created"
    assert recovered.task.task_id == "task-abc123"
    assert recovered.task.repo == "owner/repo"
    assert recovered.task.epic_id == "epic-1"
    assert recovered.task.workflow_id == "wf-xyz"
    assert recovered.task.created_by == "user-1"


# ---------------------------------------------------------------------------
# StepEvent
# ---------------------------------------------------------------------------


def test_roundtrip_step_event():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(
        task_id="task-abc",
        run_id="run-1",
        step_id="step-1",
        step_name="code-review",
        compute_type="claude",
        role_id="reviewer",
        repo="owner/repo",
        step_index=0,
    ))

    recovered = deserialize_from_sns(serialize_for_sns(evt))

    assert recovered.event_id == evt.event_id
    assert recovered.source == "step.started"
    assert recovered.step.task_id == "task-abc"
    assert recovered.step.run_id == "run-1"
    assert recovered.step.step_id == "step-1"
    assert recovered.step.step_name == "code-review"
    assert recovered.step.compute_type == "claude"
    assert recovered.step.role_id == "reviewer"
    assert recovered.step.repo == "owner/repo"
    assert recovered.step.step_index == 0


# ---------------------------------------------------------------------------
# WorkflowRunEvent
# ---------------------------------------------------------------------------


def test_roundtrip_workflow_run_event():
    evt = create_event("workflow_run", "created")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(
        task_id="task-wf-1",
        run_id="run-abc",
        workflow_id="wf-def",
        repo="owner/repo",
        trigger="http_task_create",
        trigger_event_id="evt-ext-1",
    ))

    recovered = deserialize_from_sns(serialize_for_sns(evt))

    assert recovered.event_id == evt.event_id
    assert recovered.source == "workflow_run.created"
    assert recovered.workflow_run.task_id == "task-wf-1"
    assert recovered.workflow_run.run_id == "run-abc"
    assert recovered.workflow_run.workflow_id == "wf-def"
    assert recovered.workflow_run.repo == "owner/repo"
    assert recovered.workflow_run.trigger == "http_task_create"
    assert recovered.workflow_run.trigger_event_id == "evt-ext-1"


# ---------------------------------------------------------------------------
# GitHubEvent
# ---------------------------------------------------------------------------


def test_roundtrip_github_event():
    evt = create_event("github", "opened")
    evt.github.CopyFrom(GitHubEvent(
        repo="owner/repo",
        pr_number=42,
        action="opened",
        branch="feature/my-feature",
        author="dev-user",
    ))

    recovered = deserialize_from_sns(serialize_for_sns(evt))

    assert recovered.event_id == evt.event_id
    assert recovered.source == "github.opened"
    assert recovered.github.repo == "owner/repo"
    assert recovered.github.pr_number == 42
    assert recovered.github.action == "opened"
    assert recovered.github.branch == "feature/my-feature"
    assert recovered.github.author == "dev-user"


# ---------------------------------------------------------------------------
# DeploymentEvent
# ---------------------------------------------------------------------------


def test_roundtrip_deployment_event():
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(
        deployment_id="deploy-001",
        repo="owner/repo",
        environment="production",
        service="api",
        commit_sha="abc123def456",
        pr_number=7,
    ))

    recovered = deserialize_from_sns(serialize_for_sns(evt))

    assert recovered.event_id == evt.event_id
    assert recovered.source == "deployment.created"
    assert recovered.deployment.deployment_id == "deploy-001"
    assert recovered.deployment.repo == "owner/repo"
    assert recovered.deployment.environment == "production"
    assert recovered.deployment.service == "api"
    assert recovered.deployment.commit_sha == "abc123def456"
    assert recovered.deployment.pr_number == 7


# ---------------------------------------------------------------------------
# WorkflowDefinitionEvent
# ---------------------------------------------------------------------------


def test_roundtrip_workflow_definition_event():
    evt = create_event("workflow_def", "registered")
    evt.workflow_def.CopyFrom(WorkflowDefinitionEvent(
        workflow_id="wf-code-review",
        description="Automated code review workflow",
    ))

    recovered = deserialize_from_sns(serialize_for_sns(evt))

    assert recovered.event_id == evt.event_id
    assert recovered.source == "workflow_def.registered"
    assert recovered.workflow_def.workflow_id == "wf-code-review"
    assert recovered.workflow_def.description == "Automated code review workflow"


# ---------------------------------------------------------------------------
# RepoEvent
# ---------------------------------------------------------------------------


def test_roundtrip_repo_event():
    evt = create_event("repo", "registered")
    evt.repo.CopyFrom(RepoEvent(
        repo="owner/new-repo",
        default_branch="main",
    ))

    recovered = deserialize_from_sns(serialize_for_sns(evt))

    assert recovered.event_id == evt.event_id
    assert recovered.source == "repo.registered"
    assert recovered.repo.repo == "owner/new-repo"
    assert recovered.repo.default_branch == "main"


# ---------------------------------------------------------------------------
# Envelope fields survive all round-trips
# ---------------------------------------------------------------------------


def test_roundtrip_preserves_occurred_at():
    evt = create_event("task", "updated")
    evt.task.CopyFrom(TaskEvent(task_id="t-1"))
    original_ts = evt.occurred_at.seconds

    recovered = deserialize_from_sns(serialize_for_sns(evt))

    assert recovered.occurred_at.seconds == original_ts


def test_roundtrip_preserves_schema_version():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-2"))
    body = serialize_for_sns(evt)

    recovered = deserialize_from_sns(body)

    assert recovered.schema_version == 10000
