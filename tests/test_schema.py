"""
Tests for trajectory schema.
"""

import pytest
from dataclasses import asdict

from src.trajectory_analyzer.trajectory.schema import (
    ActionInfo,
    CandidateSignal,
    EnvironmentFeedback,
    EvaluatorResult,
    EvaluatorSignal,
    FailureType,
    ObservationInfo,
    ReasoningInfo,
    Trajectory,
    TrajectoryMetadata,
    TrajectoryStep,
)


class TestActionInfo:
    def test_basic_creation(self):
        action = ActionInfo(action_type="click", action_arguments={"x": 100, "y": 200})
        assert action.action_type == "click"
        assert action.action_arguments == {"x": 100, "y": 200}

    def test_defaults(self):
        action = ActionInfo(action_type="noop")
        assert action.action_type == "noop"
        assert action.action_arguments == {}
        assert action.raw_action is None


class TestObservationInfo:
    def test_basic_creation(self):
        obs = ObservationInfo(
            screenshot="base64data...",
            text_state="Desktop with file manager open",
        )
        assert obs.screenshot == "base64data..."
        assert obs.text_state == "Desktop with file manager open"

    def test_empty_observation(self):
        obs = ObservationInfo()
        assert obs.screenshot is None
        assert obs.text_state is None


class TestReasoningInfo:
    def test_reasoning_with_uncertainty(self):
        reasoning = ReasoningInfo(
            reasoning_trace="I should click the button, but I'm not sure if it's the right one.",
            uncertainty_expressed=True,
        )
        assert reasoning.uncertainty_expressed is True

    def test_reasoning_confidence(self):
        reasoning = ReasoningInfo(
            reasoning_trace="This is the correct file.",
            confidence=0.95,
        )
        assert reasoning.confidence == 0.95


class TestEnvironmentFeedback:
    def test_success_feedback(self):
        feedback = EnvironmentFeedback(
            feedback_text="File saved successfully",
            state_changed=True,
            execution_success=True,
        )
        assert feedback.execution_success is True
        assert feedback.state_changed is True

    def test_error_feedback(self):
        feedback = EnvironmentFeedback(
            feedback_text="Permission denied",
            state_changed=False,
            execution_success=False,
            error_message="Access denied",
        )
        assert feedback.execution_success is False
        assert feedback.error_message == "Access denied"


class TestEvaluatorSignal:
    def test_success_result(self):
        signal = EvaluatorSignal(
            result=EvaluatorResult.SUCCESS,
            score=1.0,
        )
        assert signal.result == EvaluatorResult.SUCCESS
        assert signal.score == 1.0

    def test_partial_credit(self):
        signal = EvaluatorSignal(
            result=EvaluatorResult.INCOMPLETE,
            partial_credit=0.5,
        )
        assert signal.result == EvaluatorResult.INCOMPLETE
        assert signal.partial_credit == 0.5


class TestTrajectoryStep:
    def test_step_creation(self):
        step = TrajectoryStep(step_id=0, action=ActionInfo(action_type="noop"))
        assert step.step_id == 0
        assert step.observation is not None
        assert step.action is not None
        assert step.reasoning is not None

    def test_step_with_all_fields(self):
        step = TrajectoryStep(
            step_id=5,
            observation=ObservationInfo(text_state="Test state"),
            action=ActionInfo(action_type="type", action_arguments={"text": "hello"}),
            reasoning=ReasoningInfo(reasoning_trace="Typing hello"),
            environment_feedback=EnvironmentFeedback(execution_success=True),
            duration_seconds=2.5,
        )
        assert step.step_id == 5
        assert step.observation.text_state == "Test state"
        assert step.action.action_type == "type"
        assert step.duration_seconds == 2.5


