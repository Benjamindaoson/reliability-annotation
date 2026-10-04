#!/usr/bin/env python3
"""
OSWorld Trajectory Format Converter.

Converts OSWorld JSONL trajectories to the unified schema format.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterator

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def convert_osworld_trajectory(
    trajectory_dir: Path,
    trajectory_id: str = None
) -> dict:
    """
    Convert OSWorld JSONL trajectory to unified format.

    Args:
        trajectory_dir: Directory containing traj.jsonl and screenshots
        trajectory_id: Optional trajectory ID (defaults to directory name)

    Returns:
        Unified trajectory dictionary
    """
    traj_file = trajectory_dir / "traj.jsonl"
    result_file = trajectory_dir / "result.txt"

    if not traj_file.exists():
        raise FileNotFoundError(f"traj.jsonl not found in {trajectory_dir}")

    # Read all steps
    steps = []
    for line in traj_file.read_text().strip().split('\n'):
        if line.strip():
            step = json.loads(line)
            steps.append(step)

    # Read result if available
    final_result = "unknown"
    if result_file.exists():
        result_text = result_file.read_text().strip().lower()
        if "success" in result_text:
            final_result = "success"
        elif "failure" in result_text or "fail" in result_text:
            final_result = "failure"

    # Infer task_id from directory path
    # Format: category/instance_id/
    parts = trajectory_dir.parts
    if len(parts) >= 2:
        task_id = f"osworld_{parts[-2]}_{parts[-1]}"
    else:
        task_id = parts[-1] if parts else "unknown"

    # Extract model_id from path
    model_id = "unknown"
    path_str = str(trajectory_dir)
    if "claude" in path_str.lower():
        model_id = "claude-4-sonnet-20250514"
    elif "gpt" in path_str.lower():
        model_id = "gpt-4o"
    elif "o3" in path_str.lower():
        model_id = "o3"

    # Convert steps to unified format
    unified_steps = []
    for step in steps:
        action = step.get('action', {})
        action_input = action.get('input', {})

        # Build action_arguments
        action_arguments = {}
        if isinstance(action_input, dict):
            if 'coordinate' in action_input:
                action_arguments['coordinate'] = action_input['coordinate']
            if 'text' in action_input:
                action_arguments['text'] = action_input['text']
            if 'command' in action_input:
                action_arguments['command'] = action_input['command']
        else:
            # action_input might be a string
            action_arguments['raw'] = str(action_input)

        # Check for reasoning (if available in info)
        info = step.get('info', {})
        reasoning = info.get('reasoning', '')

        # Feedback from reward and done
        reward = step.get('reward', 0)
        done = step.get('done', False)

        unified_step = {
            'step_id': step.get('step_num', 0) - 1,  # 0-indexed
            'action': {
                'action_type': action_input.get('action', 'unknown'),
                'action_arguments': action_arguments,
            },
            'reasoning': reasoning,
            'observation': {
                'screenshot_file': step.get('screenshot_file', ''),
            },
            'feedback': {
                'success': reward > 0 or done,
                'reward': reward,
                'state_changed': reward != 0,
            },
            'evaluator_signal': {
                'result': 'success' if done and reward > 0 else 'failure',
                'reward': reward,
            } if done else None,
        }
        unified_steps.append(unified_step)

    # Build unified trajectory
    trajectory = {
        'trajectory_id': trajectory_id or trajectory_dir.name,
        'task_id': task_id,
        'model_id': model_id,
        'task_description': '',  # Would need metadata file
        'final_result': final_result,
        'steps': unified_steps,
    }

    return trajectory


def convert_osworld_dataset(
    data_dir: Path,
    output_file: Path = None,
    max_trajectories: int = None
) -> Iterator[dict]:
    """
    Convert all OSWorld trajectories in a directory.

    Args:
        data_dir: Directory containing extracted OSWorld data
        output_file: Optional output file for converted data
        max_trajectories: Maximum number to convert

    Yields:
        Converted trajectory dictionaries
    """
    converted = 0

    # Find all traj.jsonl files
    for traj_file in data_dir.rglob("traj.jsonl"):
        if max_trajectories and converted >= max_trajectories:
            break

        trajectory_dir = traj_file.parent

        try:
            trajectory = convert_osworld_trajectory(trajectory_dir)
            yield trajectory
            converted += 1

            if converted % 100 == 0:
                logger.info(f"Converted {converted} trajectories...")

        except Exception as e:
            logger.warning(f"Failed to convert {trajectory_dir}: {e}")
            continue

    logger.info(f"Total converted: {converted} trajectories")


def main():
    parser = argparse.ArgumentParser(
        description="Convert OSWorld trajectories to unified format"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Input directory containing OSWorld data"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file for converted trajectories"
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=100,
        help="Maximum number of trajectories to convert"
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return

    logger.info(f"Converting trajectories from {input_dir}")

    trajectories = []
    for trajectory in convert_osworld_dataset(input_dir, max_trajectories=args.limit):
        trajectories.append(trajectory)

    logger.info(f"Converted {len(trajectories)} trajectories")

    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(trajectories, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved to {output_file}")
    else:
        # Print first trajectory as sample
        if trajectories:
            print("\nSample converted trajectory:")
            print(json.dumps(trajectories[0], indent=2, ensure_ascii=False)[:2000])


if __name__ == "__main__":
    main()
