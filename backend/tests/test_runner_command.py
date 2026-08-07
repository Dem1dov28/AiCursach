"""Regression tests for workflow runner edge cases."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langgraph.types import Command

from backend.application.workflow.runner import stream_workflow


def test_stream_workflow_accepts_command_resume_input():
    """Command(resume=…) must not be passed to dict() — caused 'Command' object is not iterable."""
    cmd = Command(resume={"selected_option": "A"})
    mock_engine = MagicMock()
    mock_engine.stream.return_value = iter([])
    mock_engine.get_state.return_value = MagicMock(values={"topic": "Test"})

    with patch("backend.application.workflow.runner._workflow", return_value=mock_engine):
        final_state, status = stream_workflow(cmd, thread_id="job-cmd-test")

    assert status == "completed"
    assert final_state.get("topic") == "Test"
    mock_engine.stream.assert_called_once()
    assert mock_engine.stream.call_args.args[0] is cmd
