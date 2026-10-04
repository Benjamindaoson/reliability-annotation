"""
Core schema definitions for trajectory analysis.

This module defines the unified representation for OSWorld trajectories,
enabling consistent analysis across different data formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class FailureType(str, Enum):
    """Types of consequential failures in agent trajectories."""
    SELECTION = "selection"      # Wrong action given correct world model
    EXECUTION = "execution"      # Correct intention, failed execution
    RECOGNITION = "recognition"  # Failure occurred, agent did not detect
    RECOVERY = "recovery"        # Failure detected, recovery failed
    UNKNOWN = "unknown"          # Not yet classified


class EvaluatorResult(str, Enum):
    """Result of task evaluation."""
    SUCCESS = "success"
    FAILURE = "failure"
    INCOMPLETE = "incomplete"   # Trajectory ended before completion
    UNKNOWN = "unknown"


@dataclass
class ActionInfo:
    """Information about an agent action."""
    action_type: str = "unknown"
    action_arguments: dict[str, Any] = field(default_factory=dict)
    raw_action: Optional[str] = None
    predicted_outcome: Optional[str] = None


@dataclass
class ObservationInfo:
    """Information about the environment observation."""
    screenshot: Optional[str] = None           # Base64 or path to screenshot
    text_state: Optional[str] = None           # Textual environment state
    accessibility_state: Optional[dict] = None # Accessibility tree / DOM
    history_summary: Optional[str] = None     # Prior state summary
    hidden_state: Optional[dict] = None        # State not visible to agent


@dataclass
class ReasoningInfo:
    """Information about agent reasoning/thinking."""
    reasoning_trace: Optional[str] = None      # Full reasoning chain
    reasoning_summary: Optional[str] = None    # Condensed reasoning
    confidence: Optional[float] = None         # Agent's confidence (0-1)
    uncertainty_expressed: bool = False        # Agent mentioned uncertainty


@dataclass
class EnvironmentFeedback:
    """Feedback from the environment after an action."""
    feedback_text: Optional[str] = None
    state_changed: bool = True
    error_message: Optional[str] = None
    execution_success: bool = True


@dataclass
class EvaluatorSignal:
    """Signal from the task evaluator."""
    result: EvaluatorResult = EvaluatorResult.UNKNOWN
    score: Optional[float] = None
    partial_credit: Optional[float] = None
    feedback: Optional[str] = None
    step_metrics: Optional[dict] = None


@dataclass
class CandidateSignal:
    """Signal indicating a potential failure point."""
    signal_type: str                    # e.g., "task_failed_after_step"
    confidence: float                   # 0.0 to 1.0
    description: str
    evidence: Optional[dict] = None


@dataclass
class TrajectoryStep:
    """
    Single step in an agent trajectory.

    Represents one observation → action → feedback cycle.
    """
    step_id: int

    # Core components
    observation: ObservationInfo = field(default_factory=ObservationInfo)
    action: ActionInfo = field(default_factory=ActionInfo)
    reasoning: ReasoningInfo = field(default_factory=ReasoningInfo)
    environment_feedback: EnvironmentFeedback = field(default_factory=EnvironmentFeedback)
    evaluator_signal: Optional[EvaluatorSignal] = None

    # Timing and metadata
    timestamp: Optional[str] = None
    duration_seconds: Optional[float] = None

    # Failure-related (for candidate identification)
    candidate_signals: list[CandidateSignal] = field(default_factory=list)

    # Raw storage for unprocessed fields
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrajectoryMetadata:
    """Metadata about the trajectory as a whole."""
    trajectory_id: str
    task_id: str
    model_id: str
    model_name: Optional[str] = None

    # Task information
    task_description: Optional[str] = None
    task_category: Optional[str] = None
    task_difficulty: Optional[str] = None

    # Execution information
    environment: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_duration_seconds: Optional[float] = None

    # Source information
    data_source: Optional[str] = None     # e.g., "osworld_verified"
    source_file: Optional[str] = None


@dataclass
class Trajectory:
    """
    Complete agent trajectory.

    Represents a full episode of agent interaction with the environment.
    """
    metadata: TrajectoryMetadata
    steps: list[TrajectoryStep] = field(default_factory=list)

    # Final evaluation
    final_success: EvaluatorResult = EvaluatorResult.UNKNOWN
    final_score: Optional[float] = None

    # Derived metrics (computed during analysis)
    trajectory_length: int = 0
    reasoning覆盖率: float = 0.0

    # Raw storage
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    original_format: Optional[str] = None  # e.g., "osworld_v1", "custom"

    def __post_init__(self):
        """Compute derived fields after initialization."""
        self.trajectory_length = len(self.steps)
        if self.trajectory_length > 0:
            steps_with_reasoning = sum(
                1 for s in self.steps
                if s.reasoning.reasoning_trace
            )
            self.reasoning_coverage = steps_with_reasoning / self.trajectory_length

    def get_step(self, step_id: int) -> Optional[TrajectoryStep]:
        """Get a step by its ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_candidate_steps(self) -> list[TrajectoryStep]:
        """Get all steps with candidate failure signals."""
        return [s for s in self.steps if len(s.candidate_signals) > 0]

    def get_final_step(self) -> Optional[TrajectoryStep]:
        """Get the last step in the trajectory."""
        if self.steps:
            return self.steps[-1]
        return None


