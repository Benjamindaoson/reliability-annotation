"""
Candidate failure localization module.

Identifies potential failure points in trajectories based on heuristic signals.
Note: This is NOT failure classification - just candidate identification.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..trajectory.normalizer import normalize_trajectory
from ..trajectory.schema import CandidateSignal, Trajectory, TrajectoryStep

logger = logging.getLogger(__name__)


# Signal types for candidate failure identification
class SignalType:
    """Types of failure candidate signals."""
    # Evaluator-based signals
    TASK_FAILED_AFTER_STEP = "task_failed_after_step"
    PARTIAL_SCORE_DECREASE = "partial_score_decrease"

    # State-based signals
    STATE_NO_CHANGE = "state_no_change"
    STATE_INCONSISTENCY = "state_inconsistency"
    OBSERVABLE_ERROR = "observable_error"

    # Action-based signals
    REPEATED_ACTION = "repeated_action"
    LONG_ACTION_LOOP = "long_action_loop"
    UNCHANGED_ARGUMENT = "unchanged_argument"

    # Reasoning-based signals
    REASONING_UNCERTAINTY = "reasoning_uncertainty"
    REASONING_BACKTRACK = "reasoning_backtrack"
    REASONING_CONTRADICTION = "reasoning_contradiction"

    # Position-based signals
    FINAL_STEP_PROXIMITY = "final_step_proximity"
    MANY_STEPS_AFTER_FAILURE = "many_steps_after_failure"

    # Feedback-based signals
    ENVIRONMENT_ERROR = "environment_error"
    EXECUTION_FAILURE = "execution_failure"


@dataclass
class CandidateFailureStep:
    """A step identified as a candidate failure point."""
    step_id: int
    signals: list[str] = field(default_factory=list)
    signal_details: list[dict] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "step": self.step_id,
            "signals": self.signals,
            "signal_details": self.signal_details,
            "confidence": self.confidence,
        }


@dataclass
class TrajectoryCandidateResult:
    """Candidate failure identification result for a single trajectory."""
    trajectory_id: str
    task_id: str
    model_id: str
    trajectory_length: int
    candidate_steps: list[CandidateFailureStep] = field(default_factory=list)
    failure_proximity_steps: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "trajectory_id": self.trajectory_id,
            "task_id": self.task_id,
            "model_id": self.model_id,
            "trajectory_length": self.trajectory_length,
            "candidate_steps": [s.to_dict() for s in self.candidate_steps],
            "failure_proximity_steps": self.failure_proximity_steps,
            "num_candidates": len(self.candidate_steps),
        }


class FailureCandidateAnalyzer:
    """
    Analyzes trajectories to identify candidate failure points.

    IMPORTANT: This module identifies SUSPECTED failure points using heuristics.
    It does NOT classify failures - that requires human annotation.
    """

    def __init__(self, uncertainty_threshold: float = 0.3):
        """
        Initialize the analyzer.

        Args:
            uncertainty_threshold: Fraction of reasoning markers that triggers
                                 the uncertainty signal.
        """
        self.uncertainty_threshold = uncertainty_threshold

    def analyze(self, trajectory: Trajectory) -> TrajectoryCandidateResult:
        """
        Analyze a trajectory for candidate failure points.

        Args:
            trajectory: A normalized Trajectory object.

        Returns:
            TrajectoryCandidateResult with identified candidates.
        """
        result = TrajectoryCandidateResult(
            trajectory_id=trajectory.metadata.trajectory_id,
            task_id=trajectory.metadata.task_id,
            model_id=trajectory.metadata.model_id,
            trajectory_length=len(trajectory.steps),
        )

        if not trajectory.steps:
            return result

        # Run all detection methods
        self._check_repeated_actions(trajectory, result)
        self._check_state_changes(trajectory, result)
        self._check_reasoning_uncertainty(trajectory, result)
        self._check_final_step_proximity(trajectory, result)
        self._check_environment_errors(trajectory, result)
        self._check_failed_trajectories(trajectory, result)

        # Sort candidates by confidence
        result.candidate_steps.sort(key=lambda x: x.confidence, reverse=True)

        return result

    def analyze_raw(self, raw_trajectory: dict[str, Any]) -> TrajectoryCandidateResult:
        """Analyze a raw trajectory dictionary."""
        trajectory, warnings = normalize_trajectory(raw_trajectory)
        return self.analyze(trajectory)

    def _add_candidate(
        self,
        result: TrajectoryCandidateResult,
        step_id: int,
        signal_type: str,
        confidence: float,
        details: Optional[dict] = None
    ):
        """Add a candidate signal to a step."""
        # Find or create the candidate for this step
        candidate = None
        for c in result.candidate_steps:
            if c.step_id == step_id:
                candidate = c
                break

        if candidate is None:
            candidate = CandidateFailureStep(step_id=step_id)
            result.candidate_steps.append(candidate)

        # Add signal if not already present
        if signal_type not in candidate.signals:
            candidate.signals.append(signal_type)
            candidate.signal_details.append({
                "signal": signal_type,
                "confidence": confidence,
                "details": details or {},
            })

        # Update confidence (max of all signals)
        candidate.confidence = max(candidate.confidence, confidence)

    def _check_repeated_actions(
        self,
        trajectory: Trajectory,
        result: TrajectoryCandidateResult
    ):
        """Detect repeated or looping actions."""
        action_counts: dict[str, list[int]] = {}

        for step in trajectory.steps:
            action_key = self._get_action_key(step)
            if action_key not in action_counts:
                action_counts[action_key] = []
            action_counts[action_key].append(step.step_id)

        # Check for repeated actions
        for action_key, step_ids in action_counts.items():
            if len(step_ids) >= 3:
                # Multiple occurrences of the same action
                for step_id in step_ids:
                    self._add_candidate(
                        result,
                        step_id,
                        SignalType.REPEATED_ACTION,
                        confidence=0.5,
                        details={"action": action_key, "occurrences": len(step_ids)}
                    )

        # Check for action loops (consecutive same actions)
        for i in range(len(trajectory.steps) - 2):
            current_action = self._get_action_key(trajectory.steps[i])
            if all(
                self._get_action_key(trajectory.steps[j]) == current_action
                for j in range(i, min(i + 3, len(trajectory.steps)))
            ):
                for j in range(i, min(i + 3, len(trajectory.steps))):
                    self._add_candidate(
                        result,
                        j,
                        SignalType.LONG_ACTION_LOOP,
                        confidence=0.6,
                        details={"action": current_action, "loop_start": i}
                    )

    def _check_state_changes(
        self,
        trajectory: Trajectory,
        result: TrajectoryCandidateResult
    ):
        """Detect steps where state doesn't change."""
        for i in range(1, len(trajectory.steps)):
            prev_step = trajectory.steps[i - 1]
            curr_step = trajectory.steps[i]

            # Check if environment feedback indicates no state change
            if not curr_step.environment_feedback.state_changed:
                self._add_candidate(
                    result,
                    i,
                    SignalType.STATE_NO_CHANGE,
                    confidence=0.7,
                    details={"feedback": curr_step.environment_feedback.feedback_text}
                )

    def _check_reasoning_uncertainty(
        self,
        trajectory: Trajectory,
        result: TrajectoryCandidateResult
    ):
        """Detect reasoning with uncertainty markers."""
        uncertainty_markers = [
            "not sure", "uncertain", "might", "maybe", "perhaps",
            "could be", "not certain", "unclear", "ambiguous",
            "don't know", "cannot determine", "unable to",
        ]

        for step in trajectory.steps:
            reasoning = step.reasoning.reasoning_trace
            if not reasoning:
                continue

            reasoning_lower = reasoning.lower()
            matches = sum(1 for m in uncertainty_markers if m in reasoning_lower)
            marker_ratio = matches / len(uncertainty_markers)

            if marker_ratio >= self.uncertainty_threshold:
                self._add_candidate(
                    result,
                    step.step_id,
                    SignalType.REASONING_UNCERTAINTY,
                    confidence=0.6,
                    details={"marker_count": matches, "ratio": marker_ratio}
                )

    def _check_final_step_proximity(
        self,
        trajectory: Trajectory,
        result: TrajectoryCandidateResult
    ):
        """Mark steps near the end of failed trajectories."""
        if trajectory.final_success.value == "failure":
            # Last 20% of steps are near the end
            threshold = max(1, len(trajectory.steps) // 5)

            for i, step in enumerate(trajectory.steps):
                proximity_ratio = i / len(trajectory.steps)
                if proximity_ratio >= 0.8:
                    self._add_candidate(
                        result,
                        i,
                        SignalType.FINAL_STEP_PROXIMITY,
                        confidence=0.4,
                        details={"proximity": proximity_ratio}
                    )

    def _check_environment_errors(
        self,
        trajectory: Trajectory,
        result: TrajectoryCandidateResult
    ):
        """Detect environment or execution errors."""
        for step in trajectory.steps:
            # Check environment feedback for errors
            if step.environment_feedback.error_message:
                self._add_candidate(
                    result,
                    step.step_id,
                    SignalType.ENVIRONMENT_ERROR,
                    confidence=0.9,
                    details={"error": step.environment_feedback.error_message}
                )

            # Check execution success
            if not step.environment_feedback.execution_success:
                self._add_candidate(
                    result,
                    step.step_id,
                    SignalType.EXECUTION_FAILURE,
                    confidence=0.8,
                    details={}
                )

    def _check_failed_trajectories(
        self,
        trajectory: Trajectory,
        result: TrajectoryCandidateResult
    ):
        """For failed trajectories, identify where failure might have occurred."""
        if trajectory.final_success.value != "failure":
            return

        # For failed trajectories, the last step is a strong candidate
        if trajectory.steps:
            last_step = trajectory.steps[-1]
            self._add_candidate(
                result,
                last_step.step_id,
                SignalType.TASK_FAILED_AFTER_STEP,
                confidence=0.8,
                details={"reason": "final_step_of_failed_trajectory"}
            )

            # The step before the last is also suspicious
            if len(trajectory.steps) >= 2:
                second_last = trajectory.steps[-2]
                self._add_candidate(
                    result,
                    second_last.step_id,
                    SignalType.TASK_FAILED_AFTER_STEP,
                    confidence=0.5,
                    details={"reason": "before_final_step"}
                )

    def _get_action_key(self, step: TrajectoryStep) -> str:
        """Get a normalized action key for comparison."""
        action = step.action
        args_str = str(sorted(action.action_arguments.items()))
        return f"{action.action_type}:{args_str}"


class BatchCandidateAnalyzer:
    """Analyzes multiple trajectories for candidates."""

    def __init__(self):
        self.analyzer = FailureCandidateAnalyzer()
        self.results: list[TrajectoryCandidateResult] = []

    def analyze_trajectories(
        self,
        trajectories: list[dict[str, Any]]
    ) -> list[TrajectoryCandidateResult]:
        """Analyze multiple raw trajectories."""
        self.results = []

        for raw_trajectory in trajectories:
            result = self.analyzer.analyze_raw(raw_trajectory)
            self.results.append(result)

        return self.results

    def get_high_confidence_candidates(
        self,
        threshold: float = 0.7
    ) -> list[tuple[str, int, float]]:
        """Get high-confidence candidates across all trajectories.

        Returns:
            List of (trajectory_id, step_id, confidence) tuples.
        """
        candidates = []

        for result in self.results:
            for step in result.candidate_steps:
                if step.confidence >= threshold:
                    candidates.append((
                        result.trajectory_id,
                        step.step_id,
                        step.confidence
                    ))

        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates

    def export_results(self, output_path: str) -> str:
        """Export results to JSON."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "total_trajectories": len(self.results),
            "trajectories_with_candidates": sum(
                1 for r in self.results if r.candidate_steps
            ),
            "total_candidate_steps": sum(
                len(r.candidate_steps) for r in self.results
            ),
            "high_confidence_count": len(self.get_high_confidence_candidates()),
            "results": [r.to_dict() for r in self.results],
        }

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Candidate results exported to {output_path}")
        return str(output)


def find_candidate_failures(
    trajectories: list[dict[str, Any]]
) -> list[TrajectoryCandidateResult]:
    """
    Find candidate failure points in trajectories.

    Args:
        trajectories: List of raw trajectory dictionaries.

    Returns:
        List of candidate results per trajectory.
    """
    analyzer = BatchCandidateAnalyzer()
    return analyzer.analyze_trajectories(trajectories)
