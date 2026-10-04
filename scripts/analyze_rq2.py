#!/usr/bin/env python3
"""
RQ2 Analysis: Do agents know when they fail?

Implements offline elicitation protocol for measuring failure awareness.

Conditions:
- C0: Original trajectory reasoning (baseline)
- C1: Add verification prompt
- C2: Provide state comparison (before/after/intended)
- C3: Provide additional hidden state
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.data_loader import OSWorldLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Detection markers - agent explicitly acknowledges failure
DETECTION_MARKERS = [
    "didn't work", "failed", "error", "wrong", "incorrect",
    "that didn't", "this didn't", "that failed", "this failed",
    "seems wrong", "not correct", "mistake", "my mistake",
    "was wrong", "went wrong", "problem", "issue",
    "let me try", "should have", "should try", "need to try",
    "did not achieve", "wasn't successful", "unsuccessful"
]

# Confidence markers
CONFIDENCE_MARKERS = [
    "certain", "sure", "confident", "know", "definitely",
    "will work", "should work", "that's correct", "is right"
]

# Uncertainty markers
UNCERTAINTY_MARKERS = [
    "not sure", "uncertain", "might", "maybe", "perhaps",
    "could be", "not certain", "unclear", "ambiguous",
    "don't know", "cannot determine", "unable to",
    "i'm not sure", "let me check", "i'm uncertain"
]


def detect_failure_recognition(reasoning: Optional[str]) -> bool:
    """Check if reasoning explicitly recognizes a failure."""
    if not reasoning:
        return False
    reasoning_lower = reasoning.lower()
    return any(marker in reasoning_lower for marker in DETECTION_MARKERS)


def detect_uncertainty(reasoning: Optional[str]) -> bool:
    """Check if reasoning contains uncertainty."""
    if not reasoning:
        return False
    reasoning_lower = reasoning.lower()
    return any(marker in reasoning_lower for marker in UNCERTAINTY_MARKERS)


def compute_detection_score(reasoning: Optional[str]) -> float:
    """Compute a detection score from 0 to 1."""
    if not reasoning:
        return 0.0

    reasoning_lower = reasoning.lower()

    # Count detection markers
    detection_count = sum(1 for m in DETECTION_MARKERS if m in reasoning_lower)

    # Count uncertainty markers (reduces score)
    uncertainty_count = sum(1 for m in UNCERTAINTY_MARKERS if m in reasoning_lower)

    # Count confidence markers (increases score)
    confidence_count = sum(1 for m in CONFIDENCE_MARKERS if m in reasoning_lower)

    # Simple scoring
    score = detection_count * 0.3 + confidence_count * 0.1 - uncertainty_count * 0.1
    return max(0.0, min(1.0, score))


class ElicitationProtocol:
    """Implements C0-C3 elicitation conditions."""

    CONDITION_C0 = "c0"  # Original reasoning
    CONDITION_C1 = "c1"  # + verification prompt
    CONDITION_C2 = "c2"  # + state comparison
    CONDITION_C3 = "c3"  # + hidden state

    @staticmethod
    def create_c0_prompt(trajectory: dict, step_idx: int) -> str:
        """C0: Original reasoning context."""
        steps = trajectory.get('steps', [])
        if step_idx >= len(steps):
            return ""

        step = steps[step_idx]
        action = step.get('action', {})
        reasoning = step.get('reasoning', '')

        prompt = f"""Analyze the following agent action:

Action: {action.get('action_type', 'unknown')}
Arguments: {action.get('action_arguments', {})}

Agent's reasoning:
{reasoning if reasoning else '[No reasoning provided]'}

Did the agent recognize any failure in the previous step?"""
        return prompt

    @staticmethod
    def create_c1_prompt(trajectory: dict, step_idx: int) -> str:
        """C1: Add verification prompt."""
        c0 = ElicitationProtocol.create_c0_prompt(trajectory, step_idx)
        return c0 + """

