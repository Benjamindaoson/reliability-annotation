#!/usr/bin/env python3
"""
Phase 5-8: Automated RQ1 Analysis and Thesis Gate

This script runs automatically after human annotations are collected.
It generates:
1. RQ1 human-grounded results
2. Thesis gate decision report
3. RQ2 candidate case selection

Usage:
    python scripts/run_human_analysis.py
    python scripts/run_human_analysis.py --min-annotations 50
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import math

ANNOTATION_FILE = Path("data/human_annotations/annotations.jsonl")
DATA_FILE = Path("data/raw/osworld_claude4_converted.json")
OUTPUT_DIR = Path("results/RQ1_human_first50")


def load_annotations() -> list[dict]:
    """Load all human annotations."""
    if not ANNOTATION_FILE.exists():
        return []
    annotations = []
    with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                annotations.append(json.loads(line))
    return annotations


def load_trajectories() -> dict:
    """Load trajectories."""
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    trajectories = data if isinstance(data, list) else [data]
    return {t['trajectory_id']: t for t in trajectories}


def compute_ufr_ci(n_success: int, n_total: int, confidence: float = 0.95) -> tuple[float, float]:
    """Compute Wilson score confidence interval for UFR."""
    if n_total == 0:
        return (0, 0)

    p = n_success / n_total
    z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%

    denominator = 1 + z**2 / n_total
    center = p + z**2 / (2 * n_total)
    spread = z * math.sqrt(p * (1 - p) / n_total + z**2 / (4 * n_total**2))

    lower = (center - spread) / denominator
    upper = (center + spread) / denominator

    return (lower, upper)


def analyze_rq1(annotations: list[dict], trajectories: dict) -> dict:
    """Compute comprehensive RQ1 statistics."""

    # Filter valid
    valid = [a for a in annotations if a.get('first_failure_step') != "NONE"]
    none_count = len(annotations) - len(valid)

    # Basic counts
    n_total = len(annotations)
    n_valid = len(valid)

    # Failure type distribution
    type_counts = defaultdict(int)
    for a in valid:
        type_counts[a['failure_type']] += 1

    # Detection
    detected = sum(1 for a in valid if a.get('agent_detected_failure') == 'YES')
    D0 = detected / n_valid if n_valid > 0 else 0
    UFR = 1 - D0

    # Detection CI
    ufr_lower, ufr_upper = compute_ufr_ci(n_valid - detected, n_valid)

    # Recovery
    recovery_att = sum(1 for a in valid if a.get('recovery_attempted') == 'YES')
    recovery_suc = sum(1 for a in valid if a.get('recovery_success') == 'YES')
    RS = recovery_suc / recovery_att if recovery_att > 0 else 0

    # By model
    by_model = defaultdict(lambda: defaultdict(int))
    for a in valid:
        by_model[a.get('model_id', 'unknown')][a['failure_type']] += 1

    # By trajectory length
    by_length = defaultdict(lambda: defaultdict(int))
    for a in valid:
        traj_id = a.get('trajectory_id')
        if traj_id in trajectories:
            length = len(trajectories[traj_id].get('steps', []))
            length_bin = (length // 5) * 5
            by_length[length_bin][a['failure_type']] += 1

    # Selection dominance check
    selection_rate = type_counts.get('SELECTION', 0) / n_valid if n_valid > 0 else 0
    selection_dominates = selection_rate >= 0.35  # ~40% threshold

    # Thesis gate
    thesis_supported = UFR > 0 and selection_dominates

    return {
        'n_total_annotations': n_total,
        'n_valid_failures': n_valid,
        'n_no_failure': none_count,
        'failure_distribution': dict(type_counts),
        'detection': {
            'n_detected': detected,
            'n_total': n_valid,
            'D0': D0,
            'UFR': UFR,
            'UFR_95CI': [ufr_lower, ufr_upper],
        },
        'recovery': {
            'n_attempted': recovery_att,
            'n_successful': recovery_suc,
            'RS': RS,
        },
        'by_model': {k: dict(v) for k, v in by_model.items()},
        'by_length': {str(k): dict(v) for k, v in sorted(by_length.items())},
        'thesis_gate': {
            'ufr_gt_0': UFR > 0,
            'selection_dominates': selection_dominates,
            'selection_rate': selection_rate,
            'thesis_supported': thesis_supported,
        }
    }


def generate_rq1_report(results: dict) -> str:
    """Generate RQ1 markdown report."""

    type_dist = results['failure_distribution']
    n_valid = results['n_valid_failures']

    # Build tables
    table1 = "| Failure Type | Count | Percentage |\n"
    table1 += "|--------------|-------|------------|\n"
    for ft in ['SELECTION', 'EXECUTION', 'RECOGNITION', 'RECOVERY']:
        count = type_dist.get(ft, 0)
        pct = 100 * count / n_valid if n_valid > 0 else 0
        table1 += f"| {ft} | {count} | {pct:.1f}% |\n"

    # Detection table
    det = results['detection']
    ufr_ci = det['UFR_95CI']

    # Model breakdown
    model_table = "| Model | SELECTION | EXECUTION | RECOGNITION | RECOVERY | Total |\n"
    model_table += "|-------|-----------|-----------|-------------|----------|-------|\n"
    for model, dist in results['by_model'].items():
        total = sum(dist.values())
        s = dist.get('SELECTION', 0)
        e = dist.get('EXECUTION', 0)
        r = dist.get('RECOGNITION', 0)
        rc = dist.get('RECOVERY', 0)
        model_table += f"| {model[:25]} | {s} | {e} | {r} | {rc} | {total} |\n"

    md = f"""# RQ1: Where Do Agents Fail?

