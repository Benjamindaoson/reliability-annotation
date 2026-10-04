"""
Human Gold Agreement Analysis

Analyzes agreement between Human Gold annotators for Schema v3.

Output metrics:
- Cohen's kappa for failure mechanism
- Onset step exact match, ±1, ±2, MAE
- Cohen's kappa for failure recognition
- Cohen's kappa for recovery attempt
- Cohen's kappa for recovery outcome
- UNCLEAR rate

Usage:
    python scripts/analyze_human_gold_agreement.py
    python scripts/analyze_human_gold_agreement.py --gold_file data/annotation_db/annotations.jsonl
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation.schema_v3 import (
    AnnotationRecordV3, HasConsequentialFailure, FirstFailureMechanism,
    FailureRecognized, RecognitionFailure, RecoveryAttempted, RecoveryOutcome
)


def cohen_kappa(ratings1: list, ratings2: list) -> float:
    """Calculate Cohen's kappa for two raters."""
    if len(ratings1) != len(ratings2):
        return None

    n = len(ratings1)
    if n == 0:
        return None

    # Agreement
    n_agreement = sum(1 for r1, r2 in zip(ratings1, ratings2) if r1 == r2)
    p_o = n_agreement / n

    # Expected
    categories = set(ratings1) | set(ratings2)
    p_j1 = [sum(1 for r in ratings1 if r == c) / n for c in categories]
    p_j2 = [sum(1 for r in ratings2 if r == c) / n for c in categories]
    p_e = sum(p1 * p2 for p1, p2 in zip(p_j1, p_j2))

    if p_e == 1.0:
        return 1.0

    kappa = (p_o - p_e) / (1 - p_e)
    return kappa


def exact_match_rate(values1: list, values2: list) -> float:
    """Calculate exact match rate."""
    if len(values1) != len(values2):
        return None
    matches = sum(1 for v1, v2 in zip(values1, values2) if v1 == v2)
    return matches / len(values1)


def within_n_rate(values1: list, values2: list, n: int) -> float:
    """Calculate within-n rate."""
    if len(values1) != len(values2):
        return None
    matches = sum(1 for v1, v2 in zip(values1, values2) if v1 is not None and v2 is not None and abs(v1 - v2) <= n)
    valid = sum(1 for v1, v2 in zip(values1, values2) if v1 is not None and v2 is not None)
    return matches / valid if valid > 0 else None


def mean_absolute_error(values1: list, values2: list) -> Optional[float]:
    """Calculate MAE for numeric values."""
    pairs = [(v1, v2) for v1, v2 in zip(values1, values2) if v1 is not None and v2 is not None]
    if not pairs:
        return None
    return sum(abs(v1 - v2) for v1, v2 in pairs) / len(pairs)


def load_human_gold_annotations(file_path: str) -> dict[str, list[AnnotationRecordV3]]:
    """Load annotations grouped by trajectory, only HUMAN annotators."""
    annotations_by_trajectory = defaultdict(list)

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = AnnotationRecordV3.from_dict(json.loads(line))

            # Only include human annotations
            if record.annotator_type.value == "HUMAN":
                annotations_by_trajectory[record.trajectory_id].append(record)

    return annotations_by_trajectory


