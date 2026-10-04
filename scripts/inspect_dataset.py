#!/usr/bin/env python3
"""
Dataset inspection script.

Inspects OSWorld trajectory files and reports their structure.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.data_loader import OSWorldLoader


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def print_dataset_info(info):
    """Print formatted dataset information."""
    print("\n" + "=" * 70)
    print("DATASET INSPECTION REPORT")
    print("=" * 70)

    print(f"\nSource: {info.source_path}")
    print(f"Format: {info.format}")
    print(f"File size: {info.file_size_mb:.2f} MB")

    print(f"\n--- Trajectories ---")
    print(f"Total trajectories: {info.total_trajectories}")

    print(f"\n--- Models ({len(info.models)}) ---")
    for model in info.models:
        print(f"  - {model}")

    print(f"\n--- Tasks ({len(info.tasks)}) ---")
    for task in info.tasks[:20]:  # Limit output
        print(f"  - {task}")
    if len(info.tasks) > 20:
        print(f"  ... and {len(info.tasks) - 20} more tasks")

    print(f"\n--- Available Fields ---")
    for field in sorted(info.fields_available):
        print(f"  - {field}")

    if info.sample_schema:
        print(f"\n--- Sample Schema (first trajectory) ---")
        # Print first level keys with types
        for key, value in info.sample_schema.items():
            value_type = type(value).__name__
            if isinstance(value, dict):
                value_type = f"dict with keys: {list(value.keys())[:5]}"
            elif isinstance(value, list):
                value_type = f"list (len={len(value)})"
            elif isinstance(value, str):
                value_type = f"str (len={len(value)})"
            print(f"  {key}: {value_type}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Inspect OSWorld trajectory dataset structure."
    )
    parser.add_argument(
        "--path", "-p",
        type=str,
        help="Path to dataset directory or file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--max-samples", "-m",
        type=int,
        default=100,
        help="Maximum trajectories to sample for schema detection (default: 100)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Save report to JSON file"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Get path
    path = args.path
    if not path:
        # Try common locations
        default_paths = [
            "data/raw",
            "data",
            "osworld_data",
            "./",
        ]
        for default_path in default_paths:
            if Path(default_path).exists():
                path = default_path
                break

    if not path:
        print("Error: No path specified and no default found.")
        print("Please specify --path or place data in data/raw/")
        sys.exit(1)

    if not Path(path).exists():
        print(f"Error: Path not found: {path}")
        sys.exit(1)

    # Inspect dataset
    logger.info(f"Inspecting dataset at: {path}")
    loader = OSWorldLoader(path)

    try:
        info = loader.inspect(path, max_samples=args.max_samples)
        print_dataset_info(info)

        # Save to file if requested
        if args.output:
            import json
            from dataclasses import asdict

            output_data = asdict(info)
            output_data["fields_available"] = list(info.fields_available)
            output_data["all_fields"] = list(info.all_fields)

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"\nReport saved to: {args.output}")

    except Exception as e:
        logger.error(f"Inspection failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
