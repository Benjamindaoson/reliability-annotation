"""
Multi-Annotator Agreement Analysis

Calculates agreement metrics for:
- Failure type (Fleiss kappa)
- First failure step (MAE)
- Detection (Cohen kappa)

Usage:
    python scripts/analyze_agreement.py
    python scripts/analyze_agreement.py --trajectory_id chrome/xxx
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Optional
import sys
import math

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation.schema import (
    AnnotationRecord, FailureType, AgentDetected
)


def fleiss_kappa(annotations: list[list[int]], n_categories: int) -> float:
    """
    Calculate Fleiss' kappa for inter-rater agreement.

    Args:
        annotations: List of lists, where each inner list is the ratings for one subject
                     Each rating is an integer category index (0 to n_categories-1)
        n_categories: Number of possible categories

    Returns:
        Fleiss' kappa coefficient
    """
    n_subjects = len(annotations)
    if n_subjects == 0:
        return 0.0

    # Count raters per subject
    n_raters = [len(ratings) for ratings in annotations]
    if len(set(n_raters)) == 1:
        n = n_raters[0]
    else:
        # Use average if different
        n = sum(n_raters) / len(n_raters)

    # Count agreements
    p_j = [0.0] * n_categories
    for ratings in annotations:
        for rating in ratings:
            if 0 <= rating < n_categories:
                p_j[rating] += 1

    p_j = [p / (n_subjects * n) for p in p_j]

    # Calculate observed agreement
    p_o = 0.0
    for ratings in annotations:
        if len(ratings) < 2:
            continue
        # Count categories for this subject
        category_counts = defaultdict(int)
        for rating in ratings:
            category_counts[rating] += 1
        # Sum of n_i * (n_i - 1)
        sum_ni = 0
        for count in category_counts.values():
            sum_ni += count * (count - 1)
        p_o += sum_ni / (n * (n - 1))

    p_o /= n_subjects

    # Calculate expected agreement
    p_e = sum(p * p for p in p_j)

    # Fleiss' kappa
    if p_e == 1.0:
        return 1.0
    kappa = (p_o - p_e) / (1 - p_e)

    return kappa


def cohen_kappa(ratings1: list[int], ratings2: list[int]) -> float:
    """
    Calculate Cohen's kappa for two raters.

    Args:
        ratings1: Ratings from first rater
        ratings2: Ratings from second rater

    Returns:
        Cohen's kappa coefficient
    """
    if len(ratings1) != len(ratings2):
        raise ValueError("Ratings must have same length")

    n = len(ratings1)
    if n == 0:
        return 0.0

    # Count agreements
    n_agreement = sum(1 for r1, r2 in zip(ratings1, ratings2) if r1 == r2)
    p_o = n_agreement / n

    # Count expected agreement
    categories = set(ratings1) | set(ratings2)
    p_j1 = [sum(1 for r in ratings1 if r == c) / n for c in categories]
    p_j2 = [sum(1 for r in ratings2 if r == c) / n for c in categories]
    p_e = sum(p1 * p2 for p1, p2 in zip(p_j1, p_j2))

    if p_e == 1.0:
        return 1.0

    kappa = (p_o - p_e) / (1 - p_e)
    return kappa


def mean_absolute_error(values1: list[float], values2: list[float]) -> float:
    """Calculate mean absolute error between two sets of values"""
    if len(values1) != len(values2):
        raise ValueError("Lists must have same length")
    return sum(abs(v1 - v2) for v1, v2 in zip(values1, values2)) / len(values1)


def exact_match_rate(values1: list[int], values2: list[int]) -> float:
    """Calculate exact match rate"""
    if len(values1) != len(values2):
        raise ValueError("Lists must have same length")
    matches = sum(1 for v1, v2 in zip(values1, values2) if v1 == v2)
    return matches / len(values1)


def load_all_annotations() -> dict[str, list[AnnotationRecord]]:
    """Load all annotations grouped by trajectory_id"""
    annotations_by_trajectory = defaultdict(list)

    # Load from all sources
    sources = ["claude", "gpt", "gemini", "human"]
    for source in sources:
        source_dir = Path(f"data/annotations/raw/{source}")
        if not source_dir.exists():
            continue

        for file in source_dir.glob("*.jsonl"):
            records = []
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        records.append(AnnotationRecord.from_dict(json.loads(line)))

            for record in records:
                annotations_by_trajectory[record.trajectory_id].append(record)

    return annotations_by_trajectory


def analyze_failure_type_agreement(annotations_by_traj: dict) -> dict:
    """Analyze agreement on failure type"""
    # Group by trajectory
    trajectories_with_multiple = {}

    for traj_id, anns in annotations_by_traj.items():
        if len(anns) >= 2:  # Need at least 2 annotators
            trajectories_with_multiple[traj_id] = anns

    if not trajectories_with_multiple:
        return {
            "n_trajectories": 0,
            "n_annotators_per_trajectory": [],
            "fleiss_kappa": None,
            "agreement_rate": None,
            "failure_type_distribution": {}
        }

    # Prepare data for Fleiss kappa
    failure_type_map = {ft.value: i for i, ft in enumerate(FailureType)}
    annotations_for_fleiss = []

    for traj_id, anns in trajectories_with_multiple.items():
        ratings = [failure_type_map.get(a.failure_type.value, 0) for a in anns]
        annotations_for_fleiss.append(ratings)

    # Calculate Fleiss kappa
    n_categories = len(FailureType)
    kappa = fleiss_kappa(annotations_for_fleiss, n_categories)

    # Calculate agreement rate
    agreements = 0
    total = 0
    for ratings in annotations_for_fleiss:
        if len(set(ratings)) == 1:
            agreements += 1
        total += 1
    agreement_rate = agreements / total if total > 0 else 0

    # Failure type distribution
    all_types = [a.failure_type.value for anns in annotations_by_traj.values() for a in anns]
    type_counts = defaultdict(int)
    for t in all_types:
        type_counts[t] += 1

    return {
        "n_trajectories_with_2plus_annotators": len(trajectories_with_multiple),
        "n_annotators_per_trajectory": [len(anns) for anns in trajectories_with_multiple.values()],
        "fleiss_kappa": round(kappa, 3),
        "agreement_rate": round(agreement_rate, 3),
        "failure_type_distribution": dict(type_counts),
        "interpretation": interpret_kappa(kappa)
    }


def analyze_first_failure_step_agreement(annotations_by_traj: dict) -> dict:
    """Analyze agreement on first failure step"""
    trajectories_with_multiple = {}

    for traj_id, anns in annotations_by_traj.items():
        # Filter out uncertain or missing steps
        valid_anns = [a for a in anns if a.first_consequential_failure_step is not None]
        if len(valid_anns) >= 2:
            trajectories_with_multiple[traj_id] = valid_anns

    if not trajectories_with_multiple:
        return {
            "n_trajectories": 0,
            "exact_match_rate": None,
            "mean_absolute_error": None
        }

    # Calculate pairwise agreement
    exact_matches = 0
    total_pairs = 0
    mae_sum = 0
    mae_count = 0

    for traj_id, anns in trajectories_with_multiple.items():
        steps = [a.first_consequential_failure_step for a in anns]
        avg_step = sum(steps) / len(steps)

        # Exact matches
        if len(set(steps)) == 1:
            exact_matches += 1
        total_pairs += 1

        # MAE (using distance from mean)
        mae_sum += sum(abs(s - avg_step) for s in steps)
        mae_count += len(steps)

    exact_match_rate = exact_matches / total_pairs if total_pairs > 0 else 0
    mae = mae_sum / mae_count if mae_count > 0 else 0

    return {
        "n_trajectories": len(trajectories_with_multiple),
        "exact_match_rate": round(exact_match_rate, 3),
        "mean_absolute_error": round(mae, 2),
        "interpretation": f"{exact_match_rate*100:.1f}% exact match, avg {mae:.1f} steps off"
    }


def analyze_detection_agreement(annotations_by_traj: dict) -> dict:
    """Analyze agreement on agent detection"""
    detection_map = {"YES": 0, "NO": 1, "UNCLEAR": 2}

    trajectories_with_multiple = {}
    for traj_id, anns in annotations_by_traj.items():
        valid_anns = [a for a in anns if a.agent_detected_failure.value in detection_map]
        if len(valid_anns) >= 2:
            trajectories_with_multiple[traj_id] = valid_anns

    if not trajectories_with_multiple:
        return {
            "n_trajectories": 0,
            "cohen_kappa": None,
            "agreement_rate": None
        }

    # Calculate agreement for each pair
    all_detections = []
    for anns in trajectories_with_multiple.values():
        detections = [detection_map[a.agent_detected_failure.value] for a in anns]
        all_detections.append(detections)

    # Use Fleiss kappa for multiple raters
    kappa = fleiss_kappa(all_detections, 3)

    # Agreement rate
    agreements = sum(1 for d in all_detections if len(set(d)) == 1)
    agreement_rate = agreements / len(all_detections) if all_detections else 0

    return {
        "n_trajectories": len(trajectories_with_multiple),
        "fleiss_kappa_detection": round(kappa, 3),
        "agreement_rate": round(agreement_rate, 3),
        "interpretation": interpret_kappa(kappa)
    }


def analyze_confidence_vs_agreement(annotations_by_traj: dict) -> dict:
    """Analyze whether high confidence correlates with agreement"""
    high_confidence_agreements = 0
    high_confidence_total = 0
    low_confidence_agreements = 0
    low_confidence_total = 0

    for traj_id, anns in annotations_by_traj.items():
        if len(anns) < 2:
            continue

        confidences = [a.confidence for a in anns]
        avg_confidence = sum(confidences) / len(confidences)

        # Check if all agree on failure type
        types = [a.failure_type.value for a in anns]
        agrees = len(set(types)) == 1

        if avg_confidence >= 0.7:
            high_confidence_total += 1
            if agrees:
                high_confidence_agreements += 1
        elif avg_confidence <= 0.5:
            low_confidence_total += 1
            if agrees:
                low_confidence_agreements += 1

    return {
        "high_confidence_agreement_rate": round(high_confidence_agreements / high_confidence_total, 3) if high_confidence_total > 0 else None,
        "high_confidence_count": high_confidence_total,
        "low_confidence_agreement_rate": round(low_confidence_agreements / low_confidence_total, 3) if low_confidence_total > 0 else None,
        "low_confidence_count": low_confidence_total,
    }


def interpret_kappa(kappa: float) -> str:
    """Interpret kappa coefficient"""
    if kappa < 0:
        return "Poor (less than chance)"
    elif kappa < 0.20:
        return "Slight"
    elif kappa < 0.40:
        return "Fair"
    elif kappa < 0.60:
        return "Moderate"
    elif kappa < 0.80:
        return "Substantial"
    else:
        return "Almost Perfect"


def generate_report(output_dir: Path):
    """Generate full agreement analysis report"""
    print("=" * 70)
    print("Multi-Annotator Agreement Analysis")
    print("=" * 70)

    # Load annotations
    annotations_by_traj = load_all_annotations()

    n_total_trajectories = len(annotations_by_traj)
    n_total_annotations = sum(len(anns) for anns in annotations_by_traj.values())

    print(f"\nDataset Overview:")
    print(f"  Total trajectories: {n_total_trajectories}")
    print(f"  Total annotations: {n_total_annotations}")
    print(f"  Avg annotations per trajectory: {n_total_annotations/n_total_trajectories:.2f}" if n_total_trajectories > 0 else "  N/A")

    # Check for multi-annotator trajectories
    multi_annotator = sum(1 for anns in annotations_by_traj.values() if len(anns) >= 2)
    print(f"  Trajectories with 2+ annotators: {multi_annotator}")

    # Analysis
    print("\n" + "=" * 70)
    print("Analysis Results")
    print("=" * 70)

    # Failure type
    ft_analysis = analyze_failure_type_agreement(annotations_by_traj)
    print("\n1. Failure Type Agreement:")
    print(f"   Fleiss Kappa: {ft_analysis['fleiss_kappa']}")
    print(f"   Interpretation: {ft_analysis['interpretation']}")
    print(f"   Agreement Rate: {ft_analysis['agreement_rate']}")

    # First failure step
    step_analysis = analyze_first_failure_step_agreement(annotations_by_traj)
    print("\n2. First Failure Step Agreement:")
    print(f"   Exact Match Rate: {step_analysis['exact_match_rate']}")
    print(f"   Mean Absolute Error: {step_analysis['mean_absolute_error']}")
    print(f"   {step_analysis['interpretation']}")

    # Detection
    det_analysis = analyze_detection_agreement(annotations_by_traj)
    print("\n3. Agent Detection Agreement:")
    print(f"   Fleiss Kappa: {det_analysis['fleiss_kappa_detection']}")
    print(f"   Agreement Rate: {det_analysis['agreement_rate']}")
    print(f"   Interpretation: {det_analysis['interpretation']}")

    # Confidence calibration
    conf_analysis = analyze_confidence_vs_agreement(annotations_by_traj)
    print("\n4. Confidence Calibration:")
    if conf_analysis['high_confidence_count']:
        print(f"   High Confidence (>=0.7) Agreement: {conf_analysis['high_confidence_agreement_rate']} ({conf_analysis['high_confidence_count']} cases)")
    if conf_analysis['low_confidence_count']:
        print(f"   Low Confidence (<=0.5) Agreement: {conf_analysis['low_confidence_agreement_rate']} ({conf_analysis['low_confidence_count']} cases)")

    # Save report
    report = {
        "generated_at": str(Path.cwd()),
        "dataset_overview": {
            "total_trajectories": n_total_trajectories,
            "total_annotations": n_total_annotations,
            "multi_annotator_trajectories": multi_annotator
        },
        "failure_type_agreement": ft_analysis,
        "first_failure_step_agreement": step_analysis,
        "detection_agreement": det_analysis,
        "confidence_calibration": conf_analysis
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "agreement_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n\nReport saved to: {report_file}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Analyze annotator agreement")
    parser.add_argument("--output_dir", type=str, default="results/annotation_agreement",
                       help="Output directory for reports")
    args = parser.parse_args()

    generate_report(Path(args.output_dir))


if __name__ == "__main__":
    main()
