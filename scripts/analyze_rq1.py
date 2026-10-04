#!/usr/bin/env python3
"""
RQ1 Analysis: Where do agents fail?

Generates failure distribution statistics and visualizations.

Research Question 1:
Where do long-horizon agents fail in the task pipeline?
"""

import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.data_loader import OSWorldLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_failure_dataset(path: str) -> list[dict]:
    """Load failure decomposition dataset."""
    records = []
    dataset_file = Path(path)

    if not dataset_file.exists():
        logger.warning(f"Dataset not found: {path}")
        return []

    if dataset_file.suffix == '.jsonl':
        with open(dataset_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    else:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                records = data

    return records


def load_candidate_failures(path: str) -> dict[str, list]:
    """Load candidate failure data for analysis."""
    candidates = {}
    candidate_file = Path(path)

    if not candidate_file.exists():
        return candidates

    with open(candidate_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for result in data.get('results', []):
            traj_id = result.get('trajectory_id')
            if traj_id:
                candidates[traj_id] = result.get('candidate_steps', [])

    return candidates


def analyze_failure_distribution(records: list[dict]) -> dict:
    """Analyze failure type distribution."""
    if not records:
        return {}

    # Overall distribution
    failure_types = Counter()
    for record in records:
        ft = record.get('failure_type', 'unknown')
        failure_types[ft] += 1

    total = len(records)

    distribution = {
        'total_failures': total,
        'by_type': {
            ft: {
                'count': count,
                'percentage': count / total * 100 if total > 0 else 0
            }
            for ft, count in failure_types.items()
        }
    }

    # Detection rates by failure type
    detection_by_type = defaultdict(lambda: {'detected': 0, 'total': 0})
    for record in records:
        ft = record.get('failure_type', 'unknown')
        detection_by_type[ft]['total'] += 1
        if record.get('agent_detected', False):
            detection_by_type[ft]['detected'] += 1

    distribution['detection_by_type'] = {
        ft: {
            'detected': stats['detected'],
            'total': stats['total'],
            'rate': stats['detected'] / stats['total'] if stats['total'] > 0 else 0
        }
        for ft, stats in detection_by_type.items()
    }

    return distribution


def analyze_by_model(records: list[dict]) -> dict:
    """Analyze failure distribution by model."""
    by_model = defaultdict(lambda: defaultdict(int))

    for record in records:
        model = record.get('model_id', 'unknown')
        ft = record.get('failure_type', 'unknown')
        by_model[model][ft] += 1

    # Convert to percentages
    result = {}
    for model, type_counts in by_model.items():
        total = sum(type_counts.values())
        result[model] = {
            'total': total,
            'by_type': {
                ft: count / total * 100 if total > 0 else 0
                for ft, count in type_counts.items()
            }
        }

    return dict(result)


def analyze_by_task_category(records: list[dict]) -> dict:
    """Analyze failure distribution by task category."""
    # Extract category from task_id (e.g., "osworld_file_edit_001" -> "file_edit")
    by_category = defaultdict(lambda: defaultdict(int))

    for record in records:
        task_id = record.get('task_id', 'unknown')
        # Extract category from task_id
        if '_' in task_id:
            parts = task_id.split('_')
            if len(parts) >= 2:
                category = '_'.join(parts[1:-1])  # e.g., file_edit from osworld_file_edit_001
            else:
                category = parts[1]
        else:
            category = 'other'

        ft = record.get('failure_type', 'unknown')
        by_category[category][ft] += 1

    result = {}
    for category, type_counts in by_category.items():
        total = sum(type_counts.values())
        result[category] = {
            'total': total,
            'by_type': {
                ft: count / total * 100 if total > 0 else 0
                for ft, count in type_counts.items()
            }
        }

    return dict(result)


def analyze_failure_position(records: list[dict]) -> dict:
    """Analyze where failures occur in trajectories."""
    positions = []
    relative_positions = []  # Position as fraction of trajectory

    for record in records:
        step = record.get('first_failure_step', 0)
        length = record.get('trajectory_length', 1)
        positions.append(step)
        relative_positions.append(step / length if length > 0 else 0)

    if not positions:
        return {}

    return {
        'mean_step': np.mean(positions),
        'median_step': np.median(positions),
        'std_step': np.std(positions),
        'min_step': min(positions),
        'max_step': max(positions),
        'mean_relative_position': np.mean(relative_positions),
        'median_relative_position': np.median(relative_positions),
    }


def analyze_detection_gap(records: list[dict]) -> dict:
    """Analyze the gap between failure and detection."""
    detected = [r for r in records if r.get('agent_detected', False)]
    not_detected = [r for r in records if not r.get('agent_detected', False)]

    detection_delays = []
    for r in detected:
        delay = r.get('detection_delay')
        if delay is not None:
            detection_delays.append(delay)

    return {
        'total_records': len(records),
        'detected': len(detected),
        'not_detected': len(not_detected),
        'detection_rate': len(detected) / len(records) if records else 0,
        'mean_detection_delay': np.mean(detection_delays) if detection_delays else None,
        'median_detection_delay': np.median(detection_delays) if detection_delays else None,
    }


def generate_rq1_report(
    distribution: dict,
    by_model: dict,
    by_category: dict,
    position: dict,
    detection_gap: dict
) -> str:
    """Generate RQ1 markdown report."""
    report = []
    report.append("# RQ1: Where Do Agents Fail?\n")
    report.append("## Research Question\n")
    report.append("*Where do long-horizon agents fail in the task pipeline?*\n")

    # Summary
    report.append("## Summary\n")
    report.append(f"- Total failures analyzed: {distribution.get('total_failures', 0)}\n")

    # Failure type distribution
    report.append("## Failure Type Distribution\n")
    report.append("| Failure Type | Count | Percentage |")
    report.append("|--------------|-------|------------|")
    for ft, stats in sorted(
        distribution.get('by_type', {}).items(),
        key=lambda x: -x[1]['count']
    ):
        report.append(f"| {ft} | {stats['count']} | {stats['percentage']:.1f}% |")
    report.append("")

    # Detection by type
    report.append("## Agent Detection Rate by Failure Type\n")
    report.append("| Failure Type | Detected | Total | Detection Rate |")
    report.append("|--------------|----------|-------|----------------|")
    for ft, stats in distribution.get('detection_by_type', {}).items():
        rate = stats['rate'] * 100
        report.append(f"| {ft} | {stats['detected']} | {stats['total']} | {rate:.1f}% |")
    report.append("")

    # By model
    if by_model:
        report.append("## Failure Distribution by Model\n")
        models = list(by_model.keys())
        if models:
            failure_types = list(by_model[models[0]]['by_type'].keys())
            report.append("| Model | " + " | ".join(failure_types) + " | Total |")
            report.append("|-------|" + "|".join(["---"] * (len(failure_types) + 1)) + "|")
            for model, stats in sorted(by_model.items()):
                counts = [f"{stats['by_type'].get(ft, 0):.1f}%" for ft in failure_types]
                report.append(f"| {model} | " + " | ".join(counts) + f" | {stats['total']} |")
            report.append("")

    # Failure position
    if position:
        report.append("## Failure Position in Trajectory\n")
        report.append(f"- Mean step: {position.get('mean_step', 0):.1f}")
        report.append(f"- Median step: {position.get('median_step', 0):.1f}")
        report.append(f"- Std dev: {position.get('std_step', 0):.1f}")
        report.append(f"- Mean relative position: {position.get('mean_relative_position', 0)*100:.1f}% of trajectory")
        report.append("")

    # Detection gap
    if detection_gap:
        report.append("## Failure Detection Gap\n")
        report.append(f"- Total failures: {detection_gap['total_records']}")
        report.append(f"- Agent detected: {detection_gap['detected']}")
        report.append(f"- Not detected: {detection_gap['not_detected']}")
        report.append(f"- Overall detection rate: {detection_gap['detection_rate']*100:.1f}%")
        if detection_gap['mean_detection_delay']:
            report.append(f"- Mean detection delay: {detection_gap['mean_detection_delay']:.1f} steps")
        report.append("")

    return "\n".join(report)


def generate_visualizations(records: list[dict], output_dir: Path):
    """Generate visualization data (for external plotting)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # 1. Failure type distribution (bar chart)
    failure_types = Counter(r.get('failure_type', 'unknown') for r in records)
    plt.figure(figsize=(10, 6))
    plt.bar(failure_types.keys(), failure_types.values())
    plt.xlabel('Failure Type')
    plt.ylabel('Count')
    plt.title('Failure Type Distribution')
    plt.tight_layout()
    plt.savefig(output_dir / 'failure_type_distribution.png', dpi=150)
    plt.close()

    # 2. Detection rate by type
    detection_by_type = defaultdict(lambda: {'detected': 0, 'total': 0})
    for r in records:
        ft = r.get('failure_type', 'unknown')
        detection_by_type[ft]['total'] += 1
        if r.get('agent_detected'):
            detection_by_type[ft]['detected'] += 1

    types = list(detection_by_type.keys())
    rates = [
        d['detected'] / d['total'] * 100 if d['total'] > 0 else 0
        for d in detection_by_type.values()
    ]
    plt.figure(figsize=(10, 6))
    plt.bar(types, rates)
    plt.xlabel('Failure Type')
    plt.ylabel('Detection Rate (%)')
    plt.title('Agent Detection Rate by Failure Type')
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(output_dir / 'detection_rate_by_type.png', dpi=150)
    plt.close()

    # 3. Failure position histogram
    positions = [r.get('first_failure_step', 0) for r in records]
    lengths = [r.get('trajectory_length', 1) for r in records]
    relative_pos = [p/l if l > 0 else 0 for p, l in zip(positions, lengths)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.hist(positions, bins=20, edgecolor='black')
    ax1.set_xlabel('Absolute Step')
    ax1.set_ylabel('Count')
    ax1.set_title('Failure Step Distribution')

    ax2.hist(relative_pos, bins=20, edgecolor='black')
    ax2.set_xlabel('Relative Position (fraction of trajectory)')
    ax2.set_ylabel('Count')
    ax2.set_title('Relative Failure Position')

    plt.tight_layout()
    plt.savefig(output_dir / 'failure_position_distribution.png', dpi=150)
    plt.close()

    logger.info(f"Generated visualizations in {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="RQ1 Analysis: Failure Distribution"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/processed/failure_decomposition.jsonl",
        help="Path to failure decomposition dataset"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/RQ1_failure_distribution",
        help="Output directory for results"
    )
    parser.add_argument(
        "--generate-figures",
        action="store_true",
        help="Generate visualization figures"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    records = load_failure_dataset(args.dataset)

    if not records:
        logger.error("No records found. Please generate the failure decomposition dataset first.")
        logger.info("Run: python scripts/generate_failure_dataset.py")
        return

    logger.info(f"Analyzing {len(records)} failure records")

    # Run analyses
    distribution = analyze_failure_distribution(records)
    by_model = analyze_by_model(records)
    by_category = analyze_by_task_category(records)
    position = analyze_failure_position(records)
    detection_gap = analyze_detection_gap(records)

    # Save results
    results = {
        'distribution': distribution,
        'by_model': by_model,
        'by_category': by_category,
        'position': position,
        'detection_gap': detection_gap,
    }

    json_path = output_dir / 'rq1_results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved results to {json_path}")

    # Generate report
    report = generate_rq1_report(
        distribution, by_model, by_category, position, detection_gap
    )
    md_path = output_dir / 'rq1_report.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Saved report to {md_path}")

    # Generate visualizations if requested
    if args.generate_figures:
        try:
            generate_visualizations(records, output_dir)
        except ImportError:
            logger.warning("matplotlib not available. Skipping visualizations.")

    # Print summary
    print("\n" + "=" * 60)
    print("RQ1 ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total failures: {distribution.get('total_failures', 0)}")
    print("\nFailure Distribution:")
    for ft, stats in sorted(
        distribution.get('by_type', {}).items(),
        key=lambda x: -x[1]['count']
    ):
        print(f"  {ft}: {stats['count']} ({stats['percentage']:.1f}%)")
    print(f"\nDetection Rate: {detection_gap.get('detection_rate', 0)*100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
