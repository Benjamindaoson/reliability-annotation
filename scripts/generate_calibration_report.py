"""
Calibration Report Generator

Generates a detailed calibration report for Batch 001 annotation.

Usage:
    python scripts/generate_calibration_report.py
    python scripts/generate_calibration_report.py --batch_id 001
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation.schema import AnnotationRecord, FailureType
from scripts.analyze_agreement import fleiss_kappa, cohen_kappa


class CalibrationReportGenerator:
    """Generate detailed calibration report for Batch 001"""

    def __init__(self):
        self.annotations_by_trajectory = defaultdict(list)
        self.sources = ["claude", "gpt", "gemini"]

    def load_annotations(self) -> dict:
        """Load all annotations grouped by trajectory"""
        for source in self.sources:
            source_dir = Path(f"data/annotations/raw/{source}")
            if not source_dir.exists():
                continue

            for file in source_dir.glob("*.jsonl"):
                with open(file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            ann = AnnotationRecord.from_dict(json.loads(line))
                            self.annotations_by_trajectory[ann.trajectory_id].append({
                                "source": source,
                                "annotator_id": ann.annotator_id,
                                "model": ann.annotator_model,
                                "record": ann
                            })

        return self.annotations_by_trajectory

    def get_causal_text(self, record: AnnotationRecord) -> str:
        """Extract causal analysis text from evidence"""
        return record.evidence_text[:200] if record.evidence_text else ""

    def classify_disagreement(self, annotations: list) -> dict:
        """
        Classify disagreement into 3 classes.

        Class 1: Same causal interpretation, different label
        Class 2: Same failure type, different onset step
        Class 3: Different causal chains
        """
        if len(annotations) < 2:
            return {"class": None, "reason": "insufficient_annotators"}

        records = [a["record"] for a in annotations]
        labels = [r.failure_type.value for r in records]
        steps = [r.first_consequential_failure_step for r in records if r.first_consequential_failure_step is not None]

        unique_labels = set(labels)
        step_range = max(steps) - min(steps) if steps else 0

        # Class 3: Different labels with very different onset steps
        if len(unique_labels) >= 2 and step_range >= 3:
            return {
                "class": 3,
                "reason": "different_causal_chains",
                "details": f"Labels: {labels}, Steps: {steps}, Range: {step_range}"
            }

        # Class 2: Same label, different onset step
        if len(unique_labels) == 1 and step_range >= 2:
            return {
                "class": 2,
                "reason": "same_type_different_onset",
                "details": f"Label: {labels[0]}, Steps: {steps}, Range: {step_range}"
            }

        # Class 1: Different labels but similar onset steps
        if len(unique_labels) >= 2 and step_range <= 2:
            return {
                "class": 1,
                "reason": "same_onset_different_label",
                "details": f"Labels: {labels}, Steps: {steps}"
            }

        # Agreement
        return {
            "class": 0,
            "reason": "agreement",
            "details": f"Labels: {labels}, Steps: {steps}"
        }

    def generate_table_row(self, traj_id: str, annotations: list) -> dict:
        """Generate a row for the calibration table"""
        if not annotations:
            return {
                "trajectory_id": traj_id,
                "gpt_label": "-",
                "claude_label": "-",
                "gemini_label": "-",
                "onset_steps": "-",
                "root_cause": "-",
                "agreement": "NO_ANNOTATIONS",
                "ambiguity_reason": "-"
            }

        # Sort by source
        labels = {}
        steps = {}
        causal_texts = {}
        for ann in annotations:
            source = ann["source"]
            record = ann["record"]
            labels[source] = record.failure_type.value
            steps[source] = record.first_consequential_failure_step
            causal_texts[source] = self.get_causal_text(record)

        # Compute agreement
        all_labels = list(labels.values())
        unique_labels = set(all_labels)
        label_agreement = 1.0 if len(unique_labels) == 1 else 0.0

        all_steps = [s for s in steps.values() if s is not None]
        step_maes = []
        step_within_1_list = []
        step_within_2_list = []
        if len(all_steps) >= 2:
            for i, s1 in enumerate(all_steps):
                for s2 in all_steps[i+1:]:
                    diff = abs(s1 - s2)
                    step_maes.append(diff)
                    step_within_1_list.append(1 if diff <= 1 else 0)
                    step_within_2_list.append(1 if diff <= 2 else 0)
        avg_step_diff = sum(step_maes) / len(step_maes) if step_maes else 0
        step_within_1 = sum(step_within_1_list) / len(step_within_1_list) if step_within_1_list else 1.0
        step_within_2 = sum(step_within_2_list) / len(step_within_2_list) if step_within_2_list else 1.0

        # Disagreement classification
        disagreement = self.classify_disagreement(annotations)

        return {
            "trajectory_id": traj_id,
            "gpt_label": labels.get("gpt", "-"),
            "claude_label": labels.get("claude", "-"),
            "gemini_label": labels.get("gemini", "-"),
            "onset_steps": str(all_steps) if all_steps else "-",
            "root_cause": causal_texts.get(list(labels.keys())[0], "-")[:100] if labels else "-",
            "agreement": "AGREE" if label_agreement == 1.0 else f"DISAGREE-{disagreement['class']}",
            "ambiguity_reason": disagreement.get("reason", "-"),
            "label_agreement": label_agreement,
            "step_maes": avg_step_diff,
            "step_within_1": step_within_1,
            "step_within_2": step_within_2,
            "disagreement_class": disagreement.get("class", None)
        }

    def calculate_metrics(self, rows: list) -> dict:
        """Calculate summary metrics from table rows"""
        valid_rows = [r for r in rows if r["agreement"] != "NO_ANNOTATIONS"]

        if not valid_rows:
            return {"error": "No valid annotations"}

        # Label agreement
        agree_count = sum(1 for r in valid_rows if r["agreement"] == "AGREE")
        label_agreement_rate = agree_count / len(valid_rows)

        # Step agreement within 1
        step_within_1_rate = sum(r.get("step_within_1", 0) for r in valid_rows) / len(valid_rows)

        # Step agreement within 2 (diagnostic)
        step_within_2_rate = sum(r.get("step_within_2", 0) for r in valid_rows) / len(valid_rows)

        # Step MAE
        avg_step_mae = sum(r.get("step_maes", 0) for r in valid_rows) / len(valid_rows)

        # Disagreement class distribution
        class_counts = Counter(r.get("disagreement_class") for r in valid_rows)

        # Failure type distribution
        ft_counts = Counter()
        for r in valid_rows:
            for key in ["gpt_label", "claude_label", "gemini_label"]:
                if r.get(key) and r[key] != "-":
                    ft_counts[r[key]] += 1

        # Gate check (primary criteria only)
        gate_passed = label_agreement_rate >= 0.8 and step_within_1_rate >= 0.8

        return {
            "n_trajectories": len(valid_rows),
            "n_fully_annotated": sum(1 for r in valid_rows if all(r.get(k) and r[k] != "-" for k in ["gpt_label", "claude_label", "gemini_label"])),
            "label_agreement_rate": round(label_agreement_rate, 3),
            "step_within_1_rate": round(step_within_1_rate, 3),
            "step_within_2_rate": round(step_within_2_rate, 3),  # Diagnostic
            "avg_step_mae": round(avg_step_mae, 2),
            "disagreement_class_distribution": dict(class_counts),
            "failure_type_distribution": dict(ft_counts),
            "gate_passed": gate_passed
        }

    def generate_report(self) -> dict:
        """Generate full calibration report"""
        self.load_annotations()

        if not self.annotations_by_trajectory:
            return {
                "error": "No annotations found. Run import first.",
                "next_steps": [
                    "python scripts/import_annotations.py --file claude_batch001.jsonl --source claude ...",
                    "python scripts/import_annotations.py --file gpt_batch001.jsonl --source gpt ...",
                    "python scripts/import_annotations.py --file gemini_batch001.jsonl --source gemini ..."
                ]
            }

        # Generate table
        table_rows = []
        for traj_id in sorted(self.annotations_by_trajectory.keys()):
            row = self.generate_table_row(traj_id, self.annotations_by_trajectory[traj_id])
            table_rows.append(row)

        # Calculate metrics
        metrics = self.calculate_metrics(table_rows)

        report = {
            "generated_at": datetime.now().isoformat(),
            "batch_id": "001",
            "metrics": metrics,
            "table": table_rows,
            "disagreement_analysis": self.analyze_disagreements(table_rows)
        }

        return report

    def analyze_disagreements(self, rows: list) -> dict:
        """Analyze disagreement patterns"""
        disagreements = [r for r in rows if r["agreement"] != "AGREE" and r["agreement"] != "NO_ANNOTATIONS"]

        analysis = {
            "total_disagreements": len(disagreements),
            "by_class": defaultdict(list)
        }

        for r in disagreements:
            cls = r.get("disagreement_class")
            if cls is not None:
                analysis["by_class"][str(cls)].append({
                    "trajectory_id": r["trajectory_id"],
                    "labels": [r.get(k) for k in ["gpt_label", "claude_label", "gemini_label"] if r.get(k) and r[k] != "-"],
                    "steps": r["onset_steps"],
                    "reason": r["ambiguity_reason"]
                })

        return dict(analysis)

    def save_report(self, report: dict, output_path: Path):
        """Save report to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def print_summary(self, report: dict):
        """Print human-readable summary"""
        if "error" in report:
            print(f"\nError: {report['error']}")
            if "next_steps" in report:
                print("\nNext steps:")
                for step in report["next_steps"]:
                    print(f"  {step}")
            return

        metrics = report["metrics"]
        print("\n" + "=" * 80)
        print("CALIBRATION REPORT - Batch 001")
        print("=" * 80)
        print(f"\nGenerated: {report['generated_at']}")
        print(f"Trajectories analyzed: {metrics['n_trajectories']}")
        print(f"Fully annotated (3/3): {metrics['n_fully_annotated']}")

        print("\n" + "-" * 40)
        print("GATE CRITERIA (Primary)")
        print("-" * 40)
        print(f"Label Agreement Rate:       {metrics['label_agreement_rate']:.1%} (target: >=80%)")
        print(f"Onset-Step Agreement (+-1):  {metrics['step_within_1_rate']:.1%} (target: >=80%)")

        print("\n" + "-" * 40)
        print("DIAGNOSTIC METRICS")
        print("-" * 40)
        print(f"Onset-Step Agreement (+-2):  {metrics.get('step_within_2_rate', 'N/A'):.1%}" if 'step_within_2_rate' in metrics else "Onset-Step Agreement (+-2): N/A")
        print(f"Avg Step MAE:               {metrics['avg_step_mae']:.2f} steps")

        print("\n" + "=" * 40)
        print(f"GATE: {'PASSED' if metrics['gate_passed'] else 'NOT PASSED'}")
        print("=" * 40)

        print("\n" + "-" * 40)
        print("DISAGREEMENT ANALYSIS")
        print("-" * 40)
        da = report["disagreement_analysis"]
        print(f"Total disagreements: {da['total_disagreements']}")
        for cls, cases in da["by_class"].items():
            print(f"  Class {cls}: {len(cases)} cases")

        print("\n" + "-" * 40)
        print("FAILURE TYPE DISTRIBUTION")
        print("-" * 40)
        for ft, count in sorted(metrics["failure_type_distribution"].items(), key=lambda x: -x[1]):
            pct = count / sum(metrics["failure_type_distribution"].values()) * 100
            print(f"  {ft}: {count} ({pct:.1f}%)")

        print("\n" + "-" * 40)
        print("CALIBRATION TABLE")
        print("-" * 40)
        print(f"{'Trajectory ID':<50} {'GPT':<12} {'Claude':<12} {'Gemini':<12} {'Agree':<10}")
        print("-" * 96)
        for row in report["table"]:
            traj_short = row["trajectory_id"][:48]
            print(f"{traj_short:<50} {row['gpt_label']:<12} {row['claude_label']:<12} {row['gemini_label']:<12} {row['agreement']:<10}")


def main():
    parser = argparse.ArgumentParser(description="Generate calibration report")
    parser.add_argument("--batch_id", type=str, default="001",
                        help="Batch ID to analyze")
    parser.add_argument("--output", type=str, default="results/calibration",
                        help="Output directory")
    args = parser.parse_args()

    generator = CalibrationReportGenerator()
    report = generator.generate_report()

    # Save JSON report
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"calibration_batch{args.batch_id}_report.json"
    generator.save_report(report, output_file)

    # Print summary
    generator.print_summary(report)

    print(f"\nFull report saved to: {output_file}")


if __name__ == "__main__":
    main()
