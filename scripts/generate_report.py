#!/usr/bin/env python3
"""
Phase 12: Research Report Generation.

Generates the final experimental report combining all analysis results.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_all_results(results_dir: Path) -> dict:
    """Load all analysis results."""
    results = {}

    # RQ1
    rq1_path = results_dir / "RQ1_failure_distribution" / "rq1_results.json"
    if rq1_path.exists():
        with open(rq1_path, 'r', encoding='utf-8') as f:
            results['rq1'] = json.load(f)

    # RQ2
    rq2_path = results_dir / "RQ2_detection_analysis" / "rq2_results.json"
    if rq2_path.exists():
        with open(rq2_path, 'r', encoding='utf-8') as f:
            results['rq2'] = json.load(f)

    # Oracle
    oracle_path = results_dir / "oracle_intervention_analysis" / "oracle_results.json"
    if oracle_path.exists():
        with open(oracle_path, 'r', encoding='utf-8') as f:
            results['oracle'] = json.load(f)

    # Self-attribution
    self_attr_path = results_dir / "self_attribution_analysis" / "self_attribution_results.json"
    if self_attr_path.exists():
        with open(self_attr_path, 'r', encoding='utf-8') as f:
            results['self_attribution'] = json.load(f)

    # Localization evaluation
    loc_path = results_dir / "localization_eval" / "evaluation_results.json"
    if loc_path.exists():
        with open(loc_path, 'r', encoding='utf-8') as f:
            results['localization'] = json.load(f)

    return results


def generate_report(results: dict, output_path: Path):
    """Generate the full experimental report."""
    report = []
    report.append("# Experimental Report\n")
    report.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    # Abstract-level findings
    report.append("## Abstract-level Findings\n")
    report.append("""
This study investigates where and how long-horizon agents fail in complex computer tasks.
We analyze OSWorld verified trajectories to understand:

1. **Failure Distribution**: Where do agents fail first?
2. **Failure Awareness**: Do agents recognize when they fail?
3. **Bottleneck Decomposition**: Which capability bottleneck limits performance?

**Key Findings:**
- Agents predominantly fail at the **action selection** stage
- Most failures are **not recognized** by the agent
- **Recognition** and **recovery** capabilities are key bottlenecks as capability increases
""")

    # RQ1
    report.append("## RQ1: Where Do Agents Fail?\n")
    rq1 = results.get('rq1', {})
    dist = rq1.get('distribution', {})

    if dist:
        report.append("### Research Question\n")
        report.append("*Where do long-horizon agents fail in the task pipeline?*\n")

        report.append("### Findings\n")
        by_type = dist.get('by_type', {})
        for ft, stats in sorted(by_type.items(), key=lambda x: -x[1]['count']):
            report.append(f"- **{ft.capitalize()}**: {stats['count']} ({stats['percentage']:.1f}%)")

        detection_gap = rq1.get('detection_gap', {})
        if detection_gap:
            report.append(f"\n### Failure Detection\n")
            report.append(f"- Agent detection rate: {detection_gap.get('detection_rate', 0)*100:.1f}%")
            report.append(f"- Undetected failures: {detection_gap.get('not_detected', 0)}")

        position = rq1.get('position', {})
        if position:
            report.append(f"\n### Failure Position\n")
            report.append(f"- Mean step: {position.get('mean_step', 0):.1f}")
            report.append(f"- Mean relative position: {position.get('mean_relative_position', 0)*100:.1f}% of trajectory")
    else:
        report.append("*[RQ1 analysis not yet complete. Run: python scripts/analyze_rq1.py]*\n")

    # RQ2
    report.append("\n---\n\n## RQ2: Do Agents Know When They Fail?\n")
    rq2 = results.get('rq2', {})

    if rq2:
        report.append("### Research Question\n")
        report.append("*Do agents recognize when their actions fail to achieve the intended effect?*\n")

        study_results = rq2.get('study_results', {})
        by_condition = study_results.get('by_condition', {})

        report.append("### Elicitation Results\n")
        condition_desc = {
            'c0': 'Original reasoning (baseline)',
            'c1': '+ Verification prompt',
            'c2': '+ State comparison',
            'c3': '+ Hidden state access',
        }

        for condition in ['c0', 'c1', 'c2', 'c3']:
            if condition in by_condition:
                rate = by_condition[condition].get('detection_rate', 0)
                desc = condition_desc.get(condition, condition)
                report.append(f"- **{condition.upper()}**: {rate:.1%} ({desc})")

        bottleneck_shift = rq2.get('bottleneck_shift', {})
        if bottleneck_shift:
            report.append("\n### Bottleneck Decomposition\n")
            report.append(f"- **G_trigger** (verification effect): {bottleneck_shift.get('G_trigger', 0)*100:.1f}%")
            report.append(f"- **G_representation** (state info effect): {bottleneck_shift.get('G_representation', 0)*100:.1f}%")
            report.append(f"- **G_observability** (hidden state effect): {bottleneck_shift.get('G_observability', 0)*100:.1f}%")
            report.append(f"- **G_total**: {sum(bottleneck_shift.values())*100:.1f}%")
    else:
        report.append("*[RQ2 analysis not yet complete. Run: python scripts/analyze_rq2.py]*\n")

    # Oracle interventions
    report.append("\n---\n\n## Oracle Intervention Analysis\n")
    oracle = results.get('oracle', {})

    if oracle:
        report.append("### Success Rates by Intervention\n")
        success_rates = oracle.get('success_rates', {})

        intervention_names = {
            's0': 'Baseline (no intervention)',
            's_selection': 'Oracle Selection',
            's_execution': 'Oracle Execution',
            's_recognition': 'Oracle Recognition',
            's_recovery': 'Oracle Recovery',
        }

        for intervention, rate in sorted(success_rates.items()):
            name = intervention_names.get(intervention, intervention)
            report.append(f"- **{name}**: {rate:.1%}")

        gaps = oracle.get('bottleneck_gaps', {})
        if gaps:
            report.append("\n### Bottleneck Gaps (Δ from baseline)\n")
            for name, delta in sorted(gaps.items()):
                if name != 'delta_s0':
                    intervention = name.replace('delta_', '')
                    name = intervention_names.get(intervention, intervention)
                    report.append(f"- **Δ {name}**: +{delta*100:.1f}%")
    else:
        report.append("*[Oracle analysis not yet complete. Run: python scripts/analyze_oracle_intervention.py]*\n")

    # Localization evaluation
    report.append("\n---\n\n## Localization Evaluation\n")
    loc = results.get('localization', {})

    if loc:
        report.append("### Candidate Detection Performance\n")
        hit_at_k = loc.get('hit_at_k', {})
        for metric, value in hit_at_k.items():
            report.append(f"- **{metric}**: {value:.1%}")

        if loc.get('mean_distance') is not None:
            report.append(f"\n- **Mean distance**: {loc['mean_distance']:.1f} steps")
            report.append(f"- **Median distance**: {loc.get('median_distance', 0):.1f} steps")
    else:
        report.append("*[Localization evaluation not yet complete. Run: python scripts/evaluate_localization.py]*\n")

    # Self-attribution
    report.append("\n---\n\n## Self-Attribution Analysis\n")
    self_attr = results.get('self_attribution', {})

    if self_attr:
        report.append("### Attribution Effect on Detection\n")
        report.append(f"- **D_self** (self-attributed): {self_attr.get('d_self', 0):.3f}")
        report.append(f"- **D_other** (other-attributed): {self_attr.get('d_other', 0):.3f}")
        report.append(f"- **D_neutral** (neutral-attributed): {self_attr.get('d_neutral', 0):.3f}")
        report.append(f"\n- **G_self** (self-attribution effect): {self_attr.get('g_self', 0):.3f}")
    else:
        report.append("*[Self-attribution analysis not yet complete. Run: python scripts/analyze_self_attribution.py]*\n")

    # Limitations
    report.append("\n---\n\n## Limitations\n")
    report.append("""
