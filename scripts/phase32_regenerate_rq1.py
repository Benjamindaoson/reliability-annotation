#!/usr/bin/env python3
"""
Phase 32: Regenerate RQ1 Results with Human Labels

This script:
1. Loads human annotations from data/human_annotations/
2. Generates failure distribution statistics
3. Creates breakdown by model, task, trajectory length
4. Outputs results to results/RQ1_human/

IMPORTANT:
- Only uses human-annotated data
- No synthetic annotations
- Reports confidence when sample size is small
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_annotations(path: str) -> list[dict]:
    """Load annotations from JSONL."""
    annotations = []
    annotation_file = Path(path)

    if not annotation_file.exists():
        return annotations

    with open(annotation_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                annotations.append(json.loads(line))

    return annotations


def load_trajectories(path: str) -> dict:
    """Load trajectories into lookup."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    trajectories = data if isinstance(data, list) else [data]
    return {t.get('trajectory_id'): t for t in trajectories}


def analyze_rq1(annotations: list[dict], trajectories: dict) -> dict:
    """Analyze RQ1 with human annotations."""

    if not annotations:
        return {
            'status': 'NO_ANNOTATIONS',
            'message': 'No human annotations found. Run annotation campaign first.',
            'n_annotations': 0
        }

    # Filter valid annotations (not NONE)
    valid_annotations = [
        a for a in annotations
        if a.get('first_failure_step') != "NONE"
        and a.get('failure_type') in {"SELECTION", "EXECUTION", "RECOGNITION", "RECOVERY"}
    ]

    n_total = len(annotations)
    n_valid = len(valid_annotations)

    # Distribution by failure type
    type_counts = defaultdict(int)
    for ann in valid_annotations:
        type_counts[ann['failure_type']] += 1

    # Distribution by model
    by_model = defaultdict(lambda: defaultdict(int))
    for ann in valid_annotations:
        model = ann.get('model_id', 'unknown')
        by_model[model][ann['failure_type']] += 1

    # Distribution by trajectory length
    by_length = defaultdict(lambda: defaultdict(int))
    for ann in valid_annotations:
        traj_id = ann.get('trajectory_id')
        if traj_id in trajectories:
            length = len(trajectories[traj_id].get('steps', []))
            length_bin = (length // 5) * 5
            by_length[length_bin][ann['failure_type']] += 1

    # Detection statistics
    detected = sum(1 for a in valid_annotations if a.get('agent_detected_failure') == 'YES')
    total_awareness = sum(1 for a in valid_annotations if a.get('agent_detected_failure') in {'YES', 'NO', 'UNCLEAR'})

    D0 = detected / n_valid if n_valid > 0 else 0
    UFR = 1 - D0

    # Recovery statistics
    recovery_attempted = sum(1 for a in valid_annotations if a.get('recovery_attempted') == 'YES')
    recovery_success = sum(1 for a in valid_annotations if a.get('recovery_success') == 'YES')
    RS = recovery_success / recovery_attempted if recovery_attempted > 0 else 0

    # NONE failures
    none_count = sum(1 for a in annotations if a.get('first_failure_step') == "NONE")

    results = {
        'status': 'SUCCESS',
        'n_total_annotations': n_total,
        'n_valid_failures': n_valid,
        'n_no_failure': none_count,
        'distribution': dict(type_counts),
        'by_model': {k: dict(v) for k, v in by_model.items()},
        'by_length': {str(k): dict(v) for k, v in by_length.items()},
        'detection': {
            'D0_detection_rate': D0,
            'UFR_undetected_rate': UFR,
            'n_detected': detected,
            'n_total': n_valid,
        },
        'recovery': {
            'RS_recovery_success': RS,
            'n_recovery_attempted': recovery_attempted,
            'n_recovery_success': recovery_success,
        }
    }

    return results


def generate_report(results: dict, output_dir: Path):
    """Generate RQ1 report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if results['status'] == 'NO_ANNOTATIONS':
        md = """# RQ1 Results: Where Do Agents Fail?

## Status: NO HUMAN ANNOTATIONS AVAILABLE

**This report requires human annotations.**

Run the annotation campaign:
```bash
streamlit run annotation_tool/app.py
```

Then analyze with:
```bash
python scripts/phase32_regenerate_rq1.py
```

### What We Need

- Minimum 50 annotated trajectories
- Human labels for failure type
- Agent detection evidence

### Pipeline Status

- ✅ Infrastructure complete
- ⏳ Awaiting human annotations
"""
        with open(output_dir / 'RQ1_human_report.md', 'w', encoding='utf-8') as f:
            f.write(md)
        return

    # Valid results
    n_valid = results['n_valid_failures']
    type_dist = results['distribution']

    # Table 1: Failure Distribution
    table1 = "| Failure Type | Count | Percentage |\n"
    table1 += "|--------------|-------|------------|\n"

    for ft in ['SELECTION', 'EXECUTION', 'RECOGNITION', 'RECOVERY']:
        count = type_dist.get(ft, 0)
        pct = (count / n_valid * 100) if n_valid > 0 else 0
        table1 += f"| {ft} | {count} | {pct:.1f}% |\n"

    md = f"""# RQ1 Results: Where Do Agents Fail?

## Status: HUMAN-GROUNDED RESULTS

**All statistics below are from human annotations.**

---

## Research Question

*Where do long-horizon agents fail in the task pipeline?*

---

## Dataset

- Total annotations: {results['n_total_annotations']}
- Valid failures: {n_valid}
- No failure found: {results['n_no_failure']}

---

## Table 1: Failure Type Distribution

{table1}

---

## Detection Statistics

| Metric | Value |
|--------|-------|
| Detected Failures | {results['detection']['n_detected']} |
| Total Failures | {results['detection']['n_total']} |
| **Detection Rate (D0)** | **{results['detection']['D0_detection_rate']:.1%}** |
| **Undetected Failure Rate (UFR)** | **{results['detection']['UFR_undetected_rate']:.1%}** |

---

## Recovery Statistics

| Metric | Value |
|--------|-------|
| Recovery Attempted | {results['recovery']['n_recovery_attempted']} |
| Recovery Successful | {results['recovery']['n_recovery_success']} |
| Recovery Success Rate (RS) | {results['recovery']['RS_recovery_success']:.1%} |

"""

    # By model
    if results['by_model']:
        md += "\n## Breakdown by Model\n\n"
        md += "| Model | SELECTION | EXECUTION | RECOGNITION | RECOVERY | Total |\n"
        md += "|-------|-----------|-----------|-------------|----------|-------|\n"

        for model, dist in results['by_model'].items():
            total = sum(dist.values())
            s = dist.get('SELECTION', 0)
            e = dist.get('EXECUTION', 0)
            r = dist.get('RECOGNITION', 0)
            rc = dist.get('RECOVERY', 0)
            md += f"| {model[:30]} | {s} | {e} | {r} | {rc} | {total} |\n"

    # By length
    if results['by_length']:
        md += "\n## Breakdown by Trajectory Length\n\n"
        md += "| Length Bin | SELECTION | EXECUTION | RECOGNITION | RECOVERY |\n"
        md += "|------------|----------|-----------|-------------|----------|\n"

        for length_bin in sorted(results['by_length'].keys(), key=int):
            dist = results['by_length'][length_bin]
            s = dist.get('SELECTION', 0)
            e = dist.get('EXECUTION', 0)
            r = dist.get('RECOGNITION', 0)
            rc = dist.get('RECOVERY', 0)
            md += f"| {length_bin}-{int(length_bin)+4} | {s} | {e} | {r} | {rc} |\n"

    # Caveats
    md += f"""

---

## Caveats

1. Sample size: {n_valid} failures
2. Single model: Claude-4-Sonnet
3. Confidence intervals: not yet computed

"""

    with open(output_dir / 'RQ1_human_report.md', 'w', encoding='utf-8') as f:
        f.write(md)

    # Save JSON
    with open(output_dir / 'rq1_human_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"RQ1 report saved to {output_dir}")
    print(f"Valid failures: {n_valid}")
    print(f"Detection rate (D0): {results['detection']['D0_detection_rate']:.1%}")
    print(f"Undetected failure rate (UFR): {results['detection']['UFR_undetected_rate']:.1%}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Regenerate RQ1 with human labels")
    parser.add_argument('--annotations', default='data/human_annotations/annotations.jsonl')
    parser.add_argument('--trajectories', default='data/raw/osworld_claude4_converted.json')
    parser.add_argument('--output', default='results/RQ1_human')
    args = parser.parse_args()

    print("Loading annotations...")
    annotations = load_annotations(args.annotations)

    print("Loading trajectories...")
    trajectories = load_trajectories(args.trajectories)

    print("Analyzing RQ1...")
    results = analyze_rq1(annotations, trajectories)

    output_dir = Path(args.output)
    generate_report(results, output_dir)


if __name__ == "__main__":
    main()
