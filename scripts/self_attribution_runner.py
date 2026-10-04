#!/usr/bin/env python3
"""
Self-Attribution Experiment Runner

Tests whether attributing failure to self vs. other affects detection.

Usage:
    python scripts/self_attribution_runner.py --cases <cases.json> --condition self
"""

import json
import argparse
from pathlib import Path


PROMPTS = {
    'self': """This is an action YOU just performed.

Evidence:
{evidence}

Question: Did YOUR action fail?
Answer with YES or NO and provide brief justification.""",

    'other': """This is an action ANOTHER AGENT performed.

Evidence:
{evidence}

Question: Did the OTHER AGENT's action fail?
Answer with YES or NO and provide brief justification.""",

    'neutral': """This is a SYSTEM LOG showing an action outcome.

Evidence:
{evidence}

Question: Did this action succeed or fail?
Answer with YES (failed) or NO (succeeded) and provide brief justification."""
}


def load_cases(cases_file: str) -> list:
    with open(cases_file, 'r') as f:
        return json.load(f)


def run_condition(cases: list, condition: str, api_key: str = None) -> dict:
    if api_key is None:
        return {
            'condition': condition,
            'status': 'BLOCKED',
            'reason': 'API key required',
            'n_cases': len(cases)
        }

    results = []
    detected = 0

    for case in cases:
        evidence = f"Task: {case.get('task_id')}\nFailure step: {case.get('first_failure_step')}"
        prompt = PROMPTS[condition].format(evidence=evidence)

        # API call would go here
        result = {
            'trajectory_id': case.get('trajectory_id'),
            'condition': condition,
            'detected': None  # Parsed from response
        }
        results.append(result)

    detected = sum(1 for r in results if r.get('detected') == True)
    D = detected / len(results) if results else 0

    return {
        'condition': condition,
        'detection_rate': D,
        'n_detected': detected,
        'n_cases': len(cases),
        'results': results
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', required=True)
    parser.add_argument('--condition', required=True, choices=['self', 'other', 'neutral'])
    parser.add_argument('--api-key')
    parser.add_argument('--output', default='results/self_attribution_real/results.json')
    args = parser.parse_args()

    cases = load_cases(args.cases)
    results = run_condition(cases, args.condition, args.api_key)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Self-attribution {args.condition}: {results.get('detection_rate', 'BLOCKED')}")


if __name__ == "__main__":
    main()
