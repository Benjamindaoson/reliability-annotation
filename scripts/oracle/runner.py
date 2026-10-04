#!/usr/bin/env python3
"""
Oracle Intervention Experiment Runner

Simulates oracle interventions on annotated failure cases.

Usage:
    python scripts/oracle/runner.py --input <cases.json> --intervention selection
"""

import json
import argparse
from pathlib import Path


INTERVENTIONS = {
    'selection': {
        'name': 'Oracle Selection',
        'description': 'Replace wrong action with correct action',
        'requires': ['environment', 'action_database']
    },
    'execution': {
        'name': 'Oracle Execution',
        'description': 'Force intended execution',
        'requires': ['environment']
    },
    'recognition': {
        'name': 'Oracle Recognition',
        'description': 'Tell agent about failure (no recovery hint)',
        'requires': ['model_api']
    },
    'recovery': {
        'name': 'Oracle Recovery',
        'description': 'Provide recovery action',
        'requires': ['environment', 'action_database']
    }
}


def load_cases(cases_file: str) -> list:
    with open(cases_file, 'r') as f:
        return json.load(f)


def run_oracle(cases: list, intervention: str, env_available: bool = False, api_key: str = None) -> dict:
    """Run oracle intervention experiment."""

    config = INTERVENTIONS.get(intervention, {})

    # Check requirements
    can_run = True
    blockers = []

    if 'environment' in config.get('requires', []):
        if not env_available:
            can_run = False
            blockers.append('OSWorld environment required for trajectory rerunning')

    if 'model_api' in config.get('requires', []):
        if not api_key:
            can_run = False
            blockers.append('Model API key required')

    if not can_run:
        return {
            'intervention': intervention,
            'status': 'BLOCKED',
            'blockers': blockers,
            'n_cases': len(cases),
            'results': []
        }

    # Placeholder results
    results = []
    for case in cases:
        results.append({
            'trajectory_id': case.get('trajectory_id'),
            'intervention': intervention,
            'success': None,  # Would be measured after rerun
            'status': 'PENDING_RERUN'
        })

    return {
        'intervention': intervention,
        'status': 'READY',
        'n_cases': len(cases),
        'results': results
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Cases JSON file')
    parser.add_argument('--intervention', required=True,
                       choices=['selection', 'execution', 'recognition', 'recovery'])
    parser.add_argument('--output', default='results/oracle_results.json')
    args = parser.parse_args()

    cases = load_cases(args.input)
    results = run_oracle(cases, args.intervention)

    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    if results['status'] == 'BLOCKED':
        print("Oracle experiment BLOCKED:")
        for b in results['blockers']:
            print(f"  - {b}")
    else:
        print(f"Oracle {args.intervention}: Ready for {results['n_cases']} cases")


if __name__ == "__main__":
    main()
