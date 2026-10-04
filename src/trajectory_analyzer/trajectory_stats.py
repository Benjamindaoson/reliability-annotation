"""
Trajectory statistics module.

Computes aggregate statistics for trajectory datasets.
"""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from ..trajectory.normalizer import normalize_trajectory
from ..trajectory.schema import EvaluatorResult, Trajectory, TrajectoryStatistics

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryRecord:
    """Per-trajectory summary record."""
    trajectory_id: str
    task_id: str
    model_id: str
    length: int
    success: bool
    last_step: int
    num_actions: int
    reasoning_available: bool
    reasoning_coverage: float
    avg_step_duration: Optional[float] = None
    total_duration: Optional[float] = None


class TrajectoryStatisticsGenerator:
    """Generates statistics from a collection of trajectories."""

    def __init__(self):
        self.trajectories: list[Trajectory] = []
        self.records: list[TrajectoryRecord] = []

    def add_trajectory(self, trajectory: Trajectory):
        """Add a trajectory to the collection."""
        self.trajectories.append(trajectory)
        self.records.append(self._create_record(trajectory))

    def add_raw_trajectory(self, raw_trajectory: dict[str, Any]):
        """Add a raw trajectory dictionary and normalize it."""
        trajectory, warnings = normalize_trajectory(raw_trajectory)
        for warning in warnings:
            logger.debug(warning)
        self.add_trajectory(trajectory)

    def _create_record(self, trajectory: Trajectory) -> TrajectoryRecord:
        """Create a summary record for a trajectory."""
        steps_with_reasoning = sum(
            1 for s in trajectory.steps
            if s.reasoning.reasoning_trace
        )
        reasoning_coverage = (
            steps_with_reasoning / len(trajectory.steps)
            if trajectory.steps else 0.0
        )

        durations = [
            s.duration_seconds for s in trajectory.steps
            if s.duration_seconds is not None
        ]
        avg_duration = sum(durations) / len(durations) if durations else None

        return TrajectoryRecord(
            trajectory_id=trajectory.metadata.trajectory_id,
            task_id=trajectory.metadata.task_id,
            model_id=trajectory.metadata.model_id,
            length=len(trajectory.steps),
            success=trajectory.final_success == EvaluatorResult.SUCCESS,
            last_step=len(trajectory.steps) - 1,
            num_actions=len(trajectory.steps),
            reasoning_available=steps_with_reasoning > 0,
            reasoning_coverage=reasoning_coverage,
            avg_step_duration=avg_duration,
            total_duration=trajectory.metadata.total_duration_seconds,
        )

    def compute_statistics(self) -> TrajectoryStatistics:
        """Compute aggregate statistics."""
        if not self.trajectories:
            return TrajectoryStatistics()

        stats = TrajectoryStatistics()

        # Basic counts
        stats.total_trajectories = len(self.trajectories)
        stats.successful_trajectories = sum(1 for t in self.trajectories if t.final_success == EvaluatorResult.SUCCESS)
        stats.failed_trajectories = sum(1 for t in self.trajectories if t.final_success == EvaluatorResult.FAILURE)
        stats.incomplete_trajectories = sum(1 for t in self.trajectories if t.final_success == EvaluatorResult.INCOMPLETE)

        # Step statistics
        lengths = [len(t.steps) for t in self.trajectories]
        stats.total_steps = sum(lengths)
        stats.avg_steps_per_trajectory = stats.total_steps / stats.total_trajectories
        stats.min_steps = min(lengths) if lengths else 0
        stats.max_steps = max(lengths) if lengths else 0

        import statistics
        if lengths:
            sorted_lengths = sorted(lengths)
            mid = len(sorted_lengths) // 2
            if len(sorted_lengths)) % 2 == 0:
                stats.median_steps_per_trajectory = (sorted_lengths[mid - 1] + sorted_lengths[mid]) / 2
            else:
                stats.median_steps_per_trajectory = sorted_lengths[mid]

        # Model breakdown
        model_trajectories = defaultdict(list)
        for t in self.trajectories:
            model_trajectories[t.metadata.model_id].append(t)

        stats.models = sorted(model_trajectories.keys())
        stats.trajectories_by_model = {
            m: len(traj_list) for m, traj_list in model_trajectories.items()
        }
        stats.success_rate_by_model = {
            m: sum(1 for t in traj_list if t.final_success == EvaluatorResult.SUCCESS) / len(traj_list)
            for m, traj_list in model_trajectories.items()
        }

        # Task breakdown
        task_trajectories = defaultdict(list)
        for t in self.trajectories:
            task_trajectories[t.metadata.task_id].append(t)

        stats.tasks = sorted(task_trajectories.keys())
        stats.trajectories_by_task = {
            task: len(traj_list) for task, traj_list in task_trajectories.items()
        }
        stats.success_rate_by_task = {
            task: sum(1 for t in traj_list if t.final_success == EvaluatorResult.SUCCESS) / len(traj_list)
            for task, traj_list in task_trajectories.items()
        }

        # Reasoning coverage
        reasoning_covered = sum(1 for r in self.records if r.reasoning_available)
        stats.trajectories_with_reasoning = reasoning_covered
        stats.avg_reasoning_coverage = (
            sum(r.reasoning_coverage for r in self.records) / len(self.records)
        )

        return stats

    def to_dataframe(self) -> pd.DataFrame:
        """Convert records to a pandas DataFrame."""
        return pd.DataFrame([asdict(r) for r in self.records])

    def export_json(self, output_path: str) -> str:
        """Export statistics to JSON."""
        stats = self.compute_statistics()
        stats_dict = asdict(stats)

        # Add individual records
        stats_dict["trajectories"] = [
            asdict(r) for r in self.records
        ]

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(stats_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Statistics exported to {output_path}")
        return str(output)

    def export_csv(self, output_path: str) -> str:
        """Export trajectory records to CSV."""
        df = self.to_dataframe()

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output, index=False)
        logger.info(f"Records exported to {output_path}")
        return str(output)