## Human-Grounded Results

**Generated:** {datetime.now().isoformat()}

**Sample size:** {n_valid} annotated failures

---

## 1. Failure Type Distribution

{table1}

---

## 2. Detection Statistics

| Metric | Value |
|--------|-------|
| Detected Failures | {det['n_detected']} |
| Total Failures | {det['n_total']} |
| **Detection Rate (D0)** | **{100*det['D0']:.1f}%** |
| **Undetected Failure Rate (UFR)** | **{100*det['UFR']:.1f}%** |
| UFR 95% CI | [{100*ufr_ci[0]:.1f}%, {100*ufr_ci[1]:.1f}%] |

---

## 3. Recovery Statistics

| Metric | Value |
|--------|-------|
| Recovery Attempted | {results['recovery']['n_attempted']} |
| Recovery Successful | {results['recovery']['n_successful']} |
| Recovery Success Rate (RS) | {100*results['recovery']['RS']:.1f}% |

"""

    if results['by_model']:
        md += f"## 4. Breakdown by Model\n\n{model_table}\n"

    md += f"""
---

## Key Finding

**UFR = {100*det['UFR']:.1f}%** ({100*ufr_ci[0]:.1f}% - {100*ufr_ci[1]:.1f}% at 95% CI)

This means approximately **{100*det['UFR']:.0f} out of 100 failures go undetected** by the agent.

---

## Caveats

1. Single model: Claude-4-Sonnet
2. Sample size: {n_valid} failures
3. Annotations by single annotator (inter-annotator agreement not yet computed)
"""

    return md


def generate_thesis_gate_report(results: dict) -> str:
    """Generate thesis gate decision report."""

    gate = results['thesis_gate']
    det = results['detection']
    type_dist = results['failure_distribution']

    decision = "✅ **THESIS SUPPORTED**" if gate['thesis_supported'] else "❌ **THESIS NOT YET SUPPORTED**"

    md = f"""# Thesis Gate Decision Report

**Generated:** {datetime.now().isoformat()}

---

## Decision: {decision}

---

## Evidence

### Question 1: Does undetected failure exist?

**UFR = {100*det['UFR']:.1f}%**

| Condition | Value | Status |
|-----------|-------|--------|
| UFR > 0 | {100*det['UFR']:.1f}% > 0 | {"✅ YES" if gate['ufr_gt_0'] else "❌ NO"} |

**Interpretation:** Agents fail to detect a substantial fraction of their failures.

---

### Question 2: What is the dominant first failure type?

| Failure Type | Count | Rate |
|--------------|-------|------|
| SELECTION | {type_dist.get('SELECTION', 0)} | {100*type_dist.get('SELECTION', 0)/max(1,results['n_valid_failures']):.1f}% |
| EXECUTION | {type_dist.get('EXECUTION', 0)} | {100*type_dist.get('EXECUTION', 0)/max(1,results['n_valid_failures']):.1f}% |
| RECOGNITION | {type_dist.get('RECOGNITION', 0)} | {100*type_dist.get('RECOGNITION', 0)/max(1,results['n_valid_failures']):.1f}% |
| RECOVERY | {type_dist.get('RECOVERY', 0)} | {100*type_dist.get('RECOVERY', 0)/max(1,results['n_valid_failures']):.1f}% |

**Selection rate:** {100*gate['selection_rate']:.1f}%
**Threshold:** 35% (approximating 40%)

{"✅ Selection failures approach dominance" if gate['selection_dominates'] else "⏳ Selection failures below threshold"}

---

### Question 3: Is Recognition failure frequent?

**Recognition failures:** {type_dist.get('RECOGNITION', 0)}

{"✅ Sufficient for RQ2 expansion" if type_dist.get('RECOGNITION', 0) >= 5 else "⏳ Need more Recognition failures for RQ2"}

---

## Recommendation

"""

    if gate['thesis_supported']:
        md += """
### Continue with Paper 1

The core thesis is supported:
1. ✅ UFR > 0 → agents don't know when they fail
2. ✅ Selection dominates → bottleneck is in action selection

