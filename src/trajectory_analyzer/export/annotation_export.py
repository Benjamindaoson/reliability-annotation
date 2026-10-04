"""
Annotation export module.

Generates human-readable annotation files from trajectories and candidate failures.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..trajectory.normalizer import normalize_trajectory
from ..trajectory.schema import AnnotationExport, EvaluatorResult, Trajectory

logger = logging.getLogger(__name__)


@dataclass
class StepContext:
    """Context around a candidate failure step."""
    step_id: int
    action_type: str
    action_summary: str
    reasoning_excerpt: Optional[str] = None
    feedback: Optional[str] = None
    evaluator_result: Optional[str] = None


class AnnotationExporter:
    """Generates annotation files for human labeling."""

    def __init__(
        self,
        context_window: int = 3,
        reasoning_excerpt_length: int = 200
    ):
        """
        Initialize the exporter.

        Args:
            context_window: Number of steps to include before/after candidate.
            reasoning_excerpt_length: Max characters for reasoning excerpts.
        """
        self.context_window = context_window
        self.reasoning_excerpt_length = reasoning_excerpt_length

    def export_trajectory(
        self,
        trajectory: Trajectory,
        candidate_step: Optional[int] = None
    ) -> AnnotationExport:
        """
        Create an annotation export for a single trajectory.

        Args:
            trajectory: Normalized trajectory.
            candidate_step: Optional step ID to highlight as candidate.

        Returns:
            AnnotationExport ready for human annotation.
        """
        # Get context
        context_before, context_failure, context_after = self._get_context(
            trajectory, candidate_step
        )

        # Build export
        export = AnnotationExport(
            trajectory_id=trajectory.metadata.trajectory_id,
            task_id=trajectory.metadata.task_id,
            model_id=trajectory.metadata.model_id,
            task_description=trajectory.metadata.task_description or "",
            final_success=trajectory.final_success == EvaluatorResult.SUCCESS,
            candidate_step=candidate_step,
            context_before=[asdict(c) for c in context_before],
            context_failure_step=asdict(context_failure) if context_failure else None,
            context_after=[asdict(c) for c in context_after],
            original_trajectory_length=len(trajectory.steps),
            exported_at=datetime.now().isoformat(),
        )

        return export

    def export_raw_trajectory(
        self,
        raw_trajectory: dict[str, Any],
        candidate_step: Optional[int] = None
    ) -> AnnotationExport:
        """Export from a raw trajectory dictionary."""
        trajectory, warnings = normalize_trajectory(raw_trajectory)
        return self.export_trajectory(trajectory, candidate_step)

    def _get_context(
        self,
        trajectory: Trajectory,
        candidate_step: Optional[int]
    ) -> tuple[list[StepContext], Optional[StepContext], list[StepContext]]:
        """Extract context around a candidate step."""
        if candidate_step is None or not trajectory.steps:
            return [], None, []

        # Before context
        start_idx = max(0, candidate_step - self.context_window)
        context_before = []
        for i in range(start_idx, candidate_step):
            context_before.append(self._step_to_context(trajectory.steps[i]))

        # Candidate step
        candidate_idx = min(candidate_step, len(trajectory.steps) - 1)
        context_failure = self._step_to_context(trajectory.steps[candidate_idx])

        # After context
        end_idx = min(
            len(trajectory.steps),
            candidate_step + self.context_window + 1
        )
        context_after = []
        for i in range(candidate_step + 1, end_idx):
            context_after.append(self._step_to_context(trajectory.steps[i]))

        return context_before, context_failure, context_after

    def _step_to_context(self, step) -> StepContext:
        """Convert a TrajectoryStep to StepContext."""
        # Get reasoning excerpt
        reasoning = step.reasoning.reasoning_trace
        reasoning_excerpt = None
        if reasoning:
            reasoning_excerpt = reasoning[:self.reasoning_excerpt_length]
            if len(reasoning) > self.reasoning_excerpt_length:
                reasoning_excerpt += "..."

        # Get evaluator result
        evaluator_result = None
        if step.evaluator_signal:
            evaluator_result = step.evaluator_signal.result.value

        return StepContext(
            step_id=step.step_id,
            action_type=step.action.action_type,
            action_summary=self._summarize_action(step),
            reasoning_excerpt=reasoning_excerpt,
            feedback=step.environment_feedback.feedback_text,
            evaluator_result=evaluator_result,
        )

    def _summarize_action(self, step) -> str:
        """Create a human-readable action summary."""
        action = step.action
        args = action.action_arguments

        if not args:
            return action.action_type

        # Format arguments
        arg_strs = []
        for key, value in list(args.items())[:3]:  # Limit to 3 args
            if isinstance(value, str) and len(value) > 50:
                value = value[:47] + "..."
            arg_strs.append(f"{key}={value}")

        return f"{action.action_type}({', '.join(arg_strs)})"


class BatchAnnotationExporter:
    """Exports annotations for multiple trajectories."""

    def __init__(self):
        self.exporter = AnnotationExporter()
        self.exports: list[AnnotationExport] = []

    def export_trajectories(
        self,
        trajectories: list[dict[str, Any]],
        candidate_results: Optional[list[dict]] = None
    ) -> list[AnnotationExport]:
        """
        Export annotations for multiple trajectories.

        Args:
            trajectories: List of raw trajectory dictionaries.
            candidate_results: Optional list of candidate failure results.

        Returns:
            List of AnnotationExport objects.
        """
        self.exports = []

        # Build a lookup for candidate results
        candidate_lookup = {}
        if candidate_results:
            for result in candidate_results:
                traj_id = result.get("trajectory_id")
                if traj_id and result.get("candidate_steps"):
                    # Use the highest confidence candidate
                    candidates = result["candidate_steps"]
                    best = max(candidates, key=lambda x: x.get("confidence", 0))
                    candidate_lookup[traj_id] = best.get("step")

        for raw_trajectory in trajectories:
            traj_id = raw_trajectory.get("trajectory_id", "unknown")
            candidate_step = candidate_lookup.get(traj_id)

            export = self.exporter.export_raw_trajectory(
                raw_trajectory, candidate_step
            )
            self.exports.append(export)

        return self.exports

    def export_to_directory(
        self,
        output_dir: str,
        trajectories: list[dict[str, Any]],
        candidate_results: Optional[list[dict]] = None
    ) -> str:
        """
        Export individual annotation files to a directory.

        Args:
            output_dir: Directory to write annotation files.
            trajectories: List of raw trajectory dictionaries.
            candidate_results: Optional candidate failure results.

        Returns:
            Path to the output directory.
        """
        exports = self.export_trajectories(trajectories, candidate_results)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for export in exports:
            filename = f"trajectory_{export.trajectory_id}.json"
            filepath = output_path / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(export), f, indent=2, ensure_ascii=False)

            logger.debug(f"Exported: {filepath}")

        logger.info(f"Exported {len(exports)} annotation files to {output_dir}")
        return str(output_dir)

    def export_combined(
        self,
        output_path: str,
        trajectories: list[dict[str, Any]],
        candidate_results: Optional[list[dict]] = None
    ) -> str:
        """
        Export all annotations to a single JSON file.

        Args:
            output_path: Path for the combined output file.
            trajectories: List of raw trajectory dictionaries.
            candidate_results: Optional candidate failure results.

        Returns:
            Path to the output file.
        """
        exports = self.export_trajectories(trajectories, candidate_results)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "exported_at": datetime.now().isoformat(),
            "total_trajectories": len(exports),
            "annotations": [asdict(e) for e in exports],
        }

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported combined annotations to {output_path}")
        return str(output)


def export_annotations(
    trajectories: list[dict[str, Any]],
    candidate_results: Optional[list[dict]] = None,
    output_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> tuple[list[AnnotationExport], str]:
    """
    Export annotations for human labeling.

    Args:
        trajectories: List of raw trajectory dictionaries.
        candidate_results: Optional candidate failure results.
        output_path: Path for combined JSON output.
        output_dir: Directory for individual files.

    Returns:
        Tuple of (list of exports, path to output).
    """
    exporter = BatchAnnotationExporter()

    if output_dir:
        output = exporter.export_to_directory(output_dir, trajectories, candidate_results)
        exports = exporter.exports
    elif output_path:
        exporter.export_combined(output_path, trajectories, candidate_results)
        exports = exporter.exports
        output = output_path
    else:
        # Export to memory only
        exports = exporter.export_trajectories(trajectories, candidate_results)
        output = ""

    return exports, output