def analyze_mechanism_agreement(annotations_by_traj: dict) -> dict:
    """Analyze agreement on failure mechanism (SELECTION vs EXECUTION)."""
    trajectories_with_multiple = {
        traj_id: anns for traj_id, anns in annotations_by_traj.items()
        if len(anns) >= 2
    }

    if not trajectories_with_multiple:
        return {"error": "No trajectories with 2+ human annotators"}

    results = []
    for traj_id, anns in trajectories_with_multiple.items():
        mechanisms = [a.first_failure_mechanism.value for a in anns]
        results.append(mechanisms)

    # Get unique annotator pairs
    kappa_values = []
    for traj_id, anns in trajectories_with_multiple.items():
        if len(anns) >= 2:
            # For 2 annotators
            if len(anns) == 2:
                ratings1 = [a.first_failure_mechanism.value for a in anns]
                ratings2 = [a.first_failure_mechanism.value for a in anns]
                kappa = cohen_kappa(ratings1[:1], ratings2[1:])
                if kappa is not None:
                    kappa_values.append(kappa)

    # Simple agreement rate
    agreements = sum(1 for r in results if len(set(r)) == 1)
    agreement_rate = agreements / len(results) if results else 0

    # Distribution
    all_mechanisms = [m for r in results for m in r]
    mechanism_counts = Counter(all_mechanisms)

    return {
        "n_trajectories": len(trajectories_with_multiple),
        "agreement_rate": round(agreement_rate, 3),
        "avg_kappa": round(sum(kappa_values) / len(kappa_values), 3) if kappa_values else None,
        "mechanism_distribution": dict(mechanism_counts)
    }


def analyze_onset_step_agreement(annotations_by_traj: dict) -> dict:
    """Analyze agreement on first failure step."""
    trajectories_with_multiple = {}

    for traj_id, anns in annotations_by_traj.items():
        valid_anns = [a for a in anns if a.first_consequential_failure_step is not None]
        if len(valid_anns) >= 2:
            trajectories_with_multiple[traj_id] = valid_anns

    if not trajectories_with_multiple:
        return {"error": "No trajectories with valid onset steps"}

    exact_matches = 0
    total_pairs = 0
    mae_sum = 0
    mae_count = 0

    for traj_id, anns in trajectories_with_multiple.items():
        steps = [a.first_consequential_failure_step for a in anns]

        if len(set(steps)) == 1:
            exact_matches += 1
        total_pairs += 1

        for i, s1 in enumerate(steps):
            for s2 in steps[i+1:]:
                if s1 is not None and s2 is not None:
                    mae_sum += abs(s1 - s2)
                    mae_count += 1

    mae = mae_sum / mae_count if mae_count > 0 else 0
    exact_rate = exact_matches / total_pairs if total_pairs > 0 else 0

    # Calculate within-1 and within-2 from pairs
    within_1 = 0
    within_2 = 0
    pair_total = 0

    for traj_id, anns in trajectories_with_multiple.items():
        steps = [a.first_consequential_failure_step for a in anns]
        for i, s1 in enumerate(steps):
            for s2 in steps[i+1:]:
                if s1 is not None and s2 is not None:
                    if abs(s1 - s2) <= 1:
                        within_1 += 1
                    if abs(s1 - s2) <= 2:
                        within_2 += 1
                    pair_total += 1

    return {
        "n_trajectories": len(trajectories_with_multiple),
        "n_pairs": pair_total,
        "exact_match_rate": round(exact_rate, 3),
        "within_1_rate": round(within_1 / pair_total, 3) if pair_total > 0 else None,
        "within_2_rate": round(within_2 / pair_total, 3) if pair_total > 0 else None,
        "mae": round(mae, 2)
    }


def analyze_recognition_agreement(annotations_by_traj: dict) -> dict:
    """Analyze agreement on failure recognition."""
    trajectories_with_multiple = {}

    for traj_id, anns in annotations_by_traj.items():
        valid_anns = [a for a in anns if a.failure_recognized.value in ["YES", "NO", "UNCLEAR"]]
        if len(valid_anns) >= 2:
            trajectories_with_multiple[traj_id] = valid_anns

    if not trajectories_with_multiple:
        return {"error": "No trajectories with recognition annotations"}

    kappa_values = []
    agreements = 0
    total = 0

    for traj_id, anns in trajectories_with_multiple.items():
        recognitions = [a.failure_recognized.value for a in anns]
        if len(anns) == 2:
            kappa = cohen_kappa(recognitions[:1], recognitions[1:])
            if kappa is not None:
                kappa_values.append(kappa)
        if len(set(recognitions)) == 1:
            agreements += 1
        total += 1

    return {
        "n_trajectories": len(trajectories_with_multiple),
        "agreement_rate": round(agreements / total, 3) if total > 0 else None,
        "avg_kappa": round(sum(kappa_values) / len(kappa_values), 3) if kappa_values else None
    }