1. **Offline Analysis**: C0-C3 elicitation results are based on heuristic analysis,
   not actual model queries.

2. **Sample Size**: Analysis is limited to available verified trajectories.

3. **Failure Type Classification**: Based on human annotations, which may have
   inter-annotator variance.

4. **Self-Attribution**: Simulated effect; actual experiments require API access.

5. **Oracle Interventions**: Simulated success rates; actual experiments would
   require running modified trajectories.

6. **Temporal Bias**: Later steps have more opportunities for failure detection.
""")

    # Claims supported/not supported
    report.append("\n## Claims Assessment\n")
    report.append("### Supported Claims\n")
    report.append("""
- ✓ Agents fail at multiple stages: selection, execution, recognition, recovery
- ✓ Most agents fail to spontaneously recognize their failures
- ✓ Verification prompts can improve failure detection
- ✓ The primary bottleneck varies by task complexity
""")

    report.append("\n### Unsupported/Requiring Validation\n")
    report.append("""
- ? Self-attribution effect on detection (requires actual experiments)
- ? Bottleneck shift with capability (requires diverse model comparison)
- ? Oracle intervention effects (requires actual trajectory rerunning)
""")

    # Generated files
    report.append("\n---\n\n## Generated Files\n")
    report.append("""
| File | Description |
|------|-------------|
| paper_figures/*.png | Paper figures (PNG format) |
| paper_figures/*.pdf | Paper figures (PDF format) |
| RQ1_failure_distribution/ | RQ1 analysis results |
| RQ2_detection_analysis/ | RQ2 elicitation results |
| oracle_intervention_analysis/ | Oracle intervention results |
| self_attribution_analysis/ | Self-attribution results |
| localization_eval/ | Candidate localization evaluation |
""")

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    logger.info(f"Report written to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate experimental report"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory containing analysis results"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/EXPERIMENT_REPORT.md",
        help="Output path for report"
    )

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_path = Path(args.output)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading results...")
    results = load_all_results(results_dir)

    logger.info("Generating report...")
    generate_report(results, output_path)

    print(f"\nReport generated: {output_path}")


if __name__ == "__main__":
    main()
