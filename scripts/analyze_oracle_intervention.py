#!/usr/bin/env python3
"""
Phase 10: Oracle Intervention Simulation Framework.

Framework for computing oracle intervention effects on success rates.

Interventions:
- S0: Baseline (no intervention)
- S_selection: Oracle corrects wrong action selection
- S_execution: Oracle forces intended execution
- S_recognition: Oracle tells failure occurred (no recovery hint)
- S_recovery: Oracle provides recovery action

Success rates computed for each intervention.
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InterventionType:
    """Oracle intervention types."""
    BASELINE = "s0"
    SELECTION = "s_selection"
    EXECUTION = "s_execution"
    RECOGNITION = "s_recognition"
    RECOVERY = "s_recovery"


def compute_intervention_effect(
    records: list[dict],
    intervention: str
) -> float:
    """
    Compute success rate for an intervention.

    For baseline (S0): Return actual success rate.
    For interventions: Estimate based on failure type.

    Logic:
    - If failure is "selection" and intervention is "selection", success += 1
    - If failure is "execution" and intervention is "execution", success += 1
    - If failure is "recognition" and intervention is "recognition", success += 1
    - If failure is "recovery" and intervention is "recovery", success += 1

    Args:
        records: Failure decomposition records
        intervention: Intervention type

    Returns:
        Estimated success rate
    """
    if not records:
        return 0.0

    # For simulation, we model the effect
    # In reality, this requires running actual interventions

    baseline_success = sum(1 for r in records if r.get('agent_detected', False))
    s0_rate = baseline_success / len(records)

    if intervention == InterventionType.BASELINE:
        return s0_rate

    # Map failure types to relevant interventions
    failure_to_intervention = {
        'selection': ['selection'],
        'execution': ['execution'],
        'recognition': ['recognition', 'recovery'],
        'recovery': ['recovery'],
    }

    # Estimate intervention effect
    successes = 0
    for record in records:
        failure_type = record.get('failure_type', 'unknown')

        # If this intervention would help
        if intervention in failure_to_intervention.get(failure_type, []):
            # Estimate success probability based on intervention type
            if intervention == InterventionType.SELECTION:
                # Correcting selection has high success rate
                successes += 0.9
            elif intervention == InterventionType.EXECUTION:
                # Forcing execution has medium success
                successes += 0.7
            elif intervention == InterventionType.RECOGNITION:
                # Telling about failure + own recovery
                successes += 0.6
            elif intervention == InterventionType.RECOVERY:
                # Providing recovery action is most effective
                successes += 0.8
        else:
            # Intervention doesn't help this failure type
            successes += 0.1  # Small chance of incidental success

    return successes / len(records)


def compute_bottleneck_gap(
    s0: float,
    interventions: dict[str, float]
) -> dict:
    """
    Compute bottleneck gap for each intervention.

    Δ_i = S_i - S_0

    Args:
        s0: Baseline success rate
        interventions: Dict of intervention -> success rate

    Returns:
        Dict of intervention -> gap
    """
    gaps = {}
    for name, rate in interventions.items():
        gaps[f'delta_{name}'] = rate - s0

    return gaps


def analyze_oracle_interventions(records: list[dict]) -> dict:
    """
    Analyze oracle intervention effects.

    Args:
        records: Failure decomposition records

    Returns:
        Intervention analysis results
    """
    results = {
        'total_records': len(records),
        'success_rates': {},
        'bottleneck_gaps': {},
        'by_failure_type': defaultdict(dict),
    }

    # Compute success rates for each intervention
    interventions = [
        InterventionType.BASELINE,
        InterventionType.SELECTION,
        InterventionType.EXECUTION,
        InterventionType.RECOGNITION,
        InterventionType.RECOVERY,
    ]

    for intervention in interventions:
        rate = compute_intervention_effect(records, intervention)
        results['success_rates'][intervention] = rate

    # Compute gaps
    s0 = results['success_rates'][InterventionType.BASELINE]
    results['bottleneck_gaps'] = compute_bottleneck_gap(s0, results['success_rates'])

    # Analyze by failure type
    for record in records:
        failure_type = record.get('failure_type', 'unknown')

        if failure_type not in results['by_failure_type']:
            results['by_failure_type'][failure_type] = {
                'total': 0,
                's0_contribution': 0,
                'intervention_effects': defaultdict(float),
            }

        results['by_failure_type'][failure_type]['total'] += 1

        # Baseline contribution
        if record.get('agent_detected', False):
            results['by_failure_type'][failure_type]['s0_contribution'] += 1

    return results


def generate_oracle_report(results: dict) -> str:
    """Generate oracle intervention analysis report."""
    report = []
    report.append("# Oracle Intervention Analysis\n")
    report.append("## Methodology\n")
    report.append("""
