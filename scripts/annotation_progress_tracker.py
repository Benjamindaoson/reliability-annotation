#!/usr/bin/env python3
"""
Annotation Progress Tracker

Generates real-time progress reports for the human annotation campaign.

Usage:
    python scripts/annotation_progress_tracker.py
    python scripts/annotation_progress_tracker.py --report full
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ANNOTATION_FILE = Path("data/human_annotations/annotations.jsonl")
DATA_FILE = Path("data/raw/osworld_claude4_converted.json")


def load_annotations() -> list[dict]:
    """Load all annotations."""
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


def compute_progress(annotations: list[dict], trajectories: dict) -> dict:
    """Compute progress statistics."""
    n_total = 200
    n_annotated = len(annotations)

    # Valid failures
    valid = [a for a in annotations if a.get('first_failure_step') != "NONE"]

    # Failure type distribution
    by_type = defaultdict(int)
    for a in valid:
        by_type[a['failure_type']] += 1

    # Detection statistics
    detected = sum(1 for a in valid if a.get('agent_detected_failure') == 'YES')
    n_valid = len(valid)

    # Recovery statistics
    recovery_att = sum(1 for a in valid if a.get('recovery_attempted') == 'YES')
    recovery_suc = sum(1 for a in valid if a.get('recovery_success') == 'YES')

    # Confidence distribution
    by_conf = defaultdict(int)
    for a in annotations:
        by_conf[a.get('confidence', 'unknown')] += 1

    return {
        'timestamp': datetime.now().isoformat(),
        'total_trajectories': n_total,
        'n_annotated': n_annotated,
        'n_remaining': n_total - n_annotated,
        'progress_pct': 100 * n_annotated / n_total,
        'n_valid_failures': n_valid,
        'n_no_failure': len(annotations) - n_valid,
        'failure_distribution': dict(by_type),
        'detection_rate': detected / n_valid if n_valid > 0 else 0,
        'ufr': 1 - (detected / n_valid if n_valid > 0 else 0),
        'n_detected': detected,
        'n_total_failures': n_valid,
        'recovery_attempted': recovery_att,
        'recovery_success': recovery_suc,
        'recovery_rate': recovery_suc / recovery_att if recovery_att > 0 else 0,
        'confidence_distribution': dict(by_conf),
    }


def generate_markdown_report(progress: dict) -> str:
    """Generate markdown progress report."""

    # Check if we have enough for RQ1
    ready_for_rq1 = progress['n_annotated'] >= 50

    md = f"""# Human Annotation Campaign Progress

**Generated:** {progress['timestamp']}

---

## Overall Progress

| Metric | Value |
|--------|-------|
| Total Trajectories | {progress['total_trajectories']} |
| Annotated | {progress['n_annotated']} |
| Remaining | {progress['n_remaining']} |
| Progress | {progress['progress_pct']:.1f}% |

{"## RQ1 Ready" if ready_for_rq1 else "## Awaiting More Annotations for RQ1"}

{"✅ **50+ annotations complete - RQ1 analysis possible!**" if ready_for_rq1 else f"⏳ Need {50 - progress['n_annotated']} more annotations for RQ1"}

"""

    if progress['n_annotated'] > 0:
        md += f"""---

## Failure Type Distribution (n={progress['n_valid_failures']})

| Failure Type | Count | Percentage |
|--------------|-------|------------|
| SELECTION | {progress['failure_distribution'].get('SELECTION', 0)} | {100*progress['failure_distribution'].get('SELECTION', 0)/max(1,progress['n_valid_failures']):.1f}% |
| EXECUTION | {progress['failure_distribution'].get('EXECUTION', 0)} | {100*progress['failure_distribution'].get('EXECUTION', 0)/max(1,progress['n_valid_failures']):.1f}% |
| RECOGNITION | {progress['failure_distribution'].get('RECOGNITION', 0)} | {100*progress['failure_distribution'].get('RECOGNITION', 0)/max(1,progress['n_valid_failures']):.1f}% |
| RECOVERY | {progress['failure_distribution'].get('RECOVERY', 0)} | {100*progress['failure_distribution'].get('RECOVERY', 0)/max(1,progress['n_valid_failures']):.1f}% |

