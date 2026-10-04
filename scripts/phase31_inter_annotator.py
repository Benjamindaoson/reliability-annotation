#!/usr/bin/env python3
"""
Phase 31: Inter-Annotator Agreement Analysis

Calculates agreement metrics between annotators:
- Cohen's Kappa for failure type
- Binary Kappa for detection
- Mean absolute difference for step localization

Usage:
    python scripts/phase31_inter_annotator.py --input1 <file1> --input2 <file2>
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import math

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_annotations(path: str) -> dict:
    """Load annotations into lookup by trajectory_id."""
    annotations = {}
    annotation_file = Path(path)

    if not annotation_file.exists():
        return annotations

    with open(annotation_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                ann = json.loads(line)
                traj_id = ann.get('trajectory_id')
                if traj_id:
                    annotations[traj_id] = ann

    return annotations


def cohen_kappa(annotations1: dict, annotations2: dict, key: str) -> float:
    """Calculate Cohen's Kappa for a categorical variable."""
    # Find common trajectory IDs
    common_ids = set(annotations1.keys()) & set(annotations2.keys())

    if not common_ids:
        return None

    # Build confusion matrix
    categories = set()
    for traj_id in common_ids:
        val1 = annotations1[traj_id].get(key)
        val2 = annotations2[traj_id].get(key)
        if val1:
            categories.add(val1)
        if val2:
            categories.add(val2)

    categories = sorted(categories)
    n_cats = len(categories)
    cat_to_idx = {c: i for i, c in enumerate(categories)}

    # Confusion matrix
    conf_matrix = [[0] * n_cats for _ in range(n_cats)]

    for traj_id in common_ids:
        val1 = annotations1[traj_id].get(key)
        val2 = annotations2[traj_id].get(key)
        if val1 and val2:
            conf_matrix[cat_to_idx[val1]][cat_to_idx[val2]] += 1

    # Calculate kappa
    n = sum(sum(row) for row in conf_matrix)
    if n == 0:
        return None

    # Observed agreement
    po = sum(conf_matrix[i][i] for i in range(n_cats)) / n

    # Expected agreement
    pe = 0
    for i in range(n_cats):
        row_sum = sum(conf_matrix[i])
        col_sum = sum(conf_matrix[j][i] for j in range(n_cats))
        pe += (row_sum * col_sum)

    if pe == 0:
        return None

    pe /= (n * n)

    # Kappa
    if po == 1.0:
        return 1.0

    kappa = (po - pe) / (1 - pe) if (1 - pe) != 0 else 1.0

    return kappa


def binary_kappa(annotations1: dict, annotations2: dict, key: str, positive: str = "YES") -> float:
    """Calculate Cohen's Kappa for binary variable."""
    common_ids = set(annotations1.keys()) & set(annotations2.keys())

    if not common_ids:
        return None

    # Build 2x2 confusion matrix
    # [a, b] = annotator1 [positive, negative]
    # [c, d] = annotator2 [positive, negative]
    a = b = c = d = 0

    for traj_id in common_ids:
        val1 = annotations1[traj_id].get(key)
        val2 = annotations2[traj_id].get(key)

        if val1 is None or val2 is None:
            continue

        val1_pos = (val1 == positive)
        val2_pos = (val2 == positive)

        if val1_pos and val2_pos:
            a += 1
        elif val1_pos and not val2_pos:
            b += 1
        elif not val1_pos and val2_pos:
            c += 1
        else:
            d += 1

    n = a + b + c + d
    if n == 0:
        return None

    # Observed agreement
    po = (a + d) / n

    # Expected agreement
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / (n * n)

    if pe == 1.0:
        return 1.0

    kappa = (po - pe) / (1 - pe) if (1 - pe) != 0 else 1.0

    return kappa


def step_mae(annotations1: dict, annotations2: dict) -> float:
    """Calculate mean absolute error for step localization."""
    common_ids = set(annotations1.keys()) & set(annotations2.keys())

    if not common_ids:
        return None

    diffs = []
    for traj_id in common_ids:
        step1 = annotations1[traj_id].get('first_failure_step')
        step2 = annotations2[traj_id].get('first_failure_step')

        if isinstance(step1, int) and isinstance(step2, int):
            diffs.append(abs(step1 - step2))

    if not diffs:
        return None

    return sum(diffs) / len(diffs)


