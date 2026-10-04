#!/usr/bin/env python3
"""
Trajectory analysis script.

Analyzes OSWorld trajectories and generates statistics.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.data_loader import OSWorldLoader
from src.trajectory_analyzer.analysis import (
    TrajectoryStatisticsGenerator,
    print_statistics,
)
from src.trajectory_analyzer.analysis import BatchCandidateAnalyzer


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def analyze_trajectories(
    path: str,
    output_dir: str,
    find_candidates: bool = True,
    limit: int = None
):
    """Run full trajectory analysis."""
    logger = logging.getLogger(__name__)

    # Load trajectories
    logger.info(f"Loading trajectories from: {path}")
    loader = OSWorldLoader(path)

    trajectories = []
    for i, trajectory in enumerate(loader.load(path)):
        trajectories.append(trajectory)
        if limit and i >= limit - 1:
            break

        if (i + 1) % 100 == 0:
            logger.info(f"Loaded {i + 1} trajectories...")

    logger.info(f"Loaded {len(trajectories)} trajectories")

    # Generate statistics
    logger.info("Generating statistics...")
    stats_gen = TrajectoryStatisticsGenerator()

    for raw_trajectory in trajectories:
        stats_gen.add_raw_trajectory(raw_trajectory)

    stats = stats_gen.compute_statistics()
    print_statistics(stats)

    # Export statistics
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "trajectory_stats.json"
    csv_path = output_path / "trajectory_stats.csv"

    stats_gen.export_json(str(json_path))
    stats_gen.export_csv(str(csv_path))

    logger.info(f"Statistics exported to {output_dir}")

    # Find candidate failures if requested
    if find_candidates:
        logger.info("Finding candidate failure points...")
        candidate_analyzer = BatchCandidateAnalyzer()
        candidate_results = candidate_analyzer.analyze_trajectories(trajectories)

        candidates_path = output_path / "candidate_failures.json"
        candidate_analyzer.export_results(str(candidates_path))

        high_conf = candidate_analyzer.get_high_confidence_candidates(threshold=0.7)
        logger.info(f"Found {len(high_conf)} high-confidence candidates")

        return stats, candidate_results

    return stats, None


def main():
    parser = argparse.ArgumentParser(
        description="Analyze OSWorld trajectories."
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
        default="results/reports",
        help="Output directory for reports"
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
        help="Limit number of trajectories to analyze"
    )
    parser.add_argument(
        "--no-candidates",
        action="store_true",
        help="Skip candidate failure detection"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Check path
    if not Path(args.path).exists():
        logger.error(f"Path not found: {args.path}")
        logger.info("Please specify a valid path with --path or place data in data/raw/")
        sys.exit(1)

    try:
        stats, candidates = analyze_trajectories(
            args.path,
            args.output,
            find_candidates=not args.no_candidates,
            limit=args.limit
        )

        print(f"\n[OK] Analysis complete!")
        print(f"  Reports: {args.output}")
        print(f"  - trajectory_stats.json")
        print(f"  - trajectory_stats.csv")
        if candidates:
            print(f"  - candidate_failures.json")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