def generate_trajectory_statistics(
    trajectories: list[dict[str, Any]]
) -> tuple[TrajectoryStatistics, pd.DataFrame]:
    """
    Generate statistics from a list of raw trajectories.

    Args:
        trajectories: List of raw trajectory dictionaries.

    Returns:
        Tuple of (TrajectoryStatistics, DataFrame of individual records)
    """
    generator = TrajectoryStatisticsGenerator()

    for raw_trajectory in trajectories:
        generator.add_raw_trajectory(raw_trajectory)

    stats = generator.compute_statistics()
    df = generator.to_dataframe()

    return stats, df


def print_statistics(stats: TrajectoryStatistics):
    """Print statistics in a formatted way."""
    print("\n" + "=" * 60)
    print("TRAJECTORY STATISTICS")
    print("=" * 60)

    print(f"\nTotal trajectories: {stats.total_trajectories}")
    print(f"  Successful: {stats.successful_trajectories}")
    print(f"  Failed: {stats.failed_trajectories}")
    print(f"  Incomplete: {stats.incomplete_trajectories}")

    print(f"\nStep Statistics:")
    print(f"  Total steps: {stats.total_steps}")
    print(f"  Average steps per trajectory: {stats.avg_steps_per_trajectory:.1f}")
    print(f"  Median steps per trajectory: {stats.median_steps_per_trajectory:.1f}")
    print(f"  Min steps: {stats.min_steps}")
    print(f"  Max steps: {stats.max_steps}")

    if stats.models:
        print(f"\nModels ({len(stats.models)}):")
        for model in stats.models[:5]:  # Show first 5
            count = stats.trajectories_by_model[model]
            rate = stats.success_rate_by_model[model] * 100
            print(f"  {model}: {count} trajectories, {rate:.1f}% success rate")
        if len(stats.models) > 5:
            print(f"  ... and {len(stats.models) - 5} more models")

    if stats.tasks:
        print(f"\nTasks ({len(stats.tasks)}):")
        for task in stats.tasks[:5]:  # Show first 5
            count = stats.trajectories_by_task[task]
            rate = stats.success_rate_by_task[task] * 100
            print(f"  {task}: {count} trajectories, {rate:.1f}% success rate")
        if len(stats.tasks) > 5:
            print(f"  ... and {len(stats.tasks) - 5} more tasks")

    print(f"\nReasoning Coverage:")
    print(f"  Average coverage: {stats.avg_reasoning_coverage * 100:.1f}%")
    print(f"  Trajectories with reasoning: {stats.trajectories_with_reasoning}/{stats.total_trajectories}")

    print("\n" + "=" * 60)