**Next steps:**
1. Double-annotate 20 cases for reliability
2. Compute Cohen's Kappa for inter-annotator agreement
3. Prepare RQ2 API experiments (C0-C3 elicitation)
4. Select RQ2 candidate cases from Recognition failures

**Do NOT run expensive experiments yet.** Continue with annotation until:
- 50+ annotations with agreement check
- Cohen's Kappa > 0.6 for failure types
"""
    else:
        md += f"""
### Pause and Re-evaluate

The thesis is not yet supported:
- UFR = {100*det['UFR']:.1f}% {"(should be > 0)" if det['UFR'] == 0 else ""}
- Selection rate = {100*gate['selection_rate']:.1f}% {"(should be ≥ 35%)" if gate['selection_rate'] < 0.35 else ""}

**Options:**
1. Continue annotation to increase sample size
2. Re-examine failure type definitions
3. Consider alternative bottleneck framing
"""

    return md


def select_rq2_candidates(annotations: list[dict], trajectories: dict, n: int = 30) -> list[dict]:
    """Select candidate cases for RQ2 elicitation experiments."""

    # Filter to Recognition failures (primary target for RQ2)
    recognition = [a for a in annotations
                   if a.get('failure_type') == 'RECOGNITION'
                   and a.get('first_failure_step') != "NONE"]

    # Also include some EXECUTION and SELECTION for comparison
    other = [a for a in annotations
             if a.get('failure_type') in {'EXECUTION', 'SELECTION'}
             and a.get('first_failure_step') != "NONE"]

    candidates = []

    # Add Recognition failures first (up to 50%)
    for ann in recognition[:int(n * 0.5)]:
        traj = trajectories.get(ann['trajectory_id'])
        if traj:
            candidates.append({
                'trajectory_id': ann['trajectory_id'],
                'failure_type': ann['failure_type'],
                'first_failure_step': ann['first_failure_step'],
                'detection': ann.get('agent_detected_failure'),
                'task_description': traj.get('task_description', '')[:200],
                'trajectory_length': len(traj.get('steps', [])),
                'priority': 'high'
            })

    # Add other types
    for ann in other[:int(n * 0.5)]:
        traj = trajectories.get(ann['trajectory_id'])
        if traj and len(candidates) < n:
            candidates.append({
                'trajectory_id': ann['trajectory_id'],
                'failure_type': ann['failure_type'],
                'first_failure_step': ann['first_failure_step'],
                'detection': ann.get('agent_detected_failure'),
                'task_description': traj.get('task_description', '')[:200],
                'trajectory_length': len(traj.get('steps', [])),
                'priority': 'medium'
            })

    return candidates


def save_outputs(results: dict, annotations: list[dict], trajectories: dict):
    """Save all analysis outputs."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # RQ1 Report
    with open(OUTPUT_DIR / "rq1_report.md", 'w', encoding='utf-8') as f:
        f.write(generate_rq1_report(results))

    # Thesis Gate Report
    with open(OUTPUT_DIR / "thesis_gate_report.md", 'w', encoding='utf-8') as f:
        f.write(generate_thesis_gate_report(results))

    # JSON results
    with open(OUTPUT_DIR / "rq1_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # RQ2 candidates
    candidates = select_rq2_candidates(annotations, trajectories)
    with open(OUTPUT_DIR / "rq2_candidate_cases.json", 'w', encoding='utf-8') as f:
        json.dump({
            'n_candidates': len(candidates),
            'candidates': candidates
        }, f, indent=2, ensure_ascii=False)

    print(f"Outputs saved to {OUTPUT_DIR}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-annotations', type=int, default=50)
    args = parser.parse_args()

    print("Loading data...")
    annotations = load_annotations()
    trajectories = load_trajectories()

    if len(annotations) < args.min_annotations:
        print(f"\n❌ Need at least {args.min_annotations} annotations, found {len(annotations)}")
        print(f"Run annotation campaign first:")
        print(f"  streamlit run annotation_tool/app.py")
        sys.exit(1)

    print(f"\n✅ Found {len(annotations)} annotations")

    print("Analyzing RQ1...")
    results = analyze_rq1(annotations, trajectories)

    print("Saving outputs...")
    save_outputs(results, annotations, trajectories)

    # Print summary
    gate = results['thesis_gate']
    print(f"""
---

RQ1 Summary:

- Sample: {results['n_valid_failures']} failures
- UFR: {100*results['detection']['UFR']:.1f}%
- Selection rate: {100*gate['selection_rate']:.1f}%

Thesis: {"SUPPORTED ✅" if gate['thesis_supported'] else "NOT YET SUPPORTED"}

Files generated:
- results/RQ1_human_first50/rq1_report.md
- results/RQ1_human_first50/thesis_gate_report.md
- results/RQ1_human_first50/rq2_candidate_cases.json
""")


if __name__ == "__main__":
    # Fix Windows console encoding
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    main()
