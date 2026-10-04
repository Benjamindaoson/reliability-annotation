"""
Data loader module for OSWorld trajectories.

Handles loading trajectories from various sources and formats.
"""

from __future__ import annotations

import gzip
import json
import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class DatasetInfo:
    """Information about a loaded dataset."""
    source_path: str
    format: str
    total_trajectories: int = 0
    models: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    fields_available: list[str] = field(default_factory=list)
    file_size_mb: float = 0.0

    # Schema information
    sample_schema: Optional[dict] = None
    all_fields: set[str] = field(default_factory=set)


class OSWorldLoader:
    """
    Loader for OSWorld trajectory datasets.

    Supports multiple formats: JSON, JSONL, JSONL.gz, ZIP, and HuggingFace datasets.
    """

    def __init__(self, path: Optional[str] = None):
        """
        Initialize the loader.

        Args:
            path: Path to the dataset directory or file.
        """
        self.path = Path(path) if path else None
        self.dataset_info: Optional[DatasetInfo] = None

    def inspect(
        self,
        path: Optional[str] = None,
        max_samples: int = 100
    ) -> DatasetInfo:
        """
        Inspect a dataset and return information about its structure.

        Args:
            path: Path to the dataset. Uses self.path if not provided.
            max_samples: Maximum number of trajectories to sample for schema detection.

        Returns:
            DatasetInfo with schema and statistics.
        """
        target_path = Path(path) if path else self.path
        if not target_path:
            raise ValueError("No path provided for inspection")

        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")

        info = DatasetInfo(source_path=str(target_path), format="unknown")

        # Determine format and load
        if target_path.is_file():
            if target_path.suffix == ".zip":
                info = self._inspect_zip(target_path, info, max_samples)
            elif target_path.suffix == ".gz":
                info = self._inspect_gzip(target_path, info, max_samples)
            elif target_path.suffix in [".json", ".jsonl"]:
                info = self._inspect_json_file(target_path, info, max_samples)
        elif target_path.is_dir():
            info = self._inspect_directory(target_path, info, max_samples)
        else:
            raise ValueError(f"Unsupported path type: {target_path}")

        self.dataset_info = info
        return info

    def load(
        self,
        path: Optional[str] = None,
        filter_model: Optional[str] = None,
        filter_task: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Generator[dict[str, Any], None, None]:
        """
        Load trajectories from a dataset.

        Args:
            path: Path to the dataset. Uses self.path if not provided.
            filter_model: Only load trajectories from this model.
            filter_task: Only load trajectories from this task.
            limit: Maximum number of trajectories to load.

        Yields:
            Raw trajectory dictionaries.
        """
        target_path = Path(path) if path else self.path
        if not target_path:
            raise ValueError("No path provided for loading")

        count = 0
        for trajectory in self._iter_trajectories(target_path):
            # Apply filters
            if filter_model and trajectory.get("model_id") != filter_model:
                continue
            if filter_task and trajectory.get("task_id") != filter_task:
                continue

            yield trajectory
            count += 1

            if limit and count >= limit:
                break

    def _iter_trajectories(
        self,
        path: Path
    ) -> Generator[dict[str, Any], None, None]:
        """Iterate over trajectories in a file or directory."""
        if path.is_file():
            if path.suffix == ".zip":
                yield from self._iter_zip(path)
            elif path.suffix == ".gz":
                yield from self._iter_gzip(path)
            elif path.suffix == ".json":
                yield from self._iter_json(path)
            elif path.suffix == ".jsonl":
                yield from self._iter_jsonl(path)
        elif path.is_dir():
            yield from self._iter_directory(path)
        else:
            raise ValueError(f"Unsupported path: {path}")

    def _inspect_directory(
        self,
        dir_path: Path,
        info: DatasetInfo,
        max_samples: int
    ) -> DatasetInfo:
        """Inspect a directory of trajectory files."""
        json_files = list(dir_path.rglob("*.json")) + list(dir_path.rglob("*.jsonl"))
        info.format = f"directory ({len(json_files)} files)"

        if not json_files:
            return info

        # Get file size
        total_size = sum(f.stat().st_size for f in json_files)
        info.file_size_mb = total_size / (1024 * 1024)

        # Sample first file for schema
        sample_file = json_files[0]
        info.sample_schema = self._extract_schema_from_file(sample_file)

        # Count trajectories
        all_models = set()
        all_tasks = set()
        all_fields = set()
        trajectory_count = 0

        for json_file in json_files[:10]:  # Sample up to 10 files
            for trajectory in self._iter_json_file(json_file):
                trajectory_count += 1
                all_models.add(trajectory.get("model_id", trajectory.get("model", "unknown")))
                all_tasks.add(trajectory.get("task_id", trajectory.get("instance_id", "unknown")))
                all_fields.update(trajectory.keys())

                if trajectory_count >= max_samples:
                    break

        info.total_trajectories = trajectory_count
        info.models = sorted(list(all_models))
        info.tasks = sorted(list(all_tasks))
        info.fields_available = sorted(list(all_fields))
        info.all_fields = all_fields

        return info

    def _inspect_json_file(
        self,
        file_path: Path,
        info: DatasetInfo,
        max_samples: int
    ) -> DatasetInfo:
        """Inspect a single JSON or JSONL file."""
        info.format = file_path.suffix.lower()

        # Get file size
        info.file_size_mb = file_path.stat().st_size / (1024 * 1024)

        # Extract schema
        all_models = set()
        all_tasks = set()
        all_fields = set()
        trajectories = []

        for trajectory in self._iter_json_file(file_path):
            trajectories.append(trajectory)
            all_models.add(trajectory.get("model_id", trajectory.get("model", "unknown")))
            all_tasks.add(trajectory.get("task_id", trajectory.get("instance_id", "unknown")))
            all_fields.update(trajectory.keys())

            if len(trajectories) >= max_samples:
                break

        info.total_trajectories = len(trajectories)
        info.models = sorted(list(all_models))
        info.tasks = sorted(list(all_tasks))
        info.fields_available = sorted(list(all_fields))
        info.all_fields = all_fields
        info.sample_schema = trajectories[0] if trajectories else None

        return info

    def _inspect_zip(
        self,
        zip_path: Path,
        info: DatasetInfo,
        max_samples: int
    ) -> DatasetInfo:
        """Inspect a ZIP archive."""
        info.format = "zip"
        info.file_size_mb = zip_path.stat().st_size / (1024 * 1024)

        all_models = set()
        all_tasks = set()
        all_fields = set()
        trajectory_count = 0

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if not name.endswith(('.json', '.jsonl')):
                    continue

                with zf.open(name) as f:
                    for line in f:
                        try:
                            trajectory = json.loads(line)
                            trajectory_count += 1
                            all_models.add(trajectory.get("model_id", "unknown"))
                            all_tasks.add(trajectory.get("task_id", "unknown"))
                            all_fields.update(trajectory.keys())

                            if trajectory_count >= max_samples:
                                break
                        except json.JSONDecodeError:
                            continue

                if trajectory_count >= max_samples:
                    break

        info.total_trajectories = trajectory_count
        info.models = sorted(list(all_models))
        info.tasks = sorted(list(all_tasks))
        info.fields_available = sorted(list(all_fields))
        info.all_fields = all_fields

        return info

    def _inspect_gzip(
        self,
        gz_path: Path,
        info: DatasetInfo,
        max_samples: int
    ) -> DatasetInfo:
        """Inspect a gzip compressed JSONL file."""
        info.format = "jsonl.gz"
        info.file_size_mb = gz_path.stat().st_size / (1024 * 1024)

        all_models = set()
        all_tasks = set()
        all_fields = set()
        trajectory_count = 0

        with gzip.open(gz_path, 'rt') as f:
            for line in f:
                try:
                    trajectory = json.loads(line)
                    trajectory_count += 1
                    all_models.add(trajectory.get("model_id", "unknown"))
                    all_tasks.add(trajectory.get("task_id", "unknown"))
                    all_fields.update(trajectory.keys())

                    if trajectory_count >= max_samples:
                        break
                except json.JSONDecodeError:
                    continue

        info.total_trajectories = trajectory_count
        info.models = sorted(list(all_models))
        info.tasks = sorted(list(all_tasks))
        info.fields_available = sorted(list(all_fields))
        info.all_fields = all_fields

        return info

    def _extract_schema_from_file(self, file_path: Path) -> Optional[dict]:
        """Extract schema from the first trajectory in a file."""
        for trajectory in self._iter_json_file(file_path):
            return trajectory
        return None

    def _iter_json_file(self, file_path: Path) -> Generator[dict, None, None]:
        """Iterate over trajectories in a JSON or JSONL file."""
        if file_path.suffix == ".jsonl":
            yield from self._iter_jsonl(file_path)
        else:
            yield from self._iter_json(file_path)

    def _iter_json(self, file_path: Path) -> Generator[dict, None, None]:
        """Iterate over trajectories in a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both array and single object formats
            if isinstance(data, list):
                yield from data
            else:
                yield data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {file_path}: {e}")

    def _iter_jsonl(self, file_path: Path) -> Generator[dict, None, None]:
        """Iterate over trajectories in a JSONL file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping malformed line in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to read JSONL file {file_path}: {e}")

    def _iter_zip(self, zip_path: Path) -> Generator[dict, None, None]:
        """Iterate over trajectories in a ZIP archive."""
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if not name.endswith(('.json', '.jsonl')):
                    continue

                try:
                    with zf.open(name) as f:
                        content = f.read().decode('utf-8')

                    # Determine format
                    if name.endswith('.jsonl'):
                        for line in content.split('\n'):
                            if line.strip():
                                try:
                                    yield json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                    else:
                        try:
                            data = json.loads(content)
                            if isinstance(data, list):
                                yield from data
                            else:
                                yield data
                        except json.JSONDecodeError:
                            continue
                except Exception as e:
                    logger.warning(f"Skipping file {name} in ZIP: {e}")

    def _iter_gzip(self, gz_path: Path) -> Generator[dict, None, None]:
        """Iterate over trajectories in a gzip compressed file."""
        try:
            with gzip.open(gz_path, 'rt') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read gzip file {gz_path}: {e}")

    def _iter_directory(self, dir_path: Path) -> Generator[dict, None, None]:
        """Iterate over all trajectories in a directory."""
        for json_file in dir_path.rglob("*.json"):
            yield from self._iter_json(json_file)
        for jsonl_file in dir_path.rglob("*.jsonl"):
            yield from self._iter_jsonl(jsonl_file)


def load_osworld_dataset(
    path: str,
    filter_model: Optional[str] = None,
    filter_task: Optional[str] = None,
    limit: Optional[int] = None
) -> Generator[dict[str, Any], None, None]:
    """
    Convenience function to load OSWorld trajectories.

    Args:
        path: Path to the dataset.
        filter_model: Optional model filter.
        filter_task: Optional task filter.
        limit: Optional limit on number of trajectories.

    Yields:
        Trajectory dictionaries.
    """
    loader = OSWorldLoader(path)
    yield from loader.load(path, filter_model, filter_task, limit)


def inspect_osworld_dataset(path: str, max_samples: int = 100) -> DatasetInfo:
    """
    Convenience function to inspect an OSWorld dataset.

    Args:
        path: Path to the dataset.
        max_samples: Maximum samples for schema detection.

    Returns:
        DatasetInfo with schema and statistics.
    """
    loader = OSWorldLoader()
    return loader.inspect(path, max_samples)
