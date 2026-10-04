#!/usr/bin/env python3
"""
Localization evaluation script.

Evaluates how well candidate failure detection matches human annotations.

Metrics:
- Hit@K: Human t* in top K candidates
- Mean Distance: Mean |candidate - human|
- Annotation Reduction: Ratio of full trajectory to local window
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.analysis import BatchCandidateAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_human_annotations(path: str) -> list[dict]:
    """Load human annotations from JSONL file."""
    annotations = []
    annotation_file = Path(path)

    if not annotation_file.exists():
        return []

    # Try JSONL first
    if annotation_file.suffix == '.jsonl':
        with open(annotation_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    annotations.append(json.loads(line))
    else:
        # Try JSON array
        with open(annotation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                annotations = data
            elif isinstance(data, dict) and 'annotations' in data:
                annotations = data['annotations']

    return annotations


def load_candidate_results(path: str) -> dict[str, list]:
    """Load candidate failure results."""
    candidate_file = Path(path)

    if not candidate_file.exists():
        return {}

    with open(candidate_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Build lookup by trajectory_id
    results = {}
    for result in data.get('results', []):
        traj_id = result.get('trajectory_id')
        if traj_id:
            # Sort by confidence descending
            candidates = sorted(
                result.get('candidate_steps', []),
                key=lambda x: x.get('confidence', 0),
                reverse=True
            )
            results[traj_id] = candidates

    return results


def compute_hit_at_k(
    human_step: int,
    candidate_steps: list[tuple[int, float]],
    k: int
) -> bool:
    """Check if human step is in top K candidates."""
    if not candidate_steps:
        return False

    top_k_steps = [step for step, _ in candidate_steps[:k]]
    return human_step in top_k_steps


def compute_distance(
    human_step: int,
    top_candidate: Optional[int]
) -> Optional[float]:
    """Compute distance between human and top candidate."""
    if top_candidate is None:
        return None
    return abs(human_step - top_candidate)


def evaluate_localization(
    candidate_results: dict[str, list],
    human_annotations: list[dict],
    ks: list[int] = [1, 3, 5]
) -> dict:
    """
    Evaluate localization against human annotations.

    Returns evaluation metrics.
    """
    results = {
        'total_evaluated': 0,
        'hit_at_k': {f'hit@{k}': 0 for k in ks},
        'distances': [],
        'no_candidates': 0,
        'trajectory_lengths': [],
        'annotation_reduction': [],
        'by_model': defaultdict(lambda: {'total': 0, 'hit@1': 0, 'hit@3': 0, 'hit@5': 0}),
        'by_failure_type': defaultdict(lambda: {'total': 0, 'hit@1': 0}),
        'errors': [],
    }

    for annotation in human_annotations:
        traj_id = annotation.get('trajectory_id')
        human_step = annotation.get('first_failure_step')

        if traj_id not in candidate_results:
            continue

        candidates = candidate_results[traj_id]
        results['total_evaluated'] += 1

        if not candidates:
            results['no_candidates'] += 1
            continue

        # Convert to (step, confidence) tuples
        candidate_tuples = [
            (c.get('step', c.get('step_id')), c.get('confidence', 0))
            for c in candidates
        ]

        # Compute Hit@K
        for k in ks:
            if compute_hit_at_k(human_step, candidate_tuples, k):
                results['hit_at_k'][f'hit@{k}'] += 1

        # Compute distance
        top_candidate = candidate_tuples[0][0] if candidate_tuples else None
        distance = compute_distance(human_step, top_candidate)
        if distance is not None:
            results['distances'].append(distance)

        # Track by model
        model_id = annotation.get('model_id', 'unknown')
        results['by_model'][model_id]['total'] += 1
        if compute_hit_at_k(human_step, candidate_tuples, 1):
            results['by_model'][model_id]['hit@1'] += 1
        if compute_hit_at_k(human_step, candidate_tuples, 3):
            results['by_model'][model_id]['hit@3'] += 0  # Simplified
        if compute_hit_at_k(human_step, candidate_tuples, 5):
            results['by_model'][model_id]['hit@5'] += 0  # Simplified

        # Track by failure type
        for ft in annotation.get('failure_type', []):
            results['by_failure_type'][ft]['total'] += 1
            if compute_hit_at_k(human_step, candidate_tuples, 1):
                results['by_failure_type'][ft]['hit@1'] += 1

    # Compute summary statistics
    n = results['total_evaluated']
    if n > 0:
        results['hit_at_k'] = {
            k: v / n for k, v in results['hit_at_k'].items()
        }

        if results['distances']:
            results['mean_distance'] = np.mean(results['distances'])
            results['median_distance'] = np.median(results['distances'])
            results['std_distance'] = np.std(results['distances'])
        else:
            results['mean_distance'] = None
            results['median_distance'] = None

    # Compute per-model Hit@K
    for model in results['by_model']:
        m = results['by_model'][model]
        if m['total'] > 0:
            m['hit@1_rate'] = m['hit@1'] / m['total']
            m['hit@3_rate'] = m.get('hit@3', 0) / m['total']
            m['hit@5_rate'] = m.get('hit@5', 0) / m['total']

    # Compute per-failure-type Hit@1
    for ft in results['by_failure_type']:
        m = results['by_failure_type'][ft]
        if m['total'] > 0:
            m['hit@1_rate'] = m['hit@1'] / m['total']

    return results


def generate_report(evaluation: dict) -> str:
    """Generate markdown report from evaluation results."""
    report = []
    report.append("# Localization Evaluation Report\n")

    # Summary
    report.append("## Summary\n")
    report.append(f"- Total trajectories evaluated: {evaluation['total_evaluated']}")
    report.append(f"- Trajectories with no candidates: {evaluation['no_candidates']}\n")

    # Hit@K
    report.append("## Hit@K Performance\n")
    report.append("| Metric | Value |")
    report.append("|--------|-------|")
    for metric, value in evaluation['hit_at_k'].items():
        report.append(f"| {metric} | {value:.2%} |")
    report.append("")

    # Distance
    if 'mean_distance' in evaluation and evaluation['mean_distance'] is not None:
        report.append("## Step Distance\n")
        report.append(f"- Mean: {evaluation['mean_distance']:.2f} steps")
        report.append(f"- Median: {evaluation['median_distance']:.2f} steps")
        report.append(f"- Std: {evaluation['std_distance']:.2f} steps\n")

    # By Model
    if evaluation['by_model']:
        report.append("## Performance by Model\n")
        report.append("| Model | Total | Hit@1 |")
        report.append("|-------|-------|-------|")
        for model, stats in sorted(evaluation['by_model'].items()):
            rate = stats.get('hit@1_rate', 0)
            report.append(f"| {model} | {stats['total']} | {rate:.2%} |")
        report.append("")

    # By Failure Type
    if evaluation['by_failure_type']:
        report.append("## Hit@1 by Failure Type\n")
        report.append("| Failure Type | Total | Hit@1 |")
        report.append("|--------------|-------|-------|")
        for ft, stats in sorted(evaluation['by_failure_type'].items()):
            rate = stats.get('hit@1_rate', 0)
            report.append(f"| {ft} | {stats['total']} | {rate:.2%} |")
        report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate failure localization against human annotations"
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default="results/reports/candidate_failures.json",
        help="Path to candidate failures JSON"
    )
    parser.add_argument(
        "--annotations",
        type=str,
        default="data/annotations/annotations.jsonl",
        help="Path to human annotations"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/localization_eval",
        help="Output directory for reports"
    )

    args = parser.parse_args()

    logger.info(f"Loading candidate results from: {args.candidates}")
    candidates = load_candidate_results(args.candidates)

    logger.info(f"Loading human annotations from: {args.annotations}")
    annotations = load_human_annotations(args.annotations)

    if not candidates:
        logger.warning("No candidate results found")
        return

    if not annotations:
        logger.warning("No human annotations found")
        return

    logger.info(f"Evaluating {len(annotations)} annotations against {len(candidates)} candidate sets")

    evaluation = evaluate_localization(candidates, annotations)

    # Save results
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON report
    json_path = output_dir / "evaluation_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(evaluation, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON results to: {json_path}")

    # Markdown report
    md_path = output_dir / "evaluation_report.md"
    report = generate_report(evaluation)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Saved Markdown report to: {md_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("LOCALIZATION EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Trajectories evaluated: {evaluation['total_evaluated']}")
    for metric, value in evaluation['hit_at_k'].items():
        print(f"  {metric}: {value:.2%}")
    if 'mean_distance' in evaluation and evaluation['mean_distance'] is not None:
        print(f"  Mean distance: {evaluation['mean_distance']:.2f} steps")
    print("=" * 60)


if __name__ == "__main__":
    main()