@dataclass
class TrajectoryStatistics:
    """Aggregate statistics for a dataset of trajectories."""
    total_trajectories: int = 0
    successful_trajectories: int = 0
    failed_trajectories: int = 0
    incomplete_trajectories: int = 0

    # Step statistics
    total_steps: int = 0
    avg_steps_per_trajectory: float = 0.0
    median_steps_per_trajectory: float = 0.0
    min_steps: int = 0
    max_steps: int = 0

    # Model breakdown
    models: list[str] = field(default_factory=list)
    trajectories_by_model: dict[str, int] = field(default_factory=dict)
    success_rate_by_model: dict[str, float] = field(default_factory=dict)

    # Task breakdown
    tasks: list[str] = field(default_factory=list)
    trajectories_by_task: dict[str, int] = field(default_factory=dict)
    success_rate_by_task: dict[str, float] = field(default_factory=dict)

    # Reasoning coverage
    avg_reasoning_coverage: float = 0.0
    trajectories_with_reasoning: int = 0

    # Candidate failure statistics
    total_candidate_steps: int = 0
    trajectories_with_candidates: int = 0
    candidate_signals_by_type: dict[str, int] = field(default_factory=dict)


@dataclass
class AnnotatedFailure:
    """
    Human annotation of a failure point.

    To be filled by human annotators.
    """
    # Annotation status
    annotated: bool = False
    annotator_id: Optional[str] = None
    annotation_timestamp: Optional[str] = None

    # Core annotation
    first_consequential_failure_step: Optional[int] = None
    failure_type: Optional[FailureType] = None

    # Detailed classification
    is_selection: Optional[bool] = None
    is_execution: Optional[bool] = None
    is_recognition: Optional[bool] = None
    is_recovery: Optional[bool] = None

    # Additional context
    local_causal_window_start: Optional[int] = None
    local_causal_window_end: Optional[int] = None

    # Notes
    annotator_notes: Optional[str] = None
    confidence_level: Optional[str] = None  # "high", "medium", "low"


@dataclass
class AnnotationExport:
    """Export format for human annotation."""
    trajectory_id: str
    task_id: str
    model_id: str
    task_description: str
    final_success: bool

    candidate_step: Optional[int] = None
    candidate_signals: list[str] = field(default_factory=list)

    # Context for annotation
    context_before: list[dict] = field(default_factory=list)
    context_failure_step: Optional[dict] = None
    context_after: list[dict] = field(default_factory=list)

    # Annotation fields (to be filled)
    failure_annotation: dict = field(default_factory=lambda: {
        "first_consequential_failure": None,
        "failure_type": None,
        "selection": None,
        "execution": None,
        "recognition": None,
        "recovery": None,
        "annotator_notes": None,
    })

    # Metadata
    exported_at: str = ""
    original_trajectory_length: int = 0