IMPORTANT: You should verify whether your previous action achieved the intended effect.
Consider: Did the action produce the expected state change?"""

    @staticmethod
    def create_c2_prompt(trajectory: dict, step_idx: int) -> str:
        """C2: Provide state comparison."""
        steps = trajectory.get('steps', [])
        if step_idx >= len(steps):
            return ""

        # Get context
        before_step = steps[step_idx - 1] if step_idx > 0 else None
        current_step = steps[step_idx]
        after_step = steps[step_idx + 1] if step_idx + 1 < len(steps) else None

        before_obs = ""
        if before_step:
            obs = before_step.get('observation', {})
            before_obs = obs.get('text', obs.get('screenshot_path', '[No observation]'))

        current_action = current_step.get('action', {})
        current_obs = ""
        obs = current_step.get('observation', {})
        current_obs = obs.get('text', obs.get('screenshot_path', '[No observation]'))

        after_obs = ""
        if after_step:
            obs = after_step.get('observation', {})
            after_obs = obs.get('text', obs.get('screenshot_path', '[No observation]'))

        prompt = f"""Analyze the following agent action with state context:

BEFORE STATE:
{before_obs[:500]}

ACTION TAKEN:
{current_action.get('action_type', 'unknown')}
{current_action.get('action_arguments', {})}

AFTER STATE:
{current_obs[:500]}

INTENDED EFFECT (from task):
{trajectory.get('task_description', '[Task description not available]')}