def calculate_agreement(input1: str, input2: str, output_dir: Path):
    """Calculate all agreement metrics."""

    ann1 = load_annotations(input1)
    ann2 = load_annotations(input2)

    common_ids = set(ann1.keys()) & set(ann2.keys())

    results = {
        'input1': input1,
        'input2': input2,
        'n_annotator1': len(ann1),
        'n_annotator2': len(ann2),
        'n_common': len(common_ids),
    }

    # Cohen's Kappa for failure type
    kappa_ft = cohen_kappa(ann1, ann2, 'failure_type')
    results['failure_type_kappa'] = kappa_ft

    # Cohen's Kappa for detection
    kappa_det = binary_kappa(ann1, ann2, 'agent_detected_failure', 'YES')
    results['detection_kappa'] = kappa_det

    # Step localization MAE
    mae_step = step_mae(ann1, ann2)
    results['step_localization_mae'] = mae_step

    # Agreement rates
    if common_ids:
        ft_agree = sum(
            1 for tid in common_ids
            if ann1[tid].get('failure_type') == ann2[tid].get('failure_type')
        ) / len(common_ids)
        results['failure_type_agreement_rate'] = ft_agree

        det_agree = sum(
            1 for tid in common_ids
            if ann1[tid].get('agent_detected_failure') == ann2[tid].get('agent_detected_failure')
        ) / len(common_ids)
        results['detection_agreement_rate'] = det_agree

    # Save JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / 'annotation_agreement.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Generate markdown report
    md = f"""# Inter-Annotator Agreement Report

**Generated: 2026-10-02**

## Overview

| Metric | Value |
|--------|-------|
| Annotator 1 samples | {results['n_annotator1']} |
| Annotator 2 samples | {results['n_annotator2']} |
| Common samples | {results['n_common']} |

## Agreement Metrics

### Failure Type Agreement

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Cohen's Kappa | {kappa_ft:.3f if kappa_ft else 'N/A'} | {interpret_kappa(kappa_ft)} |
| Agreement Rate | {results.get('failure_type_agreement_rate', 'N/A'):.1%} | - |

### Detection Agreement (Binary)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Cohen's Kappa | {kappa_det:.3f if kappa_det else 'N/A'} | {interpret_kappa(kappa_det)} |
| Agreement Rate | {results.get('detection_agreement_rate', 'N/A'):.1%} | - |

### Step Localization

| Metric | Value |
|--------|-------|
| Mean Absolute Error | {mae_step:.2f if mae_step else 'N/A'} steps |

## Kappa Interpretation Guide

| Kappa | Interpretation |
|-------|----------------|
| < 0.00 | Poor |
| 0.00 - 0.20 | Slight |
| 0.21 - 0.40 | Fair |
| 0.41 - 0.60 | Moderate |
| 0.61 - 0.80 | Substantial |
| 0.81 - 1.00 | Almost Perfect |

## Recommendations

"""

    if kappa_ft and kappa_ft < 0.4:
        md += "- ⚠️ **Low failure type agreement** - Consider additional annotator training\n"
    else:
        md += "- ✅ Failure type agreement is acceptable\n"

    if kappa_det and kappa_det < 0.4:
        md += "- ⚠️ **Low detection agreement** - Detection criteria may need clarification\n"
    else:
        md += "- ✅ Detection agreement is acceptable\n"

    if mae_step and mae_step > 2:
        md += "- ⚠️ **High step localization error** - Consider defining failure more precisely\n"
    else:
        md += "- ✅ Step localization is acceptable\n"

    with open(output_dir / 'annotation_agreement.md', 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"Agreement report saved to {output_dir}")
    return results


def interpret_kappa(kappa: float) -> str:
    """Interpret Cohen's Kappa value."""
    if kappa is None:
        return "N/A"
    if kappa < 0:
        return "Poor"
    if kappa < 0.20:
        return "Slight"
    if kappa < 0.40:
        return "Fair"
    if kappa < 0.60:
        return "Moderate"
    if kappa < 0.80:
        return "Substantial"
    return "Almost Perfect"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Inter-annotator agreement analysis")
    parser.add_argument('--input1', required=True, help="First annotation file")
    parser.add_argument('--input2', required=True, help="Second annotation file")
    parser.add_argument('--output', default='results', help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    calculate_agreement(args.input1, args.input2, output_dir)


if __name__ == "__main__":
    main()
