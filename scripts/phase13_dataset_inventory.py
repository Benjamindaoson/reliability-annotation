#!/usr/bin/env python3
"""
Phase 13: Dataset Inventory Generation

Creates comprehensive dataset inventory from available OSWorld trajectories.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_trajectories(data_path: str):
    """Analyze all trajectories and generate inventory."""

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    trajectories = data if isinstance(data, list) else [data]

    # Initialize counters
    stats = {
        'total_trajectories': len(trajectories),
        'models': defaultdict(int),
        'tasks': defaultdict(int),
        'results': defaultdict(int),
        'length_distribution': defaultdict(int),
        'action_types': defaultdict(int),
        'feedback_stats': {'success': 0, 'reward_nonzero': 0, 'state_changed': 0},
    }

    all_tasks = []

    for traj in trajectories:
        model_id = traj.get('model_id', 'unknown')
        task_id = traj.get('task_id', 'unknown')
        final_result = traj.get('final_result', 'unknown')
        steps = traj.get('steps', [])
        length = len(steps)

        stats['models'][model_id] += 1
        stats['tasks'][task_id] += 1
        stats['results'][final_result] += 1
        stats['length_distribution'][length] += 1

        all_tasks.append({
            'trajectory_id': traj.get('trajectory_id'),
            'task_id': task_id,
            'model_id': model_id,
            'length': length,
            'final_result': final_result,
            'has_screenshots': any(s.get('observation', {}).get('screenshot_file') for s in steps),
            'has_feedback': any(s.get('feedback') for s in steps),
        })

        for step in steps:
            action_type = step.get('action', {}).get('action_type', 'unknown')
            stats['action_types'][action_type] += 1

            fb = step.get('feedback', {})
            if fb.get('success'):
                stats['feedback_stats']['success'] += 1
            if fb.get('reward', 0) != 0:
                stats['feedback_stats']['reward_nonzero'] += 1
            if fb.get('state_changed'):
                stats['feedback_stats']['state_changed'] += 1

    return stats, all_tasks


def generate_inventory_markdown(stats: dict, tasks: list) -> str:
    """Generate markdown inventory report."""

    md = """# Dataset Inventory

## Summary

| Metric | Value |
|--------|-------|
| Total Trajectories | {total} |
| Unique Models | {models} |
| Unique Tasks | {tasks} |
| Total Steps | {steps} |
| Avg Trajectory Length | {avg_len:.1f} |

## Models

{model_table}

## Trajectory Length Distribution

{length_table}

## Action Types

{action_table}

## Feedback Statistics

| Metric | Count |
|--------|-------|
| Successful steps | {success} |
| Non-zero reward | {reward} |
| State changed | {changed} |

## Data Availability

| Data Type | Available |
|-----------|-----------|
| Reasoning traces | **NOT AVAILABLE** |
| Evaluator signals | **NOT AVAILABLE** |
| Screenshots | Available |
| Action history | Available |
| Feedback signals | Available |

## Limitations

1. **No reasoning traces**: Model reasoning is not available in this dataset
2. **No evaluator signals**: Ground-truth task completion signals are not provided
3. **Single model**: Only Claude-4-Sonnet trajectories available
4. **Synthetic annotations needed**: Failure annotations require human labeling

## Implications for Analysis

- RQ2 (Failure Awareness): **Cannot be measured directly** - requires reasoning traces
- RQ1 (Failure Distribution): **Can infer from feedback patterns**
- RQ3 (Oracle Intervention): **Requires annotated failures**
""".format(
        total=stats['total_trajectories'],
        models=len(stats['models']),
        tasks=len(set(stats['tasks'])),
        steps=sum(k * v for k, v in stats['length_distribution'].items()),
        avg_len=sum(k*v for k,v in stats['length_distribution'].items()) / stats['total_trajectories'],
        model_table='\n'.join(f"| {m} | {c} |" for m, c in sorted(stats['models'].items())),
        length_table='\n'.join(f"| {l} | {c} |" for l, c in sorted(stats['length_distribution'].items())),
        action_table='\n'.join(f"| {a} | {c} |" for a, c in sorted(stats['action_types'].items(), key=lambda x: -x[1])[:10]),
        success=stats['feedback_stats']['success'],
        reward=stats['feedback_stats']['reward_nonzero'],
        changed=stats['feedback_stats']['state_changed'],
    )

    return md


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/raw/osworld_claude4_converted.json')
    parser.add_argument('--output-dir', default='results')
    args = parser.parse_args()

    print("Analyzing trajectories...")
    stats, tasks = analyze_trajectories(args.input)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON inventory
    stats_json = {
        'total_trajectories': stats['total_trajectories'],
        'models': dict(stats['models']),
        'task_count': len(stats['tasks']),
        'results': dict(stats['results']),
        'length_distribution': {str(k): v for k, v in stats['length_distribution'].items()},
        'action_types': dict(stats['action_types']),
        'feedback_stats': stats['feedback_stats'],
    }

    with open(output_dir / 'dataset_inventory.json', 'w', encoding='utf-8') as f:
        json.dump(stats_json, f, indent=2, ensure_ascii=False)

    # Save markdown report
    md = generate_inventory_markdown(stats, tasks)
    with open(output_dir / 'dataset_inventory.md', 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"Inventory saved to {output_dir}")
    print(f"Total trajectories: {stats['total_trajectories']}")


if __name__ == "__main__":
    main()
