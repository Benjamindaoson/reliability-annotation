#!/usr/bin/env python3
"""
Phase 33: Generate Reliability Profile from Human Annotations

Computes reliability metrics:
- A: Action correctness
- UFR: Undetected Failure Rate
- DD: Detection Delay
- RS: Recovery Success Rate
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_annotations(path: str) -> list[dict]:
    """Load annotations."""
    annotations = []
    if Path(path).exists():
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    annotations.append(json.loads(line))
    return annotations


def load_trajectories(path: str) -> dict:
    """Load trajectories."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    trajectories = data if isinstance(data, list) else [data]
    return {t.get('trajectory_id'): t for t in trajectories}


def compute_reliability_metrics(annotations: list[dict], trajectories: dict) -> dict:
    """Compute reliability metrics for each model."""

    if not annotations:
        return {
            'status': 'NO_ANNOTATIONS',
            'message': 'No human annotations found.'
        }

    # Group by model
    by_model = defaultdict(list)
    for ann in annotations:
        model = ann.get('model_id', 'unknown')
        by_model[model].append(ann)

    results = {}

    for model, model_annotations in by_model.items():
        valid = [
            a for a in model_annotations
            if a.get('first_failure_step') != "NONE"
        ]

        n = len(valid)
        if n == 0:
            continue

        # D0: Detection rate
        detected = sum(1 for a in valid if a.get('agent_detected_failure') == 'YES')
        D0 = detected / n

        # UFR: Undetected failure rate
        UFR = 1 - D0

        # DD: Detection delay
        delays = []
        for a in valid:
            failure_step = a.get('first_failure_step')
            detection_step = a.get('detection_step')
            if isinstance(failure_step, int) and isinstance(detection_step, int):
                if detection_step >= failure_step:
                    delays.append(detection_step - failure_step)

        DD = sum(delays) / len(delays) if delays else None

        # RS: Recovery success rate
        recovery_attempted = sum(1 for a in valid if a.get('recovery_attempted') == 'YES')
        recovery_success = sum(1 for a in valid if a.get('recovery_success') == 'YES')
        RS = recovery_success / recovery_attempted if recovery_attempted > 0 else None

        # A: Action correctness (1 - failure rate)
        # This is approximate - true A would need trajectory success labels
        A = 1.0 - (n / 200)  # Assuming ~200 trajectories total

        results[model] = {
            'A_action_correctness': A,
            'UFR_undetected_failure_rate': UFR,
            'D0_detection_rate': D0,
            'DD_detection_delay': DD,
            'RS_recovery_success': RS,
            'n_failures': n,
            'n_detected': detected,
            'n_recovery_attempted': recovery_attempted,
            'n_recovery_success': recovery_success,
        }

    return {
        'status': 'SUCCESS',
        'models': results
    }


def generate_profile_report(results: dict, output_dir: Path):
    """Generate reliability profile report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if results['status'] == 'NO_ANNOTATIONS':
        md = """# Reliability Profile Report

## Status: NO HUMAN ANNOTATIONS

Await human annotation campaign before computing reliability profiles.
"""
        with open(output_dir / 'reliability_profile.md', 'w', encoding='utf-8') as f:
            f.write(md)
        return

    md = """# Reliability Profile Report

**Generated from human annotations**

---

## Reliability Metrics

| Model | A (Accuracy) | UFR | D0 (Detection) | DD (Delay) | RS (Recovery) |
|-------|--------------|-----|----------------|------------|---------------|
"""

    for model, metrics in results['models'].items():
        A = metrics.get('A_action_correctness', 'N/A')
        UFR = metrics.get('UFR_undetected_failure_rate', 'N/A')
        D0 = metrics.get('D0_detection_rate', 'N/A')
        DD = metrics.get('DD_detection_delay', 'N/A')
        RS = metrics.get('RS_recovery_success', 'N/A')

        A_str = f"{A:.1%}" if isinstance(A, float) else str(A)
        UFR_str = f"{UFR:.1%}" if isinstance(UFR, float) else str(UFR)
        D0_str = f"{D0:.1%}" if isinstance(D0, float) else str(D0)
        DD_str = f"{DD:.1f}" if isinstance(DD, float) else str(DD)
        RS_str = f"{RS:.1%}" if isinstance(RS, float) else str(RS)

        md += f"| {model[:20]} | {A_str} | {UFR_str} | {D0_str} | {DD_str} | {RS_str} |\n"

    # Detailed breakdown
    md += "\n## Detailed Metrics\n\n"

    for model, metrics in results['models'].items():
        md += f"### {model}\n\n"
        md += f"| Metric | Value |\n"
        md += f"|--------|-------|\n"
        md += f"| Action Correctness (A) | {metrics.get('A_action_correctness', 'N/A'):.1%} |\n"
        md += f"| Undetected Failure Rate (UFR) | {metrics.get('UFR_undetected_failure_rate', 'N/A'):.1%} |\n"
        md += f"| Detection Rate (D0) | {metrics.get('D0_detection_rate', 'N/A'):.1%} |\n"
        md += f"| Mean Detection Delay (DD) | {metrics.get('DD_detection_delay', 'N/A')} steps |\n"
        md += f"| Recovery Success Rate (RS) | {metrics.get('RS_recovery_success', 'N/A'):.1%} |\n"
        md += f"| Total Failures | {metrics.get('n_failures', 'N/A')} |\n"
        md += "\n"

    # Visual profile
    md += "\n## Visual Profile\n\n"
    for model, metrics in results['models'].items():
        UFR = metrics.get('UFR_undetected_failure_rate', 0)
        D0 = metrics.get('D0_detection_rate', 0)
        DD = metrics.get('DD_detection_delay', 0)
        RS = metrics.get('RS_recovery_success', 0)

        md += f"### {model}\n\n"
        md += "```\n"
        md += f"UFR (Undetected):  {'█' * int(UFR*20)}{'░' * (20-int(UFR*20))} {UFR:.1%}\n"
        md += f"D0 (Detection):    {'█' * int(D0*20)}{'░' * (20-int(D0*20))} {D0:.1%}\n"
        md += f"DD (Delay):        {DD:.1f} steps\n"
        md += f"RS (Recovery):     {'█' * int(RS*20)}{'░' * (20-int(RS*20))} {RS:.1%}\n"
        md += "```\n\n"

    with open(output_dir / 'reliability_profile.md', 'w', encoding='utf-8') as f:
        f.write(md)

    with open(output_dir / 'reliability_profile.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Reliability profile saved to {output_dir}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotations', default='data/human_annotations/annotations.jsonl')
    parser.add_argument('--trajectories', default='data/raw/osworld_claude4_converted.json')
    parser.add_argument('--output', default='results/reliability_human')
    args = parser.parse_args()

    annotations = load_annotations(args.annotations)
    trajectories = load_trajectories(args.trajectories)

    results = compute_reliability_metrics(annotations, trajectories)
    generate_profile_report(results, Path(args.output))


if __name__ == "__main__":
    main()
