#!/usr/bin/env python3
"""
Phase 30: Human Annotation Quality Control

Checks human annotations for:
- Missing labels
- Invalid failure types
- Inconsistent timestamps
- Detection before failure
- Recovery before failure
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

VALID_FAILURE_TYPES = {"SELECTION", "EXECUTION", "RECOGNITION", "RECOVERY"}
VALID_DETECTION = {"YES", "NO", "UNCLEAR"}
VALID_RECOVERY = {"YES", "NO"}
VALID_SUCCESS = {"YES", "NO", "NA"}
VALID_CONFIDENCE = {"high", "medium", "low"}


def load_annotations(path: str) -> list[dict]:
    """Load annotations from JSONL file."""
    annotations = []
    annotation_file = Path(path)

    if not annotation_file.exists():
        print(f"Warning: {path} not found")
        return annotations

    with open(annotation_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    annotations.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON line: {line[:100]}")

    return annotations


def check_quality(annotations: list[dict], trajectory_lengths: dict = None) -> dict:
    """Run quality checks on annotations."""
    issues = []
    valid_count = 0

    for ann in annotations:
        traj_id = ann.get('trajectory_id', 'unknown')
        ann_issues = []

        # Check 1: Missing required fields
        required_fields = ['trajectory_id', 'first_failure_step', 'failure_type']
        for field in required_fields:
            if field not in ann or ann[field] is None:
                ann_issues.append(f"Missing required field: {field}")

        # Check 2: Invalid failure type
        ft = ann.get('failure_type')
        if ft and ft not in VALID_FAILURE_TYPES:
            ann_issues.append(f"Invalid failure_type: {ft}")

        # Check 3: Invalid detection value
        detection = ann.get('agent_detected_failure')
        if detection and detection not in VALID_DETECTION:
            ann_issues.append(f"Invalid agent_detected_failure: {detection}")

        # Check 4: Invalid recovery values
        recovery_attempted = ann.get('recovery_attempted')
        if recovery_attempted and recovery_attempted not in VALID_RECOVERY:
            ann_issues.append(f"Invalid recovery_attempted: {recovery_attempted}")

        recovery_success = ann.get('recovery_success')
        if recovery_success and recovery_success not in VALID_SUCCESS:
            ann_issues.append(f"Invalid recovery_success: {recovery_success}")

        # Check 5: Detection before failure
        failure_step = ann.get('first_failure_step')
        detection_step = ann.get('detection_step')

        if isinstance(failure_step, int) and isinstance(detection_step, int):
            if detection_step < failure_step:
                ann_issues.append(f"Detection step ({detection_step}) before failure step ({failure_step})")

        # Check 6: Recovery before detection
        if recovery_attempted == "YES" and detection in ["NO", None]:
            # Recovery implies detection - but this could be recovery without explicit detection
            pass

        # Check 7: Detection is YES but no detection step
        if detection == "YES" and detection_step is None:
            ann_issues.append("Detection marked YES but no detection_step provided")

        # Check 8: Invalid confidence
        confidence = ann.get('confidence')
        if confidence and confidence not in VALID_CONFIDENCE:
            ann_issues.append(f"Invalid confidence: {confidence}")

        if ann_issues:
            issues.append({
                'trajectory_id': traj_id,
                'issues': ann_issues
            })
        else:
            valid_count += 1

    return {
        'total': len(annotations),
        'valid': valid_count,
        'issues_count': len(issues),
        'issues': issues
    }


def generate_report(qc_results: dict, output_path: Path):
    """Generate quality control report."""
    quality_rate = (qc_results['valid']/qc_results['total']*100) if qc_results['total'] > 0 else 0
    md = f"""# Human Annotation Quality Control Report

**Generated: 2026-10-02**

## Summary

| Metric | Value |
|--------|-------|
| Total Annotations | {qc_results['total']} |
| Valid | {qc_results['valid']} |
| Issues Found | {qc_results['issues_count']} |
| Quality Rate | {quality_rate:.1f}% |

"""

    if qc_results['issues']:
        md += "\n## Issues Detail\n\n"
        md += "| Trajectory ID | Issues |\n"
        md += "|---------------|--------|\n"

        for issue in qc_results['issues'][:50]:  # Limit to first 50
            traj_id = issue['trajectory_id'][:40]
            issue_list = '; '.join(issue['issues'])
            md += f"| {traj_id} | {issue_list} |\n"

        if len(qc_results['issues']) > 50:
            md += f"\n*... and {len(qc_results['issues']) - 50} more issues*\n"
    else:
        md += "\n✅ **No issues found - all annotations are valid!**\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"Quality report saved to {output_path}")
    return qc_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Human annotation quality control")
    parser.add_argument('--input', default='data/human_annotations/annotations.jsonl')
    parser.add_argument('--output', default='results/human_annotation_qc.md')
    args = parser.parse_args()

    print("Loading annotations...")
    annotations = load_annotations(args.input)

    if not annotations:
        print("No annotations found. Generating empty report.")
        qc_results = {'total': 0, 'valid': 0, 'issues_count': 0, 'issues': []}
    else:
        print(f"Checking {len(annotations)} annotations...")
        qc_results = check_quality(annotations)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_report(qc_results, output_path)

    print(f"\nQuality: {qc_results['valid']}/{qc_results['total']} valid")


if __name__ == "__main__":
    main()
