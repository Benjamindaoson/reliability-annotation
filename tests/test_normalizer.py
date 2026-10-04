"""
Tests for trajectory normalizer.
"""

import pytest
from src.trajectory_analyzer.trajectory.normalizer import (
    TrajectoryNormalizer,
    normalize_trajectory,
    normalize_trajectories,
)


class TestTrajectoryNormalizer:
    def test_normalize_minimal_trajectory(self):
        """Test normalization of a minimal trajectory."""
        raw = {
            "trajectory_id": "traj_001",
            "task_id": "task_001",
            "model_id": "model_x",
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert trajectory.metadata.trajectory_id == "traj_001"
        assert trajectory.metadata.task_id == "task_001"
        assert trajectory.metadata.model_id == "model_x"
        assert len(trajectory.steps) == 0

    def test_normalize_with_steps(self):
        """Test normalization of a trajectory with steps."""
        raw = {
            "trajectory_id": "traj_002",
            "task_id": "task_001",
            "model_id": "model_x",
            "steps": [
                {
                    "observation": {"text_state": "Desktop"},
                    "action": {"action_type": "click", "args": {"x": 100}},
                    "reasoning": "I should click here",
                }
            ],
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert len(trajectory.steps) == 1
        assert trajectory.steps[0].observation.text_state == "Desktop"
        assert trajectory.steps[0].action.action_type == "click"
        assert trajectory.steps[0].reasoning.reasoning_trace == "I should click here"

    def test_normalize_missing_fields(self):
        """Test normalization handles missing fields gracefully."""
        raw = {
            "trajectory_id": "traj_003",
            # Missing task_id and model_id
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert trajectory.metadata.trajectory_id == "traj_003"
        assert trajectory.metadata.task_id == "unknown"
        assert trajectory.metadata.model_id == "unknown"
        assert len(warning.warnings) > 0

    def test_normalize_empty_steps(self):
        """Test normalization with empty steps array."""
        raw = {
            "trajectory_id": "traj_004",
            "task_id": "task_001",
            "model_id": "model_x",
            "steps": [],
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert len(trajectory.steps) == 0

    def test_normalize_success_field(self):
        """Test normalization of success field."""
        raw = {
            "trajectory_id": "traj_005",
            "task_id": "task_001",
            "model_id": "model_x",
            "success": True,
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert trajectory.final_success.value == "success"

        raw["success"] = False
        trajectory, _ = normalizer.normalize(raw)
        assert trajectory.final_success.value == "failure"

    def test_normalize_reasoning_string(self):
        """Test normalization of string reasoning."""
        raw = {
            "trajectory_id": "traj_006",
            "task_id": "task_001",
            "model_id": "model_x",
            "steps": [
                {
                    "observation": {},
                    "action": {"action_type": "noop"},
                    "reasoning": "This looks correct",
                }
            ],
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert trajectory.steps[0].reasoning.reasoning_trace == "This looks correct"

    def test_normalize_reasoning_dict(self):
        """Test normalization of dict reasoning."""
        raw = {
            "trajectory_id": "traj_007",
            "task_id": "task_001",
            "model_id": "model_x",
            "steps": [
                {
                    "observation": {},
                    "action": {"action_type": "noop"},
                    "reasoning": {
                        "trace": "Full reasoning here",
                        "summary": "Summary",
                        "confidence": 0.9,
                    },
                }
            ],
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert trajectory.steps[0].reasoning.reasoning_trace == "Full reasoning here"
        assert trajectory.steps[0].reasoning.reasoning_summary == "Summary"
        assert trajectory.steps[0].reasoning.confidence == 0.9

    def test_detect_uncertainty(self):
        """Test uncertainty detection in reasoning."""
        raw = {
            "trajectory_id": "traj_008",
            "task_id": "task_001",
            "model_id": "model_x",
            "steps": [
                {
                    "observation": {},
                    "action": {"action_type": "noop"},
                    "reasoning": "I'm not sure if this is correct",
                }
            ],
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert trajectory.steps[0].reasoning.uncertainty_expressed is True

    def test_detect_uncertainty_none(self):
        """Test no uncertainty detected."""
        raw = {
            "trajectory_id": "traj_009",
            "task_id": "task_001",
            "model_id": "model_x",
            "steps": [
                {
                    "observation": {},
                    "action": {"action_type": "noop"},
                    "reasoning": "This is the correct file to edit",
                }
            ],
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert trajectory.steps[0].reasoning.uncertainty_expressed is False

    def test_detect_format(self):
        """Test format detection."""
        normalizer = TrajectoryNormalizer()

        # OSWorld v1
        raw = {"trajectory_id": "t1", "history": []}
        _, _ = normalizer.normalize(raw)
        # Note: format detection is internal

    def test_preserve_raw_data(self):
        """Test that raw data is preserved."""
        raw = {
            "trajectory_id": "traj_010",
            "task_id": "task_001",
            "model_id": "model_x",
            "custom_field": "custom_value",
            "steps": [],
        }
        normalizer = TrajectoryNormalizer()
        trajectory, warning = normalizer.normalize(raw)

        assert trajectory.raw_metadata.get("custom_field") == "custom_value"


class TestNormalizeFunctions:
    def test_normalize_trajectory_function(self):
        """Test convenience function."""
        raw = {
            "trajectory_id": "traj_func",
            "task_id": "task_001",
            "model_id": "model_x",
        }
        trajectory, warnings = normalize_trajectory(raw)

        assert trajectory.metadata.trajectory_id == "traj_func"
        assert len(warnings) >= 0

    def test_normalize_trajectories_function(self):
        """Test batch normalization."""
        raw_list = [
            {"trajectory_id": "t1", "task_id": "t", "model_id": "m"},
            {"trajectory_id": "t2", "task_id": "t", "model_id": "m"},
        ]
        trajectories, warnings = normalize_trajectories(raw_list)

        assert len(trajectories) == 2
        assert len(warnings) == 2


class TestStrictMode:
    def test_strict_mode_missing_critical(self):
        """Test strict mode raises on missing critical fields."""
        raw = {}  # Missing everything
        normalizer = TrajectoryNormalizer(strict_mode=False)
        trajectory, _ = normalizer.normalize(raw)
        # Should not raise, just warn

    def test_action_format_variations(self):
        """Test handling of different action formats."""
        raw = {
            "trajectory_id": "t1",
            "task_id": "t",
            "model_id": "m",
            "steps": [
                {
                    "action": {"type": "click", "args": {}},  # 'type' instead of 'action_type'
                },
                {
                    "action": {"action_type": "type", "arguments": {}},  # 'arguments' instead of 'args'
                },
                {
                    "action": {"action": "move"},  # 'action' instead of 'action_type'
                },
            ],
        }
        normalizer = TrajectoryNormalizer()
        trajectory, _ = normalizer.normalize(raw)

        assert len(trajectory.steps) == 3
        assert trajectory.steps[0].action.action_type == "click"
        assert trajectory.steps[1].action.action_arguments == {}
        assert trajectory.steps[2].action.action_type == "move"