class TestTrajectoryMetadata:
    def test_metadata_creation(self):
        metadata = TrajectoryMetadata(
            trajectory_id="traj_001",
            task_id="task_file_edit",
            model_id="claude-3-sonnet",
        )
        assert metadata.trajectory_id == "traj_001"
        assert metadata.task_id == "task_file_edit"

    def test_metadata_with_all_fields(self):
        metadata = TrajectoryMetadata(
            trajectory_id="traj_002",
            task_id="task_calculator",
            model_id="gpt-4o",
            model_name="GPT-4 Omni",
            task_category="productivity",
            task_difficulty="medium",
            environment="osworld",
        )
        assert metadata.task_category == "productivity"
        assert metadata.environment == "osworld"


class TestTrajectory:
    def test_empty_trajectory(self):
        metadata = TrajectoryMetadata(
            trajectory_id="traj_empty",
            task_id="task_test",
            model_id="model_x",
        )
        trajectory = Trajectory(metadata=metadata, steps=[])
        assert len(trajectory.steps) == 0
        assert trajectory.trajectory_length == 0

    def test_trajectory_with_steps(self):
        metadata = TrajectoryMetadata(
            trajectory_id="traj_003",
            task_id="task_test",
            model_id="model_x",
        )
        steps = [
            TrajectoryStep(step_id=0, action=ActionInfo(action_type="noop")),
            TrajectoryStep(step_id=1, action=ActionInfo(action_type="noop")),
            TrajectoryStep(step_id=2, action=ActionInfo(action_type="noop")),
        ]
        trajectory = Trajectory(metadata=metadata, steps=steps)
        assert trajectory.trajectory_length == 3

    def test_get_step(self):
        metadata = TrajectoryMetadata(
            trajectory_id="traj_004",
            task_id="task_test",
            model_id="model_x",
        )
        steps = [
            TrajectoryStep(step_id=0, action=ActionInfo(action_type="noop")),
            TrajectoryStep(step_id=1, action=ActionInfo(action_type="noop")),
            TrajectoryStep(step_id=2, action=ActionInfo(action_type="noop")),
        ]
        trajectory = Trajectory(metadata=metadata, steps=steps)

        step = trajectory.get_step(1)
        assert step is not None
        assert step.step_id == 1

        missing = trajectory.get_step(99)
        assert missing is None

    def test_reasoning_coverage(self):
        metadata = TrajectoryMetadata(
            trajectory_id="traj_005",
            task_id="task_test",
            model_id="model_x",
        )
        steps = [
            TrajectoryStep(
                step_id=0,
                action=ActionInfo(action_type="noop"),
                reasoning=ReasoningInfo(reasoning_trace="First thought"),
            ),
            TrajectoryStep(step_id=1, action=ActionInfo(action_type="noop")),  # No reasoning
            TrajectoryStep(
                step_id=2,
                action=ActionInfo(action_type="noop"),
                reasoning=ReasoningInfo(reasoning_trace="Second thought"),
            ),
        ]
        trajectory = Trajectory(metadata=metadata, steps=steps)
        assert trajectory.reasoning_coverage == pytest.approx(2/3)


class TestCandidateSignal:
    def test_signal_creation(self):
        signal = CandidateSignal(
            signal_type="repeated_action",
            confidence=0.8,
            description="Same action repeated 3 times",
        )
        assert signal.signal_type == "repeated_action"
        assert signal.confidence == 0.8

    def test_signal_with_evidence(self):
        signal = CandidateSignal(
            signal_type="task_failed",
            confidence=0.9,
            description="Task failed after this step",
            evidence={"evaluator_result": "failure"},
        )
        assert signal.evidence["evaluator_result"] == "failure"


class TestFailureType:
    def test_failure_types(self):
        assert FailureType.SELECTION.value == "selection"
        assert FailureType.EXECUTION.value == "execution"
        assert FailureType.RECOGNITION.value == "recognition"
        assert FailureType.RECOVERY.value == "recovery"
        assert FailureType.UNKNOWN.value == "unknown"


class TestEvaluatorResult:
    def test_evaluator_results(self):
        assert EvaluatorResult.SUCCESS.value == "success"
        assert EvaluatorResult.FAILURE.value == "failure"
        assert EvaluatorResult.INCOMPLETE.value == "incomplete"
        assert EvaluatorResult.UNKNOWN.value == "unknown"