---

## Detection Statistics

| Metric | Value |
|--------|-------|
| Detected Failures | {progress['n_detected']} |
| Total Failures | {progress['n_total_failures']} |
| **Detection Rate (D0)** | **{100*progress['detection_rate']:.1f}%** |
| **Undetected Failure Rate (UFR)** | **{100*progress['ufr']:.1f}%** |

---

## Recovery Statistics

| Metric | Value |
|--------|-------|
| Recovery Attempted | {progress['recovery_attempted']} |
| Recovery Successful | {progress['recovery_success']} |
| Recovery Rate | {100*progress['recovery_rate']:.1f}% |

---

## Annotation Confidence

| Confidence | Count |
|------------|-------|
| High | {progress['confidence_distribution'].get('high', 0)} |
| Medium | {progress['confidence_distribution'].get('medium', 0)} |
| Low | {progress['confidence_distribution'].get('low', 0)} |

---

## Thesis Gate Check

**Core Question:** Does UFR > 0 AND do Selection failures dominate?

Current evidence:
- UFR = {100*progress['ufr']:.1f}% {"✅ > 0" if progress['ufr'] > 0 else "❌ = 0"}
- Selection rate = {100*progress['failure_distribution'].get('SELECTION', 0)/max(1,progress['n_valid_failures']):.1f}%
{"✅ Approaching 40% threshold" if progress['failure_distribution'].get('SELECTION', 0)/max(1,progress['n_valid_failures']) > 0.35 else "⏳ Below 40% threshold"}

---

## Next Steps

"""

        if not ready_for_rq1:
            md += f"""1. Continue annotation to reach 50
2. Target: {50 - progress['n_annotated']} more trajectories

Run analysis when ready:
```bash
python scripts/phase32_regenerate_rq1.py
```
"""
        else:
            md += """1. ✅ **RQ1 analysis now possible!**
2. Run: `python scripts/phase32_regenerate_rq1.py`
3. Check thesis gate results
4. Prepare RQ2 candidate cases

"""
    else:
        md += """

---

## Getting Started

Run the annotation tool:
```bash
streamlit run annotation_tool/app.py
```

Or use the command-line batch tool:
```bash
python scripts/batch_annotation_tool.py --batch annotation_batches/batch_001.json
```

"""

    return md


def save_progress_json(progress: dict):
    """Save progress as JSON."""
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "annotation_progress.json", 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def save_progress_md(progress: dict):
    """Save progress as Markdown."""
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    md = generate_markdown_report(progress)

    with open(output_dir / "annotation_progress.md", 'w', encoding='utf-8') as f:
        f.write(md)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Annotation progress tracker")
    parser.add_argument('--report', choices=['full', 'brief'], default='full')
    args = parser.parse_args()

    print("Loading annotations...")
    annotations = load_annotations()
    trajectories = load_trajectories()

    print("Computing progress...")
    progress = compute_progress(annotations, trajectories)

    if args.report == 'brief':
        print(f"\nProgress: {progress['n_annotated']}/{progress['total_trajectories']} ({progress['progress_pct']:.1f}%)")
        if progress['n_annotated'] > 0:
            print(f"UFR: {100*progress['ufr']:.1f}%")
            print(f"Detection rate: {100*progress['detection_rate']:.1f}%")
    else:
        # Save reports
        save_progress_json(progress)
        save_progress_md(progress)

        print("\n" + generate_markdown_report(progress))

        print("\nReports saved to:")
        print("  results/annotation_progress.json")
        print("  results/annotation_progress.md")


if __name__ == "__main__":
    # Fix Windows console encoding
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    main()
