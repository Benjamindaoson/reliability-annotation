#!/usr/bin/env python3
"""
Annotation export script.

Generates human-readable annotation files from trajectories.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.data_loader import OSWorldLoader
from src.trajectory_analyzer.export import BatchAnnotationExporter


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def load_candidate_results(path: str) -> list[dict]:
    """Load candidate failure results if available."""
    candidate_path = Path(path)
    if not candidate_path.exists():
        return []

    try:
        with open(candidate_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("results", [])
    except Exception as e:
        logging.warning(f"Could not load candidate results: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Export trajectories for human annotation."
    )
    parser.add_argument(
        "--path", "-p",
        type=str,
        default="data/raw",
        help="Path to dataset directory or file"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="results/annotation",
        help="Output directory for annotation files"
    )
    parser.add_argument(
        "--combined",
        type=str,
        help="Export as single combined JSON file"
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default="results/reports/candidate_failures.json",
        help="Path to candidate failures file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of trajectories to export"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Check data path
    if not Path(args.path).exists():
        logger.error(f"Data path not found: {args.path}")
        sys.exit(1)

    # Load candidate results
    candidate_results = load_candidate_results(args.candidates)
    if candidate_results:
        logger.info(f"Loaded {len(candidate_results)} candidate results")
    else:
        logger.info("No candidate results loaded (will use all trajectories)")

    # Load trajectories
    logger.info(f"Loading trajectories from: {args.path}")
    loader = OSWorldLoader(args.path)

    trajectories = []
    for i, trajectory in enumerate(loader.load(args.path)):
        trajectories.append(trajectory)
        if args.limit and i >= args.limit - 1:
            break

        if (i + 1) % 100 == 0:
            logger.info(f"Loaded {i + 1} trajectories...")

    logger.info(f"Loaded {len(trajectories)} trajectories")

    # Export annotations
    logger.info("Exporting annotations...")
    exporter = BatchAnnotationExporter()

    if args.combined:
        output_path = exporter.export_combined(
            args.combined, trajectories, candidate_results
        )
        print(f"\n[OK] Combined export: {output_path}")
    else:
        output_dir = exporter.export_to_directory(
            args.output, trajectories, candidate_results
        )
        print(f"\n[OK] Exported {len(exporter.exports)} annotation files to:")
        print(f"  {args.output}")

        # Show sample
        if exporter.exports:
            sample = exporter.exports[0]
            print(f"\nSample annotation (trajectory_{sample.trajectory_id}.json):")
            print(f"  task: {sample.task_id}")
            print(f"  model: {sample.model_id}")
            print(f"  candidate_step: {sample.candidate_step}")
            print(f"  context_before: {len(sample.context_before)} steps")
            print(f"  context_after: {len(sample.context_after)} steps")


if __name__ == "__main__":
    main()