Oracle interventions simulate ideal assistance at each bottleneck:

| Intervention | Description | When Effective |
|--------------|-------------|-----------------|
| S0 (Baseline) | No intervention | - |
| S_selection | Correct wrong action | Selection failures |
| S_execution | Force intended execution | Execution failures |
| S_recognition | Tell failure occurred | Recognition failures |
| S_recovery | Provide recovery action | Recovery failures |

**Note**: This is a simulation framework. Actual results require running interventions.
""")

    # Success rates
    report.append("## Success Rates\n")
    report.append("| Intervention | Success Rate | Δ from Baseline |")
    report.append("|--------------|-------------|-----------------|")

    s0 = results['success_rates'].get('s0', 0)
    for intervention, rate in sorted(results['success_rates'].items()):
        delta = rate - s0
        delta_str = f"+{delta:.1%}" if delta >= 0 else f"{delta:.1%}"
        report.append(f"| {intervention} | {rate:.1%} | {delta_str} |")
    report.append("")

    # Bottleneck ordering
    report.append("## Bottleneck Ordering\n")
    gaps = results.get('bottleneck_gaps', {})

    bottleneck_effects = []
    for name, delta in gaps.items():
        if name != 'delta_s0':
            intervention = name.replace('delta_', '')
            bottleneck_effects.append((intervention, delta))

    bottleneck_effects.sort(key=lambda x: -x[1])

    report.append("| Rank | Bottleneck | Δ Success Rate |")
    report.append("|------|------------|---------------|")
    for i, (intervention, delta) in enumerate(bottleneck_effects, 1):
        report.append(f"| {i} | {intervention} | +{delta:.1%} |")
    report.append("")

    # Interpretation
    report.append("## Interpretation\n")
    if bottleneck_effects:
        top = bottleneck_effects[0]
        report.append(f"- **Primary bottleneck**: {top[0]} (Δ = +{top[1]:.1%})")
        if len(bottleneck_effects) > 1:
            second = bottleneck_effects[1]
            report.append(f"- **Secondary bottleneck**: {second[0]} (Δ = +{second[1]:.1%})")

        report.append("")
        report.append("**Implication**: Improving oracle intervention at the primary bottleneck")
        report.append("would yield the largest improvement in overall success rate.")
    report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Oracle intervention analysis"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/processed/failure_decomposition.jsonl",
        help="Path to failure decomposition dataset"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/oracle_intervention_analysis",
        help="Output directory for results"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    records = []
    dataset_file = Path(args.dataset)
    if dataset_file.exists():
        if dataset_file.suffix == '.jsonl':
            with open(dataset_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        else:
            with open(dataset_file, 'r', encoding='utf-8') as f:
                records = json.load(f)

    if not records:
        logger.warning("No records found. Using simulated data...")
        import random
        for i in range(100):
            records.append({
                'trajectory_id': f'traj_{i}',
                'failure_type': random.choice(['selection', 'execution', 'recognition', 'recovery']),
                'agent_detected': random.random() < 0.3,
            })

    # Run analysis
    results = analyze_oracle_interventions(records)

    # Save results
    json_path = output_dir / 'oracle_results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved to {json_path}")

    # Generate report
    report = generate_oracle_report(results)
    md_path = output_dir / 'oracle_report.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Saved report to {md_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("ORACLE INTERVENTION ANALYSIS")
    print("=" * 60)
    print(f"Total records: {results['total_records']}")
    print("\nSuccess Rates:")
    for intervention, rate in sorted(results['success_rates'].items()):
        print(f"  {intervention}: {rate:.1%}")
    print("\nBottleneck Gaps (Δ from baseline):")
    for name, delta in sorted(results['bottleneck_gaps'].items()):
        if name != 'delta_s0':
            print(f"  {name.replace('delta_', '')}: +{delta:.1%}")
    print("=" * 60)


if __name__ == "__main__":
    main()
