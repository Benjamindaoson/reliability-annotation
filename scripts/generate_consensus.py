"""
Consensus Label Generator

Generates consensus labels from multiple annotators:
1. Unanimous agreement -> accept
2. Majority agreement (2/3) -> accept
3. Severe disagreement -> send to review queue

Usage:
    python scripts/generate_consensus.py
    python scripts/generate_consensus.py --min_annotators 2 --output consensus_labels.jsonl
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation.schema import (
    AnnotationRecord, FailureType, AgentDetected, RecoveryStatus
)


class ConsensusGenerator:
    """Generates consensus labels from multiple annotations"""

    def __init__(self, min_annotators: int = 2, agreement_threshold: float = 0.66):
        """
        Args:
            min_annotators: Minimum number of annotators required
            agreement_threshold: Threshold for majority agreement (0.66 = 2/3)
        """
        self.min_annotators = min_annotators
        self.agreement_threshold = agreement_threshold

    def load_annotations(self) -> dict[str, list[AnnotationRecord]]:
        """Load all annotations grouped by trajectory"""
        annotations_by_trajectory = defaultdict(list)

        sources = ["claude", "gpt", "gemini", "human"]
        for source in sources:
            source_dir = Path(f"data/annotations/raw/{source}")
            if not source_dir.exists():
                continue

            for file in source_dir.glob("*.jsonl"):
                with open(file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            ann = AnnotationRecord.from_dict(json.loads(line))
                            annotations_by_trajectory[ann.trajectory_id].append(ann)

        return annotations_by_trajectory

    def calculate_failure_type_consensus(self, annotations: list[AnnotationRecord]) -> tuple[str, float]:
        """
        Calculate consensus on failure type.

        Returns:
            (consensus_type, agreement_score)
        """
        if not annotations:
            return "UNCERTAIN", 0.0

        types = [a.failure_type.value for a in annotations]
        type_counts = Counter(types)
        total = len(types)

        # Check for unanimous agreement
        most_common = type_counts.most_common(1)[0]
        if most_common[1] == total:
            return most_common[0], 1.0

        # Check for majority agreement
        if most_common[1] / total >= self.agreement_threshold:
            return most_common[0], most_common[1] / total

        # Severe disagreement: all different types
        if len(type_counts) == len(types):
            return "UNCERTAIN", 0.0

        # Partial disagreement
        return most_common[0], most_common[1] / total

    def calculate_step_consensus(self, annotations: list[AnnotationRecord]) -> tuple[Optional[int], float]:
        """
        Calculate consensus on first failure step.

        Returns:
            (consensus_step, agreement_score)
        """
        steps = [a.first_consequential_failure_step for a in annotations
                 if a.first_consequential_failure_step is not None]

        if not steps:
            return None, 0.0

        step_counts = Counter(steps)
        most_common = step_counts.most_common(1)[0]
        total = len(steps)

        # Check for unanimity
        if most_common[1] == total:
            return most_common[0], 1.0

        # Majority
        if most_common[1] / total >= self.agreement_threshold:
            return most_common[0], most_common[1] / total

        # Use median as fallback
        median_step = sorted(steps)[len(steps) // 2]
        return median_step, most_common[1] / total

    def calculate_detection_consensus(self, annotations: list[AnnotationRecord]) -> tuple[str, float]:
        """
        Calculate consensus on agent detection.

        Returns:
            (consensus_detection, agreement_score)
        """
        detections = [a.agent_detected_failure.value for a in annotations]
        det_counts = Counter(detections)
        total = len(detections)

        most_common = det_counts.most_common(1)[0]
        if most_common[1] / total >= self.agreement_threshold:
            return most_common[0], most_common[1] / total

        # Severe disagreement
        return "UNCLEAR", most_common[1] / total

    def is_severe_disagreement(self, annotations: list[AnnotationRecord]) -> bool:
        """
        Check for severe disagreement on failure type.

        Severe disagreement = at least 3 different failure types
        """
        types = [a.failure_type.value for a in annotations if a.failure_type != FailureType.UNCERTAIN]
        if len(set(types)) >= 3:
            return True

        # Also flag if UNCERTAIN vs strong disagreement
        uncertain_count = sum(1 for a in annotations if a.failure_type == FailureType.UNCERTAIN)
        if uncertain_count > 0 and uncertain_count < len(annotations):
            # UNCERTAIN mixed with strong opinions
            non_uncertain = [a.failure_type.value for a in annotations
                           if a.failure_type != FailureType.UNCERTAIN]
            if len(set(non_uncertain)) >= 2:
                return True

        return False

    def calculate_average_confidence(self, annotations: list[AnnotationRecord]) -> float:
        """Calculate weighted average confidence"""
        confidences = [a.confidence for a in annotations]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def merge_evidence(self, annotations: list[AnnotationRecord]) -> tuple[list[int], str]:
        """
        Merge evidence from multiple annotators.

        Returns:
            (merged_steps, merged_text)
        """
        # Collect all evidence steps
        all_steps = []
        for ann in annotations:
            all_steps.extend(ann.evidence_steps)

        # Deduplicate and sort
        merged_steps = sorted(set(all_steps))

        # Merge evidence texts (take the longest/more detailed one)
        texts = [a.evidence_text for a in annotations if a.evidence_text]
        merged_text = max(texts, key=len) if texts else ""

        return merged_steps, merged_text

    def generate_consensus(self, annotations: list[AnnotationRecord]) -> Optional[dict]:
        """Generate consensus label from multiple annotations"""
        if len(annotations) < self.min_annotators:
            return None

        traj_id = annotations[0].trajectory_id

        # Calculate consensus for each dimension
        failure_type, type_agreement = self.calculate_failure_type_consensus(annotations)
        first_step, step_agreement = self.calculate_step_consensus(annotations)
        detection, det_agreement = self.calculate_detection_consensus(annotations)
        confidence = self.calculate_average_confidence(annotations)

        # Check for severe disagreement
        severe = self.is_severe_disagreement(annotations)

        # Merge evidence
        evidence_steps, evidence_text = self.merge_evidence(annotations)

        # Determine consensus status
        if severe:
            consensus_status = "DISAGREEMENT"
        elif type_agreement >= 0.9:
            consensus_status = "UNANIMOUS"
        elif type_agreement >= self.agreement_threshold:
            consensus_status = "MAJORITY"
        else:
            consensus_status = "WEAK"

        return {
            "trajectory_id": traj_id,
            "trajectory_hash": annotations[0].trajectory_hash,
            "consensus_status": consensus_status,
            "n_annotators": len(annotations),
            "annotator_ids": [a.annotator_id for a in annotations],

            # Failure type consensus
            "failure_type": failure_type,
            "failure_type_agreement": round(type_agreement, 3),

            # First step consensus
            "first_consequential_failure_step": first_step,
            "step_agreement": round(step_agreement, 3),

            # Detection consensus
            "agent_detected_failure": detection,
            "detection_agreement": round(det_agreement, 3),

            # Confidence
            "average_confidence": round(confidence, 3),

            # Evidence
            "evidence_steps": evidence_steps,
            "evidence_text": evidence_text,

            # Raw annotations
            "raw_annotations": [a.to_dict() for a in annotations]
        }

    def generate_all_consensus(self) -> tuple[list[dict], list[dict]]:
        """
        Generate consensus for all trajectories.

        Returns:
            (consensus_labels, disagreement_queue)
        """
        annotations_by_traj = self.load_annotations()

        consensus_labels = []
        disagreement_queue = []

        for traj_id, annotations in annotations_by_traj.items():
            consensus = self.generate_consensus(annotations)

            if consensus is None:
                continue

            if consensus["consensus_status"] == "DISAGREEMENT":
                disagreement_queue.append(consensus)
            else:
                consensus_labels.append(consensus)

        return consensus_labels, disagreement_queue


def main():
    parser = argparse.ArgumentParser(description="Generate consensus labels")
    parser.add_argument("--min_annotators", type=int, default=2,
                       help="Minimum annotators required")
    parser.add_argument("--agreement_threshold", type=float, default=0.66,
                       help="Agreement threshold for majority")
    parser.add_argument("--output_dir", type=str, default="data/annotations/processed",
                       help="Output directory")
    args = parser.parse_args()

    print("=" * 70)
    print("Consensus Label Generation")
    print("=" * 70)

    generator = ConsensusGenerator(
        min_annotators=args.min_annotators,
        agreement_threshold=args.agreement_threshold
    )

    print(f"\nLoading annotations...")
    consensus_labels, disagreements = generator.generate_all_consensus()

    print(f"\nResults:")
    print(f"  Consensus labels: {len(consensus_labels)}")
    print(f"  Disagreement queue: {len(disagreements)}")

    # Breakdown by status
    status_counts = Counter(c["consensus_status"] for c in consensus_labels)
    print(f"\n  Consensus status breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"    {status}: {count}")

    # Save outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save consensus labels
    consensus_file = output_dir / "consensus_labels.jsonl"
    with open(consensus_file, 'w', encoding='utf-8') as f:
        for label in consensus_labels:
            f.write(json.dumps(label, ensure_ascii=False) + '\n')
    print(f"\nSaved consensus labels to: {consensus_file}")

    # Save disagreements
    if disagreements:
        review_dir = Path("data/annotations/review")
        review_dir.mkdir(parents=True, exist_ok=True)
        disagreement_file = review_dir / "disagreement_queue.jsonl"
        with open(disagreement_file, 'w', encoding='utf-8') as f:
            for d in disagreements:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')
        print(f"Saved disagreement queue to: {disagreement_file}")

    # Failure type distribution from consensus
    if consensus_labels:
        print("\n" + "=" * 70)
        print("Consensus Failure Type Distribution")
        print("=" * 70)
        ft_counts = Counter(c["failure_type"] for c in consensus_labels)
        for ft, count in ft_counts.most_common():
            pct = count / len(consensus_labels) * 100
            print(f"  {ft}: {count} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