def analyze_recovery_agreement(annotations_by_traj: dict) -> dict:
    """Analyze agreement on recovery attempt and outcome."""
    trajectories_with_multiple = {}

    for traj_id, anns in annotations_by_traj.items():
        valid_anns = [a for a in anns if a.recovery_attempted.value in ["YES", "NO", "UNCLEAR"]]
        if len(valid_anns) >= 2:
            trajectories_with_multiple[traj_id] = valid_anns

    if not trajectories_with_multiple:
        return {"error": "No trajectories with recovery annotations"}

    kappa_values_attempt = []
    kappa_values_outcome = []
    agreements_attempt = 0
    agreements_outcome = 0
    total = 0

    for traj_id, anns in trajectories_with_multiple.items():
        attempts = [a.recovery_attempted.value for a in anns]
        outcomes = [a.recovery_outcome.value for a in anns if a.recovery_outcome.value != "NOT_ATTEMPTED"]

        if len(anns) == 2:
            kappa_att = cohen_kappa(attempts[:1], attempts[1:])
            if kappa_att is not None:
                kappa_values_attempt.append(kappa_att)

        if len(set(attempts)) == 1:
            agreements_attempt += 1

        if len(outcomes) >= 2:
            if len(outcomes) == 2:
                kappa_out = cohen_kappa(outcomes[:1], outcomes[1:])
                if kappa_out is not None:
                    kappa_values_outcome.append(kappa_out)
            if len(set(outcomes)) == 1:
                agreements_outcome += 1

        total += 1

    return {
        "n_trajectories": len(trajectories_with_multiple),
        "attempt_agreement_rate": round(agreements_attempt / total, 3) if total > 0 else None,
        "attempt_avg_kappa": round(sum(kappa_values_attempt) / len(kappa_values_attempt), 3) if kappa_values_attempt else None,
        "outcome_agreement_rate": round(agreements_outcome / total, 3) if total > 0 else None,
        "outcome_avg_kappa": round(sum(kappa_values_outcome) / len(kappa_values_outcome), 3) if kappa_values_outcome else None
    }


def analyze_unclear_rate(annotations_by_traj: dict) -> dict:
    """Analyze UNCLEAR rates."""
    total = 0
    unclear_counts = defaultdict(int)

    for traj_id, anns in annotations_by_traj.items():
        for ann in anns:
            total += 1

            if ann.has_consequential_failure.value == "UNCLEAR":
                unclear_counts["has_consequential_failure"] += 1
            if ann.first_failure_mechanism.value == "UNCERTAIN":
                unclear_counts["first_failure_mechanism"] += 1
            if ann.failure_recognized.value == "UNCLEAR":
                unclear_counts["failure_recognized"] += 1
            if ann.recognition_failure.value == "UNCLEAR":
                unclear_counts["recognition_failure"] += 1
            if ann.recovery_attempted.value == "UNCLEAR":
                unclear_counts["recovery_attempted"] += 1
            if ann.recovery_outcome.value == "UNCLEAR":
                unclear_counts["recovery_outcome"] += 1

    return {
        field: round(count / total, 3) if total > 0 else None
        for field, count in unclear_counts.items()
    }


