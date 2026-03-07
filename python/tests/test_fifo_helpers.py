"""Tests for FIFO SNS helper functions: _extract_task_id and get_message_group_id.

Also covers the workflow_run additions to to_sns_attributes().
"""

import bunkhouse_protobuf  # noqa: F401 – triggers monkey-patch
from bunkhouse_protobuf.helpers import (
    _extract_task_id,
    create_event,
    get_message_group_id,
    to_sns_attributes,
)
from bunkhouse.events.task_pb2 import TaskEvent
from bunkhouse.events.step_pb2 import StepEvent
from bunkhouse.events.workflow_run_pb2 import WorkflowRunEvent
from bunkhouse.events.github_pb2 import GitHubEvent
from bunkhouse.events.deployment_pb2 import DeploymentEvent
from bunkhouse.events.workflow_def_pb2 import WorkflowDefinitionEvent
from bunkhouse.events.repo_pb2 import RepoEvent


# ---------------------------------------------------------------------------
# _extract_task_id
# ---------------------------------------------------------------------------


def test_extract_task_id_from_task():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="task-abc"))
    assert _extract_task_id(evt) == "task-abc"


def test_extract_task_id_from_step():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(task_id="task-xyz", step_id="s-1"))
    assert _extract_task_id(evt) == "task-xyz"


def test_extract_task_id_from_workflow_run():
    evt = create_event("workflow_run", "created")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(task_id="task-wfr", run_id="run-1"))
    assert _extract_task_id(evt) == "task-wfr"


def test_extract_task_id_no_payload():
    evt = create_event("repo", "updated")
    assert _extract_task_id(evt) == ""


def test_extract_task_id_github_event():
    evt = create_event("github", "push")
    evt.github.CopyFrom(GitHubEvent(repo="owner/repo"))
    assert _extract_task_id(evt) == ""


def test_extract_task_id_deployment_event():
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-1", repo="owner/repo"))
    assert _extract_task_id(evt) == ""


def test_extract_task_id_workflow_def_event():
    evt = create_event("workflow_def", "created")
    evt.workflow_def.CopyFrom(WorkflowDefinitionEvent(workflow_id="wf-1"))
    assert _extract_task_id(evt) == ""


def test_extract_task_id_empty_task_id():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(repo="owner/repo"))  # no task_id
    assert _extract_task_id(evt) == ""


# ---------------------------------------------------------------------------
# get_message_group_id – task/step/workflow_run → task_id
# ---------------------------------------------------------------------------


def test_message_group_id_task_returns_task_id():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="task-group-1"))
    assert get_message_group_id(evt) == "task-group-1"


def test_message_group_id_step_returns_task_id():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(task_id="task-group-2", step_id="s-1"))
    assert get_message_group_id(evt) == "task-group-2"


def test_message_group_id_workflow_run_returns_task_id():
    evt = create_event("workflow_run", "started")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(task_id="task-group-3", run_id="run-1"))
    assert get_message_group_id(evt) == "task-group-3"


# ---------------------------------------------------------------------------
# get_message_group_id – github/deployment/repo → repo
# ---------------------------------------------------------------------------


def test_message_group_id_github_returns_repo():
    evt = create_event("github", "push")
    evt.github.CopyFrom(GitHubEvent(repo="owner/myrepo", action="push"))
    assert get_message_group_id(evt) == "owner/myrepo"


def test_message_group_id_deployment_returns_repo():
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-1", repo="owner/deploy-repo"))
    assert get_message_group_id(evt) == "owner/deploy-repo"


def test_message_group_id_repo_event_returns_repo():
    evt = create_event("repo", "updated")
    evt.repo.CopyFrom(RepoEvent(repo="owner/repo-event"))
    assert get_message_group_id(evt) == "owner/repo-event"


# ---------------------------------------------------------------------------
# get_message_group_id – workflow_def → workflow_id
# ---------------------------------------------------------------------------


def test_message_group_id_workflow_def_returns_workflow_id():
    evt = create_event("workflow_def", "created")
    evt.workflow_def.CopyFrom(WorkflowDefinitionEvent(workflow_id="wf-deploy"))
    assert get_message_group_id(evt) == "wf-deploy"


