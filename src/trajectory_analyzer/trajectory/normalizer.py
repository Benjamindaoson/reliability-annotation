"""
Trajectory normalization module.

Converts raw OSWorld trajectory data into the unified Trajectory schema.
Handles missing fields, format variations, and data validation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

from .schema import (
    ActionInfo,
    CandidateSignal,
    EnvironmentFeedback,
    EvaluatorResult,
    EvaluatorSignal,
    ObservationInfo,
    ReasoningInfo,
    Trajectory,
    TrajectoryMetadata,
    TrajectoryStep,
)

logger = logging.getLogger(__name__)


class NormalizationWarning:
    """Container for normalization warnings."""
    def __init__(self, trajectory_id: str):
        self.trajectory_id = trajectory_id
        self.warnings: list[str] = []

    def add(self, message: str):
        self.warnings.append(f"[{self.trajectory_id}] {message}")
        logger.warning(f"[{self.trajectory_id}] {message}")

    def get_warnings(self) -> list[str]:
        return self.warnings


class TrajectoryNormalizer:
    """
    Normalizes raw trajectory data into the unified schema.

    Supports various input formats and handles missing fields gracefully.
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the normalizer.

        Args:
            strict_mode: If True, raise exceptions on missing critical fields.
                        If False, generate warnings and use defaults.
        """
        self.strict_mode = strict_mode
        self.warnings: list[str] = []

    def normalize(self, raw_episode: dict[str, Any]) -> tuple[Trajectory, NormalizationWarning]:
        """
        Normalize a raw episode into a Trajectory.

        Args:
            raw_episode: Raw trajectory data from OSWorld

        Returns:
            Tuple of (normalized Trajectory, warnings)

        Raises:
            ValueError: If critical fields are missing in strict mode.
        """
        warning = NormalizationWarning(raw_episode.get("trajectory_id", "unknown"))

        # Extract metadata
        metadata = self._normalize_metadata(raw_episode, warning)

        # Extract steps
        steps = self._normalize_steps(raw_episode.get("steps", []), warning)

        # Extract final result
        final_success = self._normalize_final_result(raw_episode, warning)

        # Build trajectory
        trajectory = Trajectory(
            metadata=metadata,
            steps=steps,
            final_success=final_success,
            final_score=raw_episode.get("final_score"),
            raw_metadata=raw_episode,
            original_format=self._detect_format(raw_episode),
        )

        return trajectory, warning

    def _normalize_metadata(
        self,
        raw_episode: dict[str, Any],
        warning: NormalizationWarning
    ) -> TrajectoryMetadata:
        """Normalize trajectory metadata."""
        traj_id = raw_episode.get("trajectory_id") or raw_episode.get("id") or raw_episode.get("instance_id")

        if not traj_id:
            warning.add("Missing trajectory_id, using 'unknown'")
            traj_id = "unknown"

        task_id = raw_episode.get("task_id") or raw_episode.get("instance_id")
        if not task_id:
            warning.add("Missing task_id")
            task_id = "unknown"

        model_id = raw_episode.get("model_id") or raw_episode.get("model")
        if not model_id:
            warning.add("Missing model_id")
            model_id = "unknown"

        return TrajectoryMetadata(
            trajectory_id=str(traj_id),
            task_id=str(task_id),
            model_id=str(model_id),
            model_name=raw_episode.get("model_name"),
            task_description=raw_episode.get("task_description"),
            task_category=raw_episode.get("task_category"),
            task_difficulty=raw_episode.get("difficulty"),
            environment=raw_episode.get("environment"),
            start_time=raw_episode.get("start_time"),
            end_time=raw_episode.get("end_time"),
            total_duration_seconds=raw_episode.get("duration"),
            data_source=raw_episode.get("data_source"),
            source_file=raw_episode.get("source_file"),
        )

    def _normalize_steps(
        self,
        raw_steps: list[dict[str, Any]],
        warning: NormalizationWarning
    ) -> list[TrajectoryStep]:
        """Normalize trajectory steps."""
        if not raw_steps:
            warning.add("No steps found in trajectory")
            return []

        steps = []
        for i, raw_step in enumerate(raw_steps):
            try:
                step = self._normalize_single_step(raw_step, i, warning)
                steps.append(step)
            except Exception as e:
                warning.add(f"Failed to normalize step {i}: {e}")
                if self.strict_mode:
                    raise

        return steps

    def _normalize_single_step(
        self,
        raw_step: dict[str, Any],
        step_id: int,
        warning: NormalizationWarning
    ) -> TrajectoryStep:
        """Normalize a single step."""
        # Observation
        observation = self._normalize_observation(raw_step.get("observation", {}), warning)

        # Action
        action = self._normalize_action(raw_step.get("action", {}), warning)

        # Reasoning
        reasoning = self._normalize_reasoning(raw_step.get("reasoning", {}), warning)

        # Environment feedback
        feedback = self._normalize_feedback(raw_step.get("feedback", {}), warning)

        # Evaluator signal
        evaluator = self._normalize_evaluator(raw_step.get("evaluator", {}), warning)

        return TrajectoryStep(
            step_id=step_id,
            observation=observation,
            action=action,
            reasoning=reasoning,
            environment_feedback=feedback,
            evaluator_signal=evaluator,
            timestamp=raw_step.get("timestamp"),
            duration_seconds=raw_step.get("duration"),
            raw_data=raw_step,
        )

    def _normalize_observation(
        self,
        raw_obs: dict[str, Any],
        warning: NormalizationWarning
    ) -> ObservationInfo:
        """Normalize observation data."""
        if not raw_obs:
            warning.add("Step has no observation data")
            return ObservationInfo()

        return ObservationInfo(
            screenshot=raw_obs.get("screenshot") or raw_obs.get("image"),
            text_state=raw_obs.get("text_state") or raw_obs.get("observation"),
            accessibility_state=raw_obs.get("accessibility_tree") or raw_obs.get("a11y_tree"),
            history_summary=raw_obs.get("history"),
            hidden_state=raw_obs.get("hidden_state"),
        )

    def _normalize_action(
        self,
        raw_action: dict[str, Any],
        warning: NormalizationWarning
    ) -> ActionInfo:
        """Normalize action data."""
        if not raw_action:
            warning.add("Step has no action data")
            return ActionInfo(action_type="unknown")

        # Handle different action formats
        action_type = raw_action.get("action_type") or raw_action.get("type") or raw_action.get("action")
        if not action_type:
            warning.add("Action has no type field")
            action_type = "unknown"

        return ActionInfo(
            action_type=str(action_type),
            action_arguments=raw_action.get("args") or raw_action.get("arguments") or {},
            raw_action=raw_action.get("raw") or raw_action.get("raw_action"),
            predicted_outcome=raw_action.get("predicted_outcome"),
        )

    def _normalize_reasoning(
        self,
        raw_reasoning: Union[dict[str, Any], str],
        warning: NormalizationWarning
    ) -> ReasoningInfo:
        """Normalize reasoning data."""
        if not raw_reasoning:
            warning.add("Step has no reasoning trace")
            return ReasoningInfo()

        # Handle string format
        if isinstance(raw_reasoning, str):
            return ReasoningInfo(
                reasoning_trace=raw_reasoning,
                uncertainty_expressed=self._contains_uncertainty(raw_reasoning),
            )

        # Handle dict format
        trace = raw_reasoning.get("trace") or raw_reasoning.get("reasoning") or raw_reasoning.get("thought")
        if not trace:
            warning.add("Reasoning dict has no trace field")

        return ReasoningInfo(
            reasoning_trace=trace,
            reasoning_summary=raw_reasoning.get("summary"),
            confidence=raw_reasoning.get("confidence"),
            uncertainty_expressed=self._contains_uncertainty(str(trace or "")),
        )

    def _normalize_feedback(
        self,
        raw_feedback: dict[str, Any],
        warning: NormalizationWarning
    ) -> EnvironmentFeedback:
        """Normalize environment feedback."""
        if not raw_feedback:
            return EnvironmentFeedback()

        return EnvironmentFeedback(
            feedback_text=raw_feedback.get("text") or raw_feedback.get("message"),
            state_changed=raw_feedback.get("state_changed", True),
            error_message=raw_feedback.get("error"),
            execution_success=raw_feedback.get("success", True),
        )

    def _normalize_evaluator(
        self,
        raw_eval: dict[str, Any],
        warning: NormalizationWarning
    ) -> Optional[EvaluatorSignal]:
        """Normalize evaluator signal."""
        if not raw_eval:
            return None

        result_str = raw_eval.get("result", "unknown")
        try:
            result = EvaluatorResult(result_str)
        except ValueError:
            warning.add(f"Unknown evaluator result: {result_str}")
            result = EvaluatorResult.UNKNOWN

        return EvaluatorSignal(
            result=result,
            score=raw_eval.get("score"),
            partial_credit=raw_eval.get("partial_credit"),
            feedback=raw_eval.get("feedback"),
            step_metrics=raw_eval.get("metrics"),
        )

    def _normalize_final_result(
        self,
        raw_episode: dict[str, Any],
        warning: NormalizationWarning
    ) -> EvaluatorResult:
        """Normalize final trajectory result."""
        # Check for boolean success field first
        if "success" in raw_episode:
            success_val = raw_episode["success"]
            if isinstance(success_val, bool):
                return EvaluatorResult.SUCCESS if success_val else EvaluatorResult.FAILURE
            if isinstance(success_val, str):
                try:
                    return EvaluatorResult(success_val.lower())
                except ValueError:
                    pass

        # Check for string result fields
        for key in ["final_result", "result", "evaluator_result"]:
            result_str = raw_episode.get(key)
            if result_str and isinstance(result_str, str):
                try:
                    return EvaluatorResult(result_str.lower())
                except ValueError:
                    pass

        warning.add("No success or result field found")
        return EvaluatorResult.UNKNOWN

    def _detect_format(self, raw_episode: dict[str, Any]) -> str:
        """Detect the original data format."""
        # Check for OSWorld format markers
        if "history" in raw_episode:
            return "osworld_v1"
        if "instance_id" in raw_episode and "trajectory_id" not in raw_episode:
            return "osworld_instances"
        if "trajectory" in raw_episode and "steps" in raw_episode.get("trajectory", {}):
            return "osworld_wrapped"

        return "unknown"

    def _contains_uncertainty(self, text: str) -> bool:
        """Check if text contains uncertainty language."""
        uncertainty_markers = [
            "not sure", "uncertain", "might", "maybe", "perhaps",
            "could be", "not certain", "unclear", "ambiguous",
            "not sure if", "not sure whether", "don't know",
            "cannot determine", "unable to", "failed", "error",
            "mistake", "wrong", "incorrect", "issue", "problem",
        ]
        text_lower = text.lower()
        return any(marker in text_lower for marker in uncertainty_markers)


def normalize_trajectory(raw_episode: dict[str, Any]) -> tuple[Trajectory, list[str]]:
    """
    Convenience function to normalize a single trajectory.

    Args:
        raw_episode: Raw trajectory data

    Returns:
        Tuple of (Trajectory, list of warning messages)
    """
    normalizer = TrajectoryNormalizer()
    trajectory, warning = normalizer.normalize(raw_episode)
    return trajectory, warning.get_warnings()


def normalize_trajectories(
    raw_episodes: list[dict[str, Any]]
) -> tuple[list[Trajectory], list[NormalizationWarning]]:
    """
    Normalize multiple trajectories.

    Args:
        raw_episodes: List of raw trajectory data

    Returns:
        Tuple of (list of Trajectories, list of warnings per trajectory)
    """
    normalizer = TrajectoryNormalizer()
    trajectories = []
    all_warnings = []

    for episode in raw_episodes:
        trajectory, warning = normalizer.normalize(episode)
        trajectories.append(trajectory)
        all_warnings.append(warning)

    return trajectories, all_warnings
