"""
Tests for OSWorld data loader.
"""

import json
import tempfile
import zipfile
from pathlib import Path

import pytest

from src.trajectory_analyzer.data_loader.osworld_loader import (
    OSWorldLoader,
    DatasetInfo,
    inspect_osworld_dataset,
)


class TestOSWorldLoader:
    def test_load_from_empty_directory(self, tmp_path):
        """Test loading from empty directory."""
        loader = OSWorldLoader(str(tmp_path))
        trajectories = list(loader.load(str(tmp_path)))
        assert len(trajectories) == 0

    def test_load_single_json(self, tmp_path):
        """Test loading from a single JSON file."""
        # Create test file
        data = [
            {"trajectory_id": "t1", "task_id": "task1", "model_id": "m1"},
            {"trajectory_id": "t2", "task_id": "task2", "model_id": "m2"},
        ]
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        loader = OSWorldLoader()
        trajectories = list(loader.load(str(test_file)))

        assert len(trajectories) == 2
        assert trajectories[0]["trajectory_id"] == "t1"

    def test_load_jsonl(self, tmp_path):
        """Test loading from JSONL file."""
        test_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"trajectory_id": "t1", "task_id": "task1", "model_id": "m1"}),
            json.dumps({"trajectory_id": "t2", "task_id": "task2", "model_id": "m2"}),
        ]
        test_file.write_text("\n".join(lines))

        loader = OSWorldLoader()
        trajectories = list(loader.load(str(test_file)))

        assert len(trajectories) == 2

    def test_load_with_filters(self, tmp_path):
        """Test loading with model and task filters."""
        data = [
            {"trajectory_id": "t1", "task_id": "task1", "model_id": "model_a"},
            {"trajectory_id": "t2", "task_id": "task2", "model_id": "model_b"},
            {"trajectory_id": "t3", "task_id": "task1", "model_id": "model_b"},
        ]
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        loader = OSWorldLoader()

        # Filter by model
        trajectories = list(loader.load(str(test_file), filter_model="model_a"))
        assert len(trajectories) == 1
        assert trajectories[0]["trajectory_id"] == "t1"

        # Filter by task
        trajectories = list(loader.load(str(test_file), filter_task="task1"))
        assert len(trajectories) == 2  # t1 and t3 both have task_id="task1"
        assert trajectories[0]["trajectory_id"] == "t1"

    def test_load_with_limit(self, tmp_path):
        """Test loading with limit."""
        data = [{"trajectory_id": f"t{i}", "task_id": "task1", "model_id": "m1"} for i in range(10)]
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        loader = OSWorldLoader()
        trajectories = list(loader.load(str(test_file), limit=3))

        assert len(trajectories) == 3

    def test_load_directory(self, tmp_path):
        """Test loading from directory."""
        # Create multiple files
        for i in range(3):
            data = {"trajectory_id": f"t{i}", "task_id": "task1", "model_id": "m1"}
            (tmp_path / f"file{i}.json").write_text(json.dumps(data))

        loader = OSWorldLoader()
        trajectories = list(loader.load(str(tmp_path)))

        assert len(trajectories) == 3

    def test_load_zip_archive(self, tmp_path):
        """Test loading from ZIP archive."""
        # Create ZIP file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(
                "traj1.jsonl",
                json.dumps({"trajectory_id": "t1", "task_id": "task1", "model_id": "m1"}) + "\n" +
                json.dumps({"trajectory_id": "t2", "task_id": "task2", "model_id": "m2"}) + "\n"
            )

        loader = OSWorldLoader()
        trajectories = list(loader.load(str(zip_path)))

        assert len(trajectories) == 2


class TestDatasetInspection:
    def test_inspect_single_file(self, tmp_path):
        """Test inspecting a single JSON file."""
        data = [
            {"trajectory_id": "t1", "task_id": "task1", "model_id": "model_a", "extra": "value1"},
            {"trajectory_id": "t2", "task_id": "task2", "model_id": "model_b", "extra": "value2"},
        ]
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        loader = OSWorldLoader()
        info = loader.inspect(str(test_file), max_samples=10)

        assert info.total_trajectories == 2
        assert "model_a" in info.models
        assert "model_b" in info.models
        assert "task1" in info.tasks
        assert "task2" in info.tasks
        assert "trajectory_id" in info.fields_available
        assert "extra" in info.fields_available

    def test_inspect_directory(self, tmp_path):
        """Test inspecting a directory."""
        for i in range(3):
            data = {"trajectory_id": f"t{i}", "task_id": f"task{i}", "model_id": "model_x"}
            (tmp_path / f"file{i}.json").write_text(json.dumps(data))

        loader = OSWorldLoader()
        info = loader.inspect(str(tmp_path), max_samples=10)

        assert info.total_trajectories == 3
        assert "model_x" in info.models
        assert info.format.startswith("directory")

    def test_inspect_nonexistent_path(self):
        """Test inspecting non-existent path raises error."""
        loader = OSWorldLoader()
        with pytest.raises(FileNotFoundError):
            loader.inspect("/nonexistent/path")


class TestInspectFunction:
    def test_inspect_osworld_dataset(self, tmp_path):
        """Test convenience function."""
        data = {"trajectory_id": "t1", "task_id": "task1", "model_id": "m1"}
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        info = inspect_osworld_dataset(str(test_file), max_samples=10)

        assert info.total_trajectories == 1
        assert info.models == ["m1"]


class TestEdgeCases:
    def test_malformed_jsonl(self, tmp_path):
        """Test handling of malformed JSONL lines."""
        test_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"trajectory_id": "t1", "task_id": "task1", "model_id": "m1"}),
            "not valid json",  # Malformed line
            json.dumps({"trajectory_id": "t2", "task_id": "task2", "model_id": "m2"}),
        ]
        test_file.write_text("\n".join(lines))

        loader = OSWorldLoader()
        trajectories = list(loader.load(str(test_file)))

        # Should skip malformed line
        assert len(trajectories) == 2

    def test_empty_json_file(self, tmp_path):
        """Test loading empty JSON file."""
        test_file = tmp_path / "empty.json"
        test_file.write_text("[]")

        loader = OSWorldLoader()
        trajectories = list(loader.load(str(test_file)))

        assert len(trajectories) == 0

    def test_empty_jsonl_file(self, tmp_path):
        """Test loading empty JSONL file."""
        test_file = tmp_path / "empty.jsonl"
        test_file.write_text("")

        loader = OSWorldLoader()
        trajectories = list(loader.load(str(test_file)))

        assert len(trajectories) == 0