# ---------------------------------------------------------------------------
# get_message_group_id – fallback → event_id
# ---------------------------------------------------------------------------


def test_message_group_id_fallback_to_event_id_no_payload():
    evt = create_event("unknown", "action")
    # No payload set → falls back to event_id
    assert get_message_group_id(evt) == evt.event_id


def test_message_group_id_fallback_task_without_task_id():
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(repo="owner/repo"))  # task_id empty
    assert get_message_group_id(evt) == evt.event_id


def test_message_group_id_fallback_step_without_task_id():
    evt = create_event("step", "started")
    evt.step.CopyFrom(StepEvent(step_id="s-1"))  # task_id empty
    assert get_message_group_id(evt) == evt.event_id


def test_message_group_id_fallback_workflow_run_without_task_id():
    evt = create_event("workflow_run", "created")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(run_id="run-1"))  # task_id empty
    assert get_message_group_id(evt) == evt.event_id


def test_message_group_id_fallback_github_without_repo():
    evt = create_event("github", "push")
    evt.github.CopyFrom(GitHubEvent(action="push"))  # repo empty
    assert get_message_group_id(evt) == evt.event_id


def test_message_group_id_fallback_deployment_without_repo():
    evt = create_event("deployment", "created")
    evt.deployment.CopyFrom(DeploymentEvent(deployment_id="d-1"))  # repo empty
    assert get_message_group_id(evt) == evt.event_id


def test_message_group_id_fallback_repo_without_repo():
    evt = create_event("repo", "updated")
    evt.repo.CopyFrom(RepoEvent(default_branch="main"))  # repo empty
    assert get_message_group_id(evt) == evt.event_id


def test_message_group_id_fallback_workflow_def_without_workflow_id():
    evt = create_event("workflow_def", "created")
    evt.workflow_def.CopyFrom(WorkflowDefinitionEvent(description="a workflow"))  # workflow_id empty
    assert get_message_group_id(evt) == evt.event_id


# ---------------------------------------------------------------------------
# get_message_group_id returns non-empty string
# ---------------------------------------------------------------------------


def test_message_group_id_always_non_empty():
    """get_message_group_id must always return a non-empty string."""
    evt = create_event("task", "created")
    evt.task.CopyFrom(TaskEvent(task_id="t-1"))
    assert get_message_group_id(evt) != ""


# ---------------------------------------------------------------------------
# to_sns_attributes: workflow_run additions
# ---------------------------------------------------------------------------


def test_workflow_run_task_id_in_sns_attributes():
    evt = create_event("workflow_run", "created")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(task_id="task-wfr-100", run_id="run-1", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    assert "task_id" in attrs
    assert attrs["task_id"]["StringValue"] == "task-wfr-100"


def test_workflow_run_repo_in_sns_attributes():
    evt = create_event("workflow_run", "created")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(task_id="task-wfr-101", run_id="run-2", repo="owner/wf-repo"))
    attrs = to_sns_attributes(evt)
    assert "repo" in attrs
    assert attrs["repo"]["StringValue"] == "owner/wf-repo"


def test_workflow_run_entity_type_in_sns_attributes():
    evt = create_event("workflow_run", "started")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(task_id="task-wfr-102", run_id="run-3"))
    attrs = to_sns_attributes(evt)
    assert attrs["entity_type"]["StringValue"] == "workflow_run"


def test_workflow_run_no_task_id_absent_from_attributes():
    evt = create_event("workflow_run", "created")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(run_id="run-4"))  # no task_id
    attrs = to_sns_attributes(evt)
    assert "task_id" not in attrs


def test_workflow_run_no_repo_absent_from_attributes():
    evt = create_event("workflow_run", "created")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(task_id="task-wfr-103", run_id="run-5"))  # no repo
    attrs = to_sns_attributes(evt)
    assert "repo" not in attrs


def test_workflow_run_all_string_data_types():
    evt = create_event("workflow_run", "created")
    evt.workflow_run.CopyFrom(WorkflowRunEvent(task_id="task-wfr-104", run_id="run-6", repo="owner/repo"))
    attrs = to_sns_attributes(evt)
    for key, val in attrs.items():
        assert val.get("DataType") == "String", (
            f"Expected DataType='String' for attribute '{key}', got {val!r}"
        )