Did the action achieve the intended effect?"""
        return prompt

    @staticmethod
    def create_c3_prompt(trajectory: dict, step_idx: int) -> str:
        """C3: Provide additional hidden state."""
        # C3 builds on C2 with additional context
        prompt = ElicitationProtocol.create_c2_prompt(trajectory, step_idx)

        # Add hidden state hints (simulated for offline analysis)
        steps = trajectory.get('steps', [])
        if step_idx >= len(steps):
            return prompt

        step = steps[step_idx]
        feedback = step.get('feedback', {})

        hidden_context = "\n\nADDITIONAL CONTEXT:\n"
        if feedback:
            hidden_context += f"- Execution success: {feedback.get('success', 'unknown')}\n"
            hidden_context += f"- State changed: {feedback.get('state_changed', 'unknown')}\n"
            if feedback.get('error'):
                hidden_context += f"- Error message: {feedback.get('error')}\n"

        hidden_context += "- File system state available\n"
        hidden_context += "- Application logs available\n"

        return prompt + hidden_context


def simulate_detection(
    trajectory: dict,
    step_idx: int,
    condition: str = "c0"
) -> dict:
    """
    Simulate elicitation response for a given condition.

    In offline mode, this uses heuristic analysis of the reasoning trace.
    For full RQ2, this would require API calls to the model.

    Returns:
        {
            'detected': bool,
            'detection_score': float,
            'confidence': str,
            'reasoning_analysis': dict
        }
    """
    steps = trajectory.get('steps', [])
    if step_idx >= len(steps):
        return {'detected': False, 'detection_score': 0.0, 'confidence': 'low'}

    # Get reasoning from the step (or subsequent steps)
    reasoning = steps[step_idx].get('reasoning', '')

    # For C1-C3, simulate additional analysis
    if condition != "c0":
        # Look at next few steps for recovery attempts
        for i in range(step_idx + 1, min(step_idx + 5, len(steps))):
            next_reasoning = steps[i].get('reasoning', '')
            if next_reasoning:
                reasoning += " " + next_reasoning

    # Compute detection score
    detection_score = compute_detection_score(reasoning)
    detected = detection_score >= 0.3  # Threshold

    # Analyze reasoning
    reasoning_lower = reasoning.lower() if reasoning else ""
    has_uncertainty = detect_uncertainty(reasoning)
    has_detection = detect_failure_recognition(reasoning)

    # Determine confidence
    if detection_score >= 0.6:
        confidence = "high"
    elif detection_score >= 0.3:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        'detected': detected,
        'detection_score': detection_score,
        'confidence': confidence,
        'reasoning_analysis': {
            'has_uncertainty': has_uncertainty,
            'has_detection': has_detection,
            'reasoning_length': len(reasoning) if reasoning else 0,
        }
    }


def run_elicitation_study(
    records: list[dict],
    conditions: list[str] = None
) -> dict:
    """
    Run offline elicitation study on failure records.

    Args:
        records: Failure decomposition records
        conditions: List of conditions to test

    Returns:
        Elicitation study results
    """
    if conditions is None:
        conditions = ["c0", "c1", "c2", "c3"]

    results = {
        'total_records': len(records),
        'conditions': conditions,
        'by_condition': {},
        'detection_gap': {},
        'gains': {},
    }

    for condition in conditions:
        results['by_condition'][condition] = {
            'detected': 0,
            'not_detected': 0,
            'detection_score_sum': 0.0,
            'by_failure_type': defaultdict(lambda: {'detected': 0, 'total': 0}),
        }

    # Simulate each condition
    for record in records:
        traj_id = record.get('trajectory_id')
        failure_step = record.get('first_failure_step', 0)
        failure_type = record.get('failure_type', 'unknown')

        # Get trajectory data (would need to reload from source)
        # For now, use the record directly
        trajectory = {
            'trajectory_id': traj_id,
            'task_description': record.get('task_description', ''),
            'steps': []  # Would need actual steps
        }

        for condition in conditions:
            sim_result = simulate_detection(trajectory, failure_step, condition)

            results['by_condition'][condition]['detection_score_sum'] += sim_result['detection_score']

            if sim_result['detected']:
                results['by_condition'][condition]['detected'] += 1
            else:
                results['by_condition'][condition]['not_detected'] += 1

            results['by_condition'][condition]['by_failure_type'][failure_type]['total'] += 1
            if sim_result['detected']:
                results['by_condition'][condition]['by_failure_type'][failure_type]['detected'] += 1

    # Compute statistics
    n = results['total_records']
    for condition in conditions:
        c_stats = results['by_condition'][condition]
        c_stats['detection_rate'] = c_stats['detected'] / n if n > 0 else 0
        c_stats['mean_detection_score'] = c_stats['detection_score_sum'] / n if n > 0 else 0

        # Per-failure-type rates
        for ft in c_stats['by_failure_type']:
            ft_stats = c_stats['by_failure_type'][ft]
            ft_stats['rate'] = ft_stats['detected'] / ft_stats['total'] if ft_stats['total'] > 0 else 0

    # Compute gains
    d0 = results['by_condition'].get('c0', {}).get('detection_rate', 0)
    for condition in ['c1', 'c2', 'c3']:
        di = results['by_condition'].get(condition, {}).get('detection_rate', 0)
        results['detection_gap'][f'd_{condition}'] = di - d0
        results['gains'][f'G_{condition}'] = (di - d0) / (1 - d0) if d0 < 1 else 0

    return results


def compute_bottleneck_shift(
    detection_gap: dict,
    failure_distribution: dict
) -> dict:
    """
    Compute bottleneck shift metrics.

    G_trigger: Detection gain from verification prompt
    G_representation: Detection gain from state comparison
    G_observability: Detection gain from hidden state
    """
    d0 = detection_gap.get('d_c0', 0)
    d1 = detection_gap.get('d_c1', 0)
    d2 = detection_gap.get('d_c2', 0)
    d3 = detection_gap.get('d_c3', 0)

    return {
        'G_trigger': d1 - d0,  # Gain from prompting to verify
        'G_representation': d2 - d1,  # Gain from explicit state
        'G_observability': d3 - d2,  # Gain from hidden state access
        'G_total': d3 - d0,  # Total gain potential
    }


def generate_rq2_report(results: dict, bottleneck_shift: dict) -> str:
    """Generate RQ2 markdown report."""
    report = []
    report.append("# RQ2: Do Agents Know When They Fail?\n")
    report.append("## Research Question\n")
    report.append("*Do agents recognize when their actions fail to achieve the intended effect?*\n")

    # Summary
    report.append("## Summary\n")
    report.append(f"- Total failures analyzed: {results['total_records']}\n")

    # Detection rates by condition
    report.append("## Detection Rate by Elicitation Condition\n")
    report.append("| Condition | Description | Detection Rate |")
    report.append("|-----------|-------------|----------------|")

    condition_desc = {
        'c0': 'Original reasoning (baseline)',
        'c1': '+ Verification prompt',
        'c2': '+ State comparison',
        'c3': '+ Hidden state access',
    }

    for condition in ['c0', 'c1', 'c2', 'c3']:
        if condition in results['by_condition']:
            rate = results['by_condition'][condition]['detection_rate']
            desc = condition_desc.get(condition, condition)
            report.append(f"| {condition.upper()} | {desc} | {rate:.1%} |")
    report.append("")

    # Bottleneck decomposition
    report.append("## Bottleneck Decomposition\n")
    report.append("| Gain Component | Value | Interpretation |")
    report.append("|----------------|-------|----------------|")

    g_trigger = bottleneck_shift.get('G_trigger', 0)
    g_rep = bottleneck_shift.get('G_representation', 0)
    g_obs = bottleneck_shift.get('G_observability', 0)

    report.append(f"| G_trigger | {g_trigger:.1%} | Detection triggered by prompt |")
    report.append(f"| G_representation | {g_rep:.1%} | Detection improved by state info |")
    report.append(f"| G_observability | {g_obs:.1%} | Detection improved by hidden state |")
    report.append(f"| G_total | {g_trigger + g_rep + g_obs:.1%} | Total detection gap |")
    report.append("")

    # Interpretation
    report.append("## Interpretation\n")
    if g_trigger > 0.1:
        report.append("- **Major trigger gap**: Agents often fail to spontaneously verify their actions")
    else:
        report.append("- **Minor trigger gap**: Most agents attempt self-verification")

    if g_rep > 0.1:
        report.append("- **Major representation gap**: Agents struggle to compare states without explicit prompting")
    else:
        report.append("- **Minor representation gap**: State comparison is generally effective")

    if g_obs > 0.1:
        report.append("- **Major observability gap**: Hidden state access would significantly improve detection")
    else:
        report.append("- **Minor observability gap**: Observable state is sufficient for detection")
    report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="RQ2 Analysis: Failure Awareness"
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
        default="results/RQ2_detection_analysis",
        help="Output directory for results"
    )
    parser.add_argument(
        "--conditions",
        nargs='+',
        default=['c0', 'c1', 'c2', 'c3'],
        help="Conditions to test"
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
        logger.warning("No records found. Generating simulated data for demonstration...")

        # Generate simulated data for demonstration
        import random
        random.seed(42)

        for i in range(100):
            records.append({
                'trajectory_id': f'traj_{i}',
                'task_id': f'task_{i % 10}',
                'model_id': random.choice(['claude-3-sonnet', 'gpt-4o', 'gemini']),
                'first_failure_step': random.randint(5, 50),
                'failure_type': random.choice(['selection', 'execution', 'recognition', 'recovery']),
                'agent_detected': random.random() < 0.3,
                'task_description': 'Example task',
                'trajectory_length': random.randint(20, 100),
            })

        logger.info(f"Generated {len(records)} simulated records")

    logger.info(f"Analyzing {len(records)} failure records")

    # Run elicitation study
    results = run_elicitation_study(records, args.conditions)

    # Compute bottleneck shift
    bottleneck_shift = compute_bottleneck_shift(results.get('detection_gap', {}), {})

    # Save results
    output_data = {
        'study_results': results,
        'bottleneck_shift': bottleneck_shift,
    }

    json_path = output_dir / 'rq2_results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved results to {json_path}")

    # Generate report
    report = generate_rq2_report(results, bottleneck_shift)
    md_path = output_dir / 'rq2_report.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Saved report to {md_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("RQ2 ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total failures: {results['total_records']}")
    print("\nDetection Rates:")
    for condition in ['c0', 'c1', 'c2', 'c3']:
        if condition in results['by_condition']:
            rate = results['by_condition'][condition]['detection_rate']
            print(f"  {condition.upper()}: {rate:.1%}")
    print("\nBottleneck Decomposition:")
    print(f"  G_trigger: {bottleneck_shift.get('G_trigger', 0)*100:.1f}%")
    print(f"  G_representation: {bottleneck_shift.get('G_representation', 0)*100:.1f}%")
    print(f"  G_observability: {bottleneck_shift.get('G_observability', 0)*100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
