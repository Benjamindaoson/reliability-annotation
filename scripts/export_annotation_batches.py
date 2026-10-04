"""
Batch Exporter for Annotation
Exports OSWorld trajectories into annotation-ready batches for LLM/Human annotation.

Usage:
    python scripts/export_annotation_batches.py --num_batches 10 --batch_size 10
    python scripts/export_annotation_batches.py --task_type chrome --batch_size 20
"""

import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
import random


# Configuration
DATA_DIR = Path("data/external/osworld_verified/claude-4-sonnet-15steps/claude-4-sonnet-20250514-15steps")
OUTPUT_DIR = Path("annotation_batches")
OUTPUT_DIR.mkdir(exist_ok=True)


@dataclass
class BatchMetadata:
    """Metadata for a batch export"""
    batch_id: str
    created_at: str
    task_types: list[str]
    num_trajectories: int
    total_steps: int


def compute_trajectory_hash(trajectory: dict) -> str:
    """
    Compute SHA256 hash of trajectory to ensure consistency across annotators.

    Hash is computed from: trajectory_id + task_description + steps JSON
    """
    content = json.dumps({
        "trajectory_id": trajectory.get("trajectory_id", ""),
        "task_description": trajectory.get("task_description", ""),
        "steps": trajectory.get("steps", [])
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def load_trajectory(traj_dir: Path) -> Optional[dict]:
    """Load a single trajectory from directory"""
    traj_file = traj_dir / "traj.jsonl"
    if not traj_file.exists():
        return None

    steps = []
    with open(traj_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                steps.append(json.loads(line))

    if not steps:
        return None

    # Determine task type from parent directory
    task_type = traj_dir.parent.name

    # Load result if available
    result_file = traj_dir / "result.txt"
    final_result = "unknown"
    if result_file.exists():
        final_result = result_file.read_text().strip().lower()
        if "success" in final_result:
            final_result = "success"
        else:
            final_result = "failure"

    # Compute hash
    trajectory = {
        "trajectory_id": f"{task_type}/{traj_dir.name}",
        "task_type": task_type,
        "task_description": f"OSWorld task in {task_type} environment",
        "steps": steps,
        "final_result": final_result,
        "total_steps": len(steps)
    }
    trajectory["trajectory_hash"] = compute_trajectory_hash(trajectory)

    return trajectory


def load_all_trajectories(task_types: Optional[list[str]] = None) -> list[dict]:
    """Load all trajectories, optionally filtered by task type"""
    trajectories = []

    if not DATA_DIR.exists():
        print(f"Error: Data directory not found: {DATA_DIR}")
        return trajectories

    for task_type_dir in DATA_DIR.iterdir():
        if not task_type_dir.is_dir():
            continue

        # Filter by task type if specified
        if task_types and task_type_dir.name not in task_types:
            continue

        for traj_dir in task_type_dir.iterdir():
            if not traj_dir.is_dir():
                continue

            trajectory = load_trajectory(traj_dir)
            if trajectory:
                trajectories.append(trajectory)

    return trajectories


def format_trajectory_for_annotation(trajectory: dict) -> dict:
    """
    Format trajectory for annotation, including causal window analysis.
    """
    steps = trajectory.get("steps", [])

    # Identify candidate failure steps (reward = 0 or early termination)
    candidate_steps = []
    for i, step in enumerate(steps):
        reward = step.get("reward", 0)
        done = step.get("done", False)
        if reward <= 0 or done:
            candidate_steps.append(i)

    # Format action information
    formatted_steps = []
    for i, step in enumerate(steps):
        action = step.get("action", {})
        if isinstance(action, str):
            # Handle string action
            action_type = "unknown"
            coords = []
            text = ""
            action_desc = action
        elif isinstance(action, dict):
            inp = action.get("input", {})
            if isinstance(inp, dict):
                action_type = inp.get("action", "unknown")
                coords = inp.get("coordinate", [])
                text = inp.get("text", "")
            else:
                action_type = inp if isinstance(inp, str) else "unknown"
                coords = []
                text = ""
            action_desc = action_type
            if coords:
                action_desc += f" at {coords}"
            if text:
                action_desc += f": '{text[:50]}...'" if len(text) > 50 else f": '{text}'"
        else:
            action_type = "unknown"
            coords = []
            text = ""
            action_desc = "unknown"

        formatted_steps.append({
            "step_num": i + 1,
            "screenshot_file": step.get("screenshot_file", ""),
            "action": action_desc,
            "action_type": action_type if isinstance(action_type, str) else "unknown",
            "coordinates": coords if isinstance(coords, list) else [],
            "reward": step.get("reward", 0),
            "done": step.get("done", False),
            "is_candidate_failure": i in candidate_steps
        })

    return {
        "trajectory_id": trajectory["trajectory_id"],
        "trajectory_hash": trajectory["trajectory_hash"],
        "task_type": trajectory["task_type"],
        "task_description": trajectory["task_description"],
        "final_result": trajectory["final_result"],
        "total_steps": trajectory["total_steps"],
        "candidate_failure_steps": candidate_steps,
        "steps": formatted_steps
    }


def export_batch(trajectories: list[dict], batch_id: str) -> Path:
    """Export a batch of trajectories to JSON file"""
    batch_data = {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(),
        "num_trajectories": len(trajectories),
        "total_steps": sum(t["total_steps"] for t in trajectories),
        "task_types": list(set(t["task_type"] for t in trajectories)),
        "trajectories": [format_trajectory_for_annotation(t) for t in trajectories]
    }

    output_file = OUTPUT_DIR / f"batch_{batch_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)

    return output_file


def main():
    parser = argparse.ArgumentParser(description="Export trajectory batches for annotation")
    parser.add_argument("--num_batches", type=int, default=10,
                        help="Number of batches to create")
    parser.add_argument("--batch_size", type=int, default=10,
                        help="Number of trajectories per batch")
    parser.add_argument("--task_type", type=str, nargs="+", default=None,
                        help="Filter by task type(s)")
    parser.add_argument("--output_dir", type=str, default="annotation_batches",
                        help="Output directory")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    parser.add_argument("--max_trajectories", type=int, default=None,
                        help="Maximum number of trajectories to export")

    args = parser.parse_args()

    global OUTPUT_DIR
    OUTPUT_DIR = Path(args.output_dir)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Set random seed
    random.seed(args.seed)

    # Load trajectories
    print(f"Loading trajectories from {DATA_DIR}...")
    trajectories = load_all_trajectories(args.task_type)
    print(f"Found {len(trajectories)} trajectories")

    if not trajectories:
        print("No trajectories found!")
        return

    # Limit if specified
    if args.max_trajectories:
        trajectories = trajectories[:args.max_trajectories]
        print(f"Limited to {args.max_trajectories} trajectories")

    # Shuffle for variety
    random.shuffle(trajectories)

    # Calculate batches
    total_batches = min(args.num_batches, (len(trajectories) + args.batch_size - 1) // args.batch_size)
    print(f"Exporting {len(trajectories)} trajectories in {total_batches} batches of ~{args.batch_size}")

    # Export batches
    for i in range(total_batches):
        start_idx = i * args.batch_size
        end_idx = min(start_idx + args.batch_size, len(trajectories))
        batch_trajectories = trajectories[start_idx:end_idx]

        batch_id = f"{i+1:03d}"
        output_file = export_batch(batch_trajectories, batch_id)

        print(f"  Batch {batch_id}: {len(batch_trajectories)} trajectories -> {output_file}")

    # Generate summary
    summary = {
        "exported_at": datetime.now().isoformat(),
        "data_dir": str(DATA_DIR),
        "output_dir": str(OUTPUT_DIR),
        "task_types": list(set(t["task_type"] for t in trajectories)),
        "total_trajectories": len(trajectories),
        "total_batches": total_batches,
        "batch_size": args.batch_size,
        "random_seed": args.seed
    }

    summary_file = OUTPUT_DIR / "export_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nExport complete! Summary saved to {summary_file}")


if __name__ == "__main__":
    main()
