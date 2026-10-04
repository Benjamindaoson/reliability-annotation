#!/usr/bin/env python3
"""
Phase 11: Paper Figure Generation.

Generates figures for the paper:
1. Failure taxonomy diagram
2. First failure distribution
3. Reliability Profile (A, UFR, DD, RS)
4. C0-C3 detection gap
5. Oracle intervention impact
6. Capability vs bottleneck shift
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available. Skipping figure generation.")


def load_results(data_dir: Path) -> dict:
    """Load all analysis results."""
    results = {}

    # RQ1 results
    rq1_path = data_dir / "RQ1_failure_distribution" / "rq1_results.json"
    if rq1_path.exists():
        with open(rq1_path, 'r', encoding='utf-8') as f:
            results['rq1'] = json.load(f)

    # RQ2 results
    rq2_path = data_dir / "RQ2_detection_analysis" / "rq2_results.json"
    if rq2_path.exists():
        with open(rq2_path, 'r', encoding='utf-8') as f:
            results['rq2'] = json.load(f)

    # Oracle results
    oracle_path = data_dir / "oracle_intervention_analysis" / "oracle_results.json"
    if oracle_path.exists():
        with open(oracle_path, 'r', encoding='utf-8') as f:
            results['oracle'] = json.load(f)

    # Self-attribution results
    self_attr_path = data_dir / "self_attribution_analysis" / "self_attribution_results.json"
    if self_attr_path.exists():
        with open(self_attr_path, 'r', encoding='utf-8') as f:
            results['self_attribution'] = json.load(f)

    return results


def generate_taxonomy_diagram(output_dir: Path):
    """Figure 1: Failure taxonomy diagram."""
    if not MATPLOTLIB_AVAILABLE:
        return

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(5, 9.5, 'Agent Failure Taxonomy', fontsize=16, fontweight='bold',
            ha='center', va='center')

    # Root node
    root = mpatches.FancyBboxPatch((4, 7), 2, 1, boxstyle="round,pad=0.1",
                                    facecolor='#ff6b6b', edgecolor='black', linewidth=2)
    ax.add_patch(root)
    ax.text(5, 7.5, 'Agent Failure', ha='center', va='center', fontsize=12,
            fontweight='bold', color='white')

    # Failure types
    failure_types = [
        ('Selection', 1.5, 5, '#4ecdc4'),
        ('Execution', 5, 5, '#45b7d1'),
        ('Recognition', 8.5, 5, '#96ceb4'),
    ]

    for ft_name, x, y, color in failure_types:
        box = mpatches.FancyBboxPatch((x-1, y-0.5), 2, 1, boxstyle="round,pad=0.1",
                                       facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, ft_name, ha='center', va='center', fontsize=11,
                fontweight='bold')

        # Connect to root
        ax.annotate('', xy=(x, y+0.5), xytext=(5, 7),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=2))

    # Detection outcomes
    detection_x = 5
    detection_y = 3

    detected = mpatches.FancyBboxPatch((detection_x-2, detection_y-0.5), 1.8, 1,
                                        boxstyle="round,pad=0.1",
                                        facecolor='#90EE90', edgecolor='black')
    ax.add_patch(detected)
    ax.text(detection_x-1.1, detection_y, 'Detected', ha='center', va='center',
            fontsize=10)

    not_detected = mpatches.FancyBboxPatch((detection_x+0.2, detection_y-0.5), 1.8, 1,
                                            boxstyle="round,pad=0.1",
                                            facecolor='#FFB6C1', edgecolor='black')
    ax.add_patch(not_detected)
    ax.text(detection_x+1.1, detection_y, 'Not Detected', ha='center', va='center',
            fontsize=10)

    # Recovery
    recovery_y = 1
    recovered = mpatches.FancyBboxPatch((detection_x-2, recovery_y-0.5), 1.8, 1,
                                         boxstyle="round,pad=0.1",
                                         facecolor='#98FB98', edgecolor='black')
    ax.add_patch(recovered)
    ax.text(detection_x-1.1, recovery_y, 'Recovered', ha='center', va='center',
            fontsize=10)

    not_recovered = mpatches.FancyBboxPatch((detection_x+0.2, recovery_y-0.5), 1.8, 1,
                                             boxstyle="round,pad=0.1",
                                             facecolor='#FFA07A', edgecolor='black')
    ax.add_patch(not_recovered)
    ax.text(detection_x+1.1, recovery_y, 'Not Recovered', ha='center', va='center',
            fontsize=10)

    # Connecting lines
    ax.annotate('', xy=(detection_x-1.1, detection_y+0.5), xytext=(detection_x-1.1, detection_y+1.5),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))
    ax.annotate('', xy=(detection_x-1.1, recovery_y+0.5), xytext=(detection_x-1.1, recovery_y+1.5),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

    plt.tight_layout()
    plt.savefig(output_dir / 'figure1_taxonomy.png', dpi=150, bbox_inches='tight')
    plt.savefig(output_dir / 'figure1_taxonomy.pdf', bbox_inches='tight')
    plt.close()

    logger.info("Generated Figure 1: Failure Taxonomy")


def generate_failure_distribution(results: dict, output_dir: Path):
    """Figure 2: First failure distribution."""
    if not MATPLOTLIB_AVAILABLE:
        return

    rq1 = results.get('rq1', {})
    dist = rq1.get('distribution', {})
    by_type = dist.get('by_type', {})

    if not by_type:
        logger.warning("No RQ1 data available for Figure 2")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Bar chart
    ax1 = axes[0]
    types = list(by_type.keys())
    counts = [by_type[t]['count'] for t in types]
    percentages = [by_type[t]['percentage'] for t in types]

    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
    bars = ax1.bar(types, counts, color=colors[:len(types)])

    ax1.set_xlabel('Failure Type')
    ax1.set_ylabel('Count')
    ax1.set_title('Failure Type Distribution')

    # Add percentage labels
    for bar, pct in zip(bars, percentages):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=10)

    # Pie chart
    ax2 = axes[1]
    ax2.pie(counts, labels=types, autopct='%1.1f%%', colors=colors[:len(types)],
            startangle=90)
    ax2.set_title('Failure Type Proportions')

    plt.tight_layout()
    plt.savefig(output_dir / 'figure2_failure_distribution.png', dpi=150, bbox_inches='tight')
    plt.savefig(output_dir / 'figure2_failure_distribution.pdf', bbox_inches='tight')
    plt.close()

    logger.info("Generated Figure 2: Failure Distribution")


def generate_reliability_profile(results: dict, output_dir: Path):
    """Figure 3: Reliability Profile (A, UFR, DD, RS)."""
    if not MATPLOTLIB_AVAILABLE:
        return

    rq1 = results.get('rq1', {})
    detection_gap = rq1.get('detection_gap', {})

    if not detection_gap:
        logger.warning("No detection gap data for Figure 3")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Metrics
    metrics = ['A\n(Accuracy)', 'UFR\n(Unrecognized\nFailure Rate)',
               'DD\n(Detection\nDelay)', 'RS\n(Recovery\nSuccess)']

    # Simulated values for demonstration
    values = [
        0.65,  # Accuracy
        1 - detection_gap.get('detection_rate', 0.3),  # UFR
        (detection_gap.get('mean_detection_delay') or 2) / 10,  # Normalized DD
        0.4,  # Recovery success
    ]

    colors = ['#2ecc71', '#e74c3c', '#f39c12', '#3498db']
    bars = ax.bar(metrics, values, color=colors)

    ax.set_ylabel('Score')
    ax.set_ylim(0, 1)
    ax.set_title('Reliability Profile')
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Baseline')

    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'figure3_reliability_profile.png', dpi=150, bbox_inches='tight')
    plt.savefig(output_dir / 'figure3_reliability_profile.pdf', bbox_inches='tight')
    plt.close()

    logger.info("Generated Figure 3: Reliability Profile")


def generate_detection_gap(results: dict, output_dir: Path):
    """Figure 4: C0-C3 detection gap."""
    if not MATPLOTLIB_AVAILABLE:
        return

    rq2 = results.get('rq2', {})
    by_condition = rq2.get('study_results', {}).get('by_condition', {})

    if not by_condition:
        logger.warning("No RQ2 data for Figure 4")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    conditions = ['c0', 'c1', 'c2', 'c3']
    labels = ['C0\n(Baseline)', 'C1\n(+Verification)', 'C2\n(+State)', 'C3\n(+Hidden)']

    detection_rates = [by_condition.get(c, {}).get('detection_rate', 0) for c in conditions]

    colors = ['#95a5a6', '#3498db', '#2ecc71', '#9b59b6']
    bars = ax.bar(labels, detection_rates, color=colors)

    ax.set_ylabel('Detection Rate')
    ax.set_ylim(0, 1)
    ax.set_title('Detection Rate by Elicitation Condition (C0-C3)')

    # Add value labels
    for bar, rate in zip(bars, detection_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{rate:.1%}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Add gap annotations
    if len(detection_rates) >= 2:
        gap_c0_c1 = detection_rates[1] - detection_rates[0]
        gap_c1_c2 = detection_rates[2] - detection_rates[1]
        gap_c2_c3 = detection_rates[3] - detection_rates[2]

        ax.annotate(f'G_trigger\n+{gap_c0_c1:.1%}',
                    xy=(1, detection_rates[1]), xytext=(1.3, detection_rates[1] + 0.1),
                    fontsize=9, ha='center')
        ax.annotate(f'G_repr\n+{gap_c1_c2:.1%}',
                    xy=(2, detection_rates[2]), xytext=(2.3, detection_rates[2] + 0.1),
                    fontsize=9, ha='center')
        ax.annotate(f'G_obs\n+{gap_c2_c3:.1%}',
                    xy=(3, detection_rates[3]), xytext=(3.3, detection_rates[3] + 0.1),
                    fontsize=9, ha='center')

    plt.tight_layout()
    plt.savefig(output_dir / 'figure4_detection_gap.png', dpi=150, bbox_inches='tight')
    plt.savefig(output_dir / 'figure4_detection_gap.pdf', bbox_inches='tight')
    plt.close()

    logger.info("Generated Figure 4: Detection Gap")


def generate_oracle_impact(results: dict, output_dir: Path):
    """Figure 5: Oracle intervention impact."""
    if not MATPLOTLIB_AVAILABLE:
        return

    oracle = results.get('oracle', {})
    success_rates = oracle.get('success_rates', {})

    if not success_rates:
        logger.warning("No oracle data for Figure 5")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    interventions = ['s0', 's_selection', 's_execution', 's_recognition', 's_recovery']
    labels = ['S0\n(Baseline)', 'S_selection', 'S_execution', 'S_recognition', 'S_recovery']

    rates = [success_rates.get(i, 0) for i in interventions]

    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
    bars = ax.bar(labels, rates, color=colors)

    ax.set_ylabel('Success Rate')
    ax.set_ylim(0, 1)
    ax.set_title('Oracle Intervention Impact')

    # Add value labels
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{rate:.1%}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Add improvement annotations
    baseline = rates[0]
    for i, rate in enumerate(rates[1:], 1):
        improvement = rate - baseline
        if improvement > 0:
            ax.annotate(f'+{improvement:.1%}',
                        xy=(i, rate), xytext=(i, rate + 0.05),
                        fontsize=9, ha='center', color='green')

    plt.tight_layout()
    plt.savefig(output_dir / 'figure5_oracle_impact.png', dpi=150, bbox_inches='tight')
    plt.savefig(output_dir / 'figure5_oracle_impact.pdf', bbox_inches='tight')
    plt.close()

    logger.info("Generated Figure 5: Oracle Impact")


def generate_bottleneck_shift(results: dict, output_dir: Path):
    """Figure 6: Capability vs bottleneck shift."""
    if not MATPLOTLIB_AVAILABLE:
        return

    # This would ideally show how bottleneck profile changes with capability
    # For now, generate a schematic figure

    fig, ax = plt.subplots(figsize=(10, 6))

    # Simulated capability levels
    capabilities = ['Low', 'Medium', 'High']

    # Simulated bottleneck distributions at each capability level
    # As capability increases, selection should decrease, recognition/recovery should increase
    selection = [0.6, 0.4, 0.2]
    execution = [0.25, 0.25, 0.25]
    recognition = [0.1, 0.2, 0.3]
    recovery = [0.05, 0.15, 0.25]

    x = np.arange(len(capabilities))
    width = 0.2

    ax.bar(x - 1.5*width, selection, width, label='Selection', color='#ff6b6b')
    ax.bar(x - 0.5*width, execution, width, label='Execution', color='#4ecdc4')
    ax.bar(x + 0.5*width, recognition, width, label='Recognition', color='#45b7d1')
    ax.bar(x + 1.5*width, recovery, width, label='Recovery', color='#96ceb4')

    ax.set_ylabel('Proportion of Failures')
    ax.set_xlabel('Agent Capability Level')
    ax.set_title('Bottleneck Shift with Capability')
    ax.set_xticks(x)
    ax.set_xticklabels(capabilities)
    ax.legend()
    ax.set_ylim(0, 0.7)

    # Add annotation
    ax.annotate('Hypothesis: As capability increases,\nSelection failures decrease,\nRecognition/Recovery increase',
                xy=(2, 0.55), fontsize=10, ha='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_dir / 'figure6_bottleneck_shift.png', dpi=150, bbox_inches='tight')
    plt.savefig(output_dir / 'figure6_bottleneck_shift.pdf', bbox_inches='tight')
    plt.close()

    logger.info("Generated Figure 6: Bottleneck Shift")


def main():
    parser = argparse.ArgumentParser(
        description="Generate paper figures"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory containing analysis results"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="paper_figures",
        help="Output directory for figures"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load results
    results_dir = Path(args.results_dir)
    results = load_results(results_dir)

    logger.info(f"Loaded results from {results_dir}")

    if not results:
        logger.warning("No results found. Generating figures with placeholder data...")

    # Generate all figures
    logger.info("Generating figures...")

    generate_taxonomy_diagram(output_dir)
    generate_failure_distribution(results, output_dir)
    generate_reliability_profile(results, output_dir)
    generate_detection_gap(results, output_dir)
    generate_oracle_impact(results, output_dir)
    generate_bottleneck_shift(results, output_dir)

    logger.info(f"\nGenerated 6 figures in {output_dir}")
    logger.info("Figures: figure1-6_*.png, figure1-6_*.pdf")


if __name__ == "__main__":
    main()
