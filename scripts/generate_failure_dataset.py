#!/usr/bin/env python3
"""
Failure Decomposition Dataset Generator.

Creates the structured dataset for RQ1 analysis from human annotations.

Schema:
{
    trajectory_id: str,
    task_id: str,
    model_id: str,
    first_failure_step: int,
    failure_type: str,  # selection|execution|recognition|recovery
    before_state: str,
    action: str,
    after_state: str,
    agent_detected: bool,
    detection_step: int | null,
    detection_delay: int | null,
    recovered: bool
}
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.data_loader import OSWorldLoader
from src.trajectory_analyzer.trajectory.normalizer import normalize_trajectory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Uncertainty markers for agent self-awareness detection
UNCERTAINTY_MARKERS = [
    "not sure", "uncertain", "might", "maybe", "perhaps",
    "could be", "not certain", "unclear", "ambiguous",
    "don't know", "cannot determine", "unable to",
    "i'm not sure", "let me check", "i'm not certain",
    "need to verify", "need to check", "should verify",
    "let me verify", "i'm uncertain"
]

# Detection markers - agent explicitly acknowledges failure
DETECTION_MARKERS = [
    "didn't work", "failed", "error", "wrong", "incorrect",
    "that didn't", "this didn't", "that failed", "this failed",
    "seems wrong", "not correct", "mistake", "my mistake",
    "was wrong", "went wrong", "problem", "issue",
    "let me try", "should have", "should try", "need to try"
]


def detect_agent_uncertainty(reasoning: Optional[str]) -> bool:
    """Check if reasoning contains uncertainty markers."""
    if not reasoning:
        return False
    reasoning_lower = reasoning.lower()
    return any(marker in reasoning_lower for marker in UNCERTAINTY_MARKERS)


def detect_agent_failure_recognition(
    reasoning: Optional[str],
    after_reasoning: Optional[str] = None
) -> bool:
    """Check if agent explicitly recognizes a failure."""
    if not reasoning:
        return False

    # Check current step
    reasoning_lower = reasoning.lower()
    has_detection = any(marker in reasoning_lower for marker in DETECTION_MARKERS)

    # Check next step's reasoning if available
    if not has_detection and after_reasoning:
        after_lower = after_reasoning.lower()
        has_detection = any(marker in after_lower for marker in DETECTION_MARKERS)

    return has_detection


def extract_step_context(
    trajectory: dict,
    step_idx: int,
    context_before: int = 1,
    context_after: int = 1
) -> dict:
    """Extract context around a failure step."""
    steps = trajectory.get('steps', [])

    before_idx = max(0, step_idx - context_before)
    after_idx = min(len(steps), step_idx + context_after + 1)

    before_step = steps[before_idx] if before_idx < len(steps) else None
    current_step = steps[step_idx] if step_idx < len(steps) else None
    after_step = steps[step_idx + 1] if step_idx + 1 < len(steps) else None

    return {
        'before': before_step,
        'current': current_step,
        'after': after_step,
    }


def format_action_summary(step: dict) -> str:
    """Create a human-readable action summary."""
    action = step.get('action', {})
    action_type = action.get('action_type', 'unknown')
    args = action.get('action_arguments', {})

    if not args:
        return action_type

    arg_parts = []
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 50:
            value = value[:47] + "..."
        arg_parts.append(f"{key}={value}")

    return f"{action_type}({', '.join(arg_parts[:3])})"


def process_trajectory(
    trajectory: dict,
    annotation: dict
) -> dict:
    """
    Process a single trajectory with annotation into failure decomposition record.

    Args:
        trajectory: Raw trajectory dictionary
        annotation: Human annotation for this trajectory

    Returns:
        Failure decomposition record
    """
    failure_step = annotation.get('first_failure_step', 0)
    if failure_step is None or failure_step < 0:
        return None  # Skip trajectories without valid failure step

    # Handle empty failure_type list
    failure_types = annotation.get('failure_type', [])
    failure_type = failure_types[0] if failure_types else 'unknown'
    traj_id = trajectory.get('trajectory_id', 'unknown')

    # Get steps for context
    steps = trajectory.get('steps', [])
    if failure_step >= len(steps):
        return None  # Skip if failure_step is out of range

    # Extract context
    context = extract_step_context(trajectory, failure_step)

    # Get reasoning traces for detection analysis
    current_reasoning = None
    after_reasoning = None

    if failure_step < len(steps):
        current_reasoning = steps[failure_step].get('reasoning')

    if failure_step + 1 < len(steps):
        after_reasoning = steps[failure_step + 1].get('reasoning')

    # Detect agent awareness
    agent_detected = detect_agent_failure_recognition(current_reasoning, after_reasoning)

    # Find detection step (if agent detected)
    detection_step = None
    detection_delay = None

    if agent_detected:
        detection_step = failure_step  # Detection happens at or after failure

        # Look for explicit detection in subsequent steps
        for i in range(failure_step + 1, min(failure_step + 5, len(steps))):
            step_reasoning = steps[i].get('reasoning', '')
            if detect_agent_failure_recognition(step_reasoning):
                detection_step = i
                detection_delay = i - failure_step
                break

    # Determine if recovered
    # Check if trajectory continues successfully after failure
    recovered = False
    if failure_step + 2 < len(steps):
        # Check feedback in subsequent steps
        for i in range(failure_step + 1, min(failure_step + 5, len(steps))):
            feedback = steps[i].get('feedback', {})
            if feedback.get('success', False):
                recovered = True
                break

    # Format states
    before_state = ""
    if context['before']:
        obs = context['before'].get('observation', {})
        before_state = obs.get('text', obs.get('screenshot_path', ''))[:200]

    current_action = ""
    if context['current']:
        current_action = format_action_summary(context['current'])

    after_state = ""
    if context['after']:
        obs = context['after'].get('observation', {})
        after_state = obs.get('text', obs.get('screenshot_path', ''))[:200]

    return {
        'trajectory_id': traj_id,
        'task_id': trajectory.get('task_id', 'unknown'),
        'model_id': trajectory.get('model_id', 'unknown'),
        'first_failure_step': failure_step,
        'failure_type': failure_type,
        'before_state': before_state,
        'action': current_action,
        'after_state': after_state,
        'agent_detected': agent_detected,
        'detection_step': detection_step,
        'detection_delay': detection_delay,
        'recovered': recovered,
        # Additional metadata
        'task_description': trajectory.get('task_description', ''),
        'trajectory_length': len(steps),
        'final_result': trajectory.get('final_result', 'unknown'),
        'annotator_notes': annotation.get('annotator_notes', ''),
    }


def load_annotations(path: str) -> dict[str, dict]:
    """Load annotations into lookup by trajectory_id."""
    annotations = {}
    annotation_file = Path(path)

    if not annotation_file.exists():
        logger.warning(f"Annotations file not found: {path}")
        return annotations

    if annotation_file.suffix == '.jsonl':
        with open(annotation_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    ann = json.loads(line)
                    traj_id = ann.get('trajectory_id')
                    if traj_id:
                        annotations[traj_id] = ann
    else:
        with open(annotation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for ann in data:
                    traj_id = ann.get('trajectory_id')
                    if traj_id:
                        annotations[traj_id] = ann
            elif isinstance(data, dict) and 'annotations' in data:
                for ann in data['annotations']:
                    traj_id = ann.get('trajectory_id')
                    if traj_id:
                        annotations[traj_id] = ann

    return annotations


def generate_failure_decomposition_dataset(
    trajectories_path: str,
    annotations_path: str,
    output_path: str
) -> str:
    """
    Generate the failure decomposition dataset.

    Args:
        trajectories_path: Path to trajectory data
        annotations_path: Path to human annotations
        output_path: Output path for the dataset

    Returns:
        Path to generated dataset
    """
    logger.info("Loading trajectories...")
    loader = OSWorldLoader(trajectories_path)
    trajectories = list(loader.load(trajectories_path))

    logger.info(f"Loaded {len(trajectories)} trajectories")

    logger.info("Loading annotations...")
    annotations = load_annotations(annotations_path)
    logger.info(f"Loaded {len(annotations)} annotations")

    # Process trajectories with annotations
    records = []
    unmatched = []

    for trajectory in trajectories:
        traj_id = trajectory.get('trajectory_id')
        if traj_id in annotations:
            record = process_trajectory(trajectory, annotations[traj_id])
            if record is not None:  # Skip invalid records
                records.append(record)
        else:
            unmatched.append(traj_id)

    if unmatched:
        logger.warning(f"{len(unmatched)} trajectories have no annotation")

    # Save dataset
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    logger.info(f"Generated {len(records)} records in {output_path}")

    # Also save as JSON for easier inspection
    json_path = output_file.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    logger.info(f"Also saved JSON version to {json_path}")

    return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description="Generate failure decomposition dataset from annotations"
    )
    parser.add_argument(
        "--trajectories",
        type=str,
        default="data/raw/sample_trajectories.json",
        help="Path to trajectory data"
    )
    parser.add_argument(
        "--annotations",
        type=str,
        default="data/annotations/annotations.jsonl",
        help="Path to human annotations"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/failure_decomposition.jsonl",
        help="Output path for dataset"
    )

    args = parser.parse_args()

    generate_failure_decomposition_dataset(
        args.trajectories,
        args.annotations,
        args.output
    )


if __name__ == "__main__":
    main()