def generate_report(gold_file: str) -> dict:
    """Generate full Human Gold agreement report."""
    print("=" * 70)
    print("Human Gold Agreement Analysis - Schema v3")
    print("=" * 70)

    # Load annotations
    annotations_by_traj = load_human_gold_annotations(gold_file)

    print(f"\nLoaded {sum(len(anns) for anns in annotations_by_traj.values())} human annotations")
    print(f"Across {len(annotations_by_traj)} trajectories")

    n_multi = sum(1 for anns in annotations_by_traj.values() if len(anns) >= 2)
    print(f"Trajectories with 2+ annotators: {n_multi}")

    if n_multi == 0:
        print("\n⚠️  No trajectories with 2+ human annotators yet.")
        print("Human Gold calibration requires at least 2 annotators per trajectory.")
        return {"error": "Insufficient data for agreement analysis"}

    # Analyze
    print("\n" + "-" * 40)
    print("Analysis Results")
    print("-" * 40)

    # Gate criteria
    print("\n📊 Gate Criteria:")

    mechanism_results = analyze_mechanism_agreement(annotations_by_traj)
    if "error" not in mechanism_results:
        print(f"\n1. Onset Mechanism Agreement:")
        print(f"   Agreement Rate: {mechanism_results['agreement_rate']:.1%}")
        print(f"   Cohen's Kappa: {mechanism_results.get('avg_kappa', 'N/A')}")

        gate_mechanism = mechanism_results['agreement_rate'] >= 0.8
        print(f"   Gate (>=80%): {'✅ PASS' if gate_mechanism else '❌ FAIL'}")

    onset_results = analyze_onset_step_agreement(annotations_by_traj)
    if "error" not in onset_results:
        print(f"\n2. Onset Step Agreement:")
        print(f"   Exact Match: {onset_results['exact_match_rate']:.1%}")
        print(f"   Within ±1: {onset_results.get('within_1_rate', 'N/A'):.1%}")
        print(f"   Within ±2: {onset_results.get('within_2_rate', 'N/A'):.1%}")
        print(f"   MAE: {onset_results['mae']} steps")

        gate_onset = onset_results.get('within_1_rate', 0) >= 0.8
        print(f"   Gate (±1 >=80%): {'✅ PASS' if gate_onset else '❌ FAIL'}")

    recognition_results = analyze_recognition_agreement(annotations_by_traj)
    if "error" not in recognition_results:
        print(f"\n3. Failure Recognition Agreement:")
        print(f"   Agreement Rate: {recognition_results['agreement_rate']:.1%}")
        print(f"   Cohen's Kappa: {recognition_results.get('avg_kappa', 'N/A')}")

        gate_recognition = recognition_results['agreement_rate'] >= 0.8
        print(f"   Gate (>=80%): {'✅ PASS' if gate_recognition else '❌ FAIL'}")

    recovery_results = analyze_recovery_agreement(annotations_by_traj)
    if "error" not in recovery_results:
        print(f"\n4. Recovery Agreement:")
        print(f"   Attempt Agreement: {recovery_results['attempt_agreement_rate']:.1%}")
        print(f"   Outcome Agreement: {recovery_results.get('outcome_agreement_rate', 'N/A'):.1%}")

    unclear_results = analyze_unclear_rate(annotations_by_traj)
    if unclear_results:
        print(f"\n5. UNCLEAR Rates:")
        for field, rate in unclear_results.items():
            print(f"   {field}: {rate:.1%}")

    # Overall gate
    overall_gate = (
        mechanism_results.get('agreement_rate', 0) >= 0.8 and
        onset_results.get('within_1_rate', 0) >= 0.8 and
        recognition_results.get('agreement_rate', 0) >= 0.8
    )

    print("\n" + "=" * 40)
    print(f"OVERALL GATE: {'✅ PASSED' if overall_gate else '❌ NOT PASSED'}")
    print("=" * 40)

    return {
        "mechanism_agreement": mechanism_results,
        "onset_step_agreement": onset_results,
        "recognition_agreement": recognition_results,
        "recovery_agreement": recovery_results,
        "unclear_rates": unclear_results,
        "overall_gate_passed": overall_gate
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze Human Gold agreement")
    parser.add_argument("--gold_file", type=str,
                       default="data/annotation_db/annotations.jsonl",
                       help="Path to Human Gold annotations file")
    parser.add_argument("--output", type=str,
                       default="results/human_gold_agreement.json",
                       help="Output path for report")
    args = parser.parse_args()

    report = generate_report(args.gold_file)

    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
