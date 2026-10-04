#!/usr/bin/env python3
"""
RQ2 API Experiment Runner

Runs C0-C3 elicitation experiments on human-annotated cases.

Usage:
    python scripts/rq2_api_runner.py --cases <cases.json> --condition C0 --output <results.json>
"""

import json
import argparse
from pathlib import Path


# C0-C3 prompt templates
PROMPTS = {
    'C0': """Given the following trajectory evidence, did the agent explicitly recognize that their action failed?

Evidence:
{evidence}

Question: Did the agent explicitly acknowledge the failure?
Answer with YES or NO and provide brief justification.""",

    'C1': """Given the following trajectory evidence, did the agent explicitly recognize that their action failed?

IMPORTANT: First verify whether your previous action achieved the intended effect.

Evidence:
{evidence}

Question: Did the agent explicitly acknowledge the failure?
Answer with YES or NO and provide brief justification.""",

    'C2': """Analyze the following action:

BEFORE: {before_state}
ACTION: {action_taken}
AFTER: {after_state}
INTENDED EFFECT: {intended_effect}

Question: Did the agent explicitly acknowledge the failure?
Answer with YES or NO and provide brief justification.""",

    'C3': """Analyze the following action with full state information:

BEFORE: {before_state}
ACTION: {action_taken}
AFTER: {after_state}
INTENDED EFFECT: {intended_effect}

HIDDEN STATE (available for verification):
{hidden_state}

Question: Did the agent explicitly acknowledge the failure?
Answer with YES or NO and provide brief justification."""
}


def load_cases(cases_file: str) -> list:
    """Load selected cases for RQ2."""
    with open(cases_file, 'r') as f:
        return json.load(f)


def extract_evidence(case: dict) -> dict:
    """Extract evidence from case for prompting."""
    context = case.get('context', {})

    return {
        'evidence': f"Task: {case.get('task_id')}\nFailure step: {case.get('first_failure_step')}",
        'before_state': str(context.get('before', [])),
        'action_taken': str(context.get('failure', [])),
        'after_state': str(context.get('after', [])),
        'intended_effect': '[Annotator-provided intended effect]',
        'hidden_state': '[Available hidden state: filesystem, DOM, etc.]'
    }


def run_condition(cases: list, condition: str, model_api_key: str = None) -> dict:
    """Run elicitation for a condition."""

    if model_api_key is None:
        print(f"WARNING: No API key provided. Cannot run {condition} experiment.")
        return {
            'condition': condition,
            'status': 'BLOCKED',
            'reason': 'API key required',
            'n_cases': len(cases),
            'results': []
        }

    results = []
    detected_count = 0

    for case in cases:
        evidence = extract_evidence(case)
        prompt = PROMPTS[condition].format(**evidence)

        # In real implementation, call model API here
        # response = call_model_api(prompt, api_key)

        # Placeholder result
        result = {
            'trajectory_id': case.get('trajectory_id'),
            'condition': condition,
            'prompt': prompt[:200] + '...',
            'response': '[API_RESPONSE_PLACEHOLDER]',
            'detected': None  # Would be parsed from response
        }
        results.append(result)

    # Compute detection rate
    detected_count = sum(1 for r in results if r.get('detected') == True)
    D = detected_count / len(results) if results else 0

    return {
        'condition': condition,
        'status': 'COMPLETED' if model_api_key else 'BLOCKED',
        'n_cases': len(cases),
        'n_detected': detected_count,
        'detection_rate': D,
        'results': results
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', required=True, help='Cases JSON file')
    parser.add_argument('--condition', required=True, choices=['C0', 'C1', 'C2', 'C3'])
    parser.add_argument('--api-key', help='Model API key')
    parser.add_argument('--output', default='results/RQ2_final/cascade_results.json')
    args = parser.parse_args()

    print(f"Loading cases from {args.cases}...")
    cases = load_cases(args.cases)

    print(f"Running {args.condition} experiment on {len(cases)} cases...")
    results = run_condition(cases, args.condition, args.api_key)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    if results['status'] == 'BLOCKED':
        print(f"WARNING: {results['reason']}")
        print("Set API key to run experiment:")
        print("  python scripts/rq2_api_runner.py --cases <file> --condition C0 --api-key YOUR_KEY")
    else:
        print(f"Detection rate: {results['detection_rate']:.1%}")


if __name__ == "__main__":
    main()
