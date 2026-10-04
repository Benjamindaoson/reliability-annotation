"""
Prepare Human Gold Calibration Set (60 trajectories)

Creates a stratified sample of 60 real OSWorld trajectories for double-blind annotation.

Stratification:
- App types: Writer, Calc, GIMP, Chrome, Thunderbird, VLC
- Trajectory lengths: short (1-7), medium (8-12), long (13+)
- Task success: success, failure

Usage:
    python scripts/prepare_human_gold_60.py
    python scripts/prepare_human_gold_60.py --output calibration/human_gold_60/
"""

import json
import argparse
import random
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.data_loader import OSWorldLoader


def load_all_trajectories(data_path: str = None) -> list[dict]:
    """Load all available trajectories."""
    if data_path is None:
        # Try to find trajectory data
        data_path = "data/raw/sample_trajectories.json"
        if not Path(data_path).exists():
            data_path = "data/external/osworld_verified/claude-4-sonnet-15steps"

    if data_path.endswith('.json'):
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif data_path.endswith('.jsonl'):
        trajectories = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    trajectories.append(json.loads(line))
        return trajectories
    else:
        # Directory of trajectories
        loader = OSWorldLoader(data_path)
        return list(loader.load(data_path))


def categorize_trajectory(traj: dict) -> dict:
    """Categorize a trajectory by app type, length, and success."""
    task_id = traj.get('task_id', '')

    # App type
    app_type = 'unknown'
    task_id_lower = task_id.lower()
    if 'writer' in task_id_lower:
        app_type = 'libreoffice_writer'
    elif 'calc' in task_id_lower:
        app_type = 'libreoffice_calc'
    elif 'gimp' in task_id_lower:
        app_type = 'gimp'
    elif 'chrome' in task_id_lower or 'browser' in task_id_lower:
        app_type = 'chrome'
    elif 'thunderbird' in task_id_lower or 'email' in task_id_lower:
        app_type = 'thunderbird'
    elif 'vlc' in task_id_lower:
        app_type = 'vlc'

    # Length
    steps = traj.get('steps', [])
    length = len(steps)

    if length <= 7:
        length_cat = 'short'
    elif length <= 12:
        length_cat = 'medium'
    else:
        length_cat = 'long'

    # Success
    result = traj.get('final_result', 'unknown')
    success = result == 'success'

    return {
        'app_type': app_type,
        'length_cat': length_cat,
        'success': success,
        'length': length
    }


def create_stratified_sample(trajectories: list[dict], target_size: int = 60) -> list[dict]:
    """
    Create a stratified sample that covers app types, lengths, and success rates.
    """
    # Categorize all trajectories
    categorized = defaultdict(list)

    for traj in trajectories:
        cat = categorize_trajectory(traj)
        key = (cat['app_type'], cat['length_cat'], cat['success'])
        categorized[key].append((traj, cat))

    # Calculate target per stratum
    n_strata = len(categorized)
    target_per_stratum = target_size // n_strata

    # Sample from each stratum
    sample = []
    remaining = target_size

    for key, items in categorized.items():
        if remaining <= 0:
            break

        # Take min of target and available
        n_take = min(target_per_stratum, len(items), remaining)

        # Random sample
        selected = random.sample(items, n_take)
        sample.extend([item[0] for item in selected])

        remaining -= n_take

    # If we need more, fill from any stratum
    all_unselected = []
    selected_ids = {t.get('trajectory_id') for t in sample}

    for traj in trajectories:
        if traj.get('trajectory_id') not in selected_ids:
            all_unselected.append(traj)

    while remaining > 0 and all_unselected:
        traj = random.choice(all_unselected)
        sample.append(traj)
        all_unselected.remove(traj)
        remaining -= 1

    return sample


def create_double_blind_assignments(trajectories: list[dict], n_annotators: int = 2) -> dict:
    """
    Create double-blind annotation assignments.

    Each trajectory is assigned to n_annotators.
    Annotators do not see each other's labels.
    """
    assignments = {}

    # Create annotator pool
    annotators = [f"A{str(i).zfill(3)}" for i in range(1, 99)]

    for traj in trajectories:
        traj_id = traj.get('trajectory_id')

        # Assign to 2 annotators
        assigned_anns = random.sample(annotators, n_annotators)

        for ann_id in assigned_anns:
            if ann_id not in assignments:
                assignments[ann_id] = []
            assignments[ann_id].append({
                'trajectory_id': traj_id,
                'status': 'pending',
                'assigned_at': None  # Will be set when annotator opens
            })

    return assignments


def prepare_calibration_set(
    data_path: str = None,
    output_dir: str = "calibration/human_gold_60",
    target_size: int = 60
) -> dict:
    """Prepare the full Human Gold calibration set."""

    print("=" * 60)
    print("Preparing Human Gold Calibration Set (60 trajectories)")
    print("=" * 60)

    # Load trajectories
    print("\nLoading trajectories...")
    trajectories = load_all_trajectories(data_path)
    print(f"Loaded {len(trajectories)} trajectories")

    if not trajectories:
        print("\n⚠️ No trajectories found!")
        print("Please ensure OSWorld trajectory data is available.")
        return {"error": "No trajectories available"}

    # Show distribution
    categorized = defaultdict(int)
    for traj in trajectories:
        cat = categorize_trajectory(traj)
        key = f"{cat['app_type']} / {cat['length_cat']} / {'success' if cat['success'] else 'failure'}"
        categorized[key] += 1

    print("\nTrajectory distribution:")
    for key, count in sorted(categorized.items()):
        print(f"  {key}: {count}")

    # Create stratified sample
    print(f"\nCreating stratified sample of {target_size} trajectories...")
    sample = create_stratified_sample(trajectories, target_size)

    # Show sample distribution
    sample_cats = defaultdict(int)
    for traj in sample:
        cat = categorize_trajectory(traj)
        key = f"{cat['app_type']} / {cat['length_cat']}"
        sample_cats[key] += 1

    print("\nSample distribution:")
    for key, count in sorted(sample_cats.items()):
        print(f"  {key}: {count}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save trajectories
    trajectories_file = output_path / "trajectories.json"
    with open(trajectories_file, 'w', encoding='utf-8') as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(sample)} trajectories to: {trajectories_file}")

    # Create double-blind assignments
    print("\nCreating double-blind assignments...")
    assignments = create_double_blind_assignments(sample, n_annotators=2)

    assignments_file = output_path / "assignments.json"
    with open(assignments_file, 'w', encoding='utf-8') as f:
        json.dump(assignments, f, ensure_ascii=False, indent=2)
    print(f"Saved assignments to: {assignments_file}")

    # Summary
    print("\n" + "=" * 60)
    print("Human Gold Calibration Set Ready")
    print("=" * 60)
    print(f"\nTrajectories: {len(sample)}")
    print(f"Annotators: {len(assignments)}")
    print(f"Output: {output_path}")

    return {
        'n_trajectories': len(sample),
        'n_annotators': len(assignments),
        'output_dir': str(output_path),
        'trajectories_file': str(trajectories_file),
        'assignments_file': str(assignments_file),
        'sample_distribution': dict(sample_cats)
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare Human Gold calibration set")
    parser.add_argument("--data_path", type=str, default=None,
                       help="Path to trajectory data")
    parser.add_argument("--output", type=str, default="calibration/human_gold_60",
                       help="Output directory")
    parser.add_argument("--size", type=int, default=60,
                       help="Target number of trajectories")
    args = parser.parse_args()

    result = prepare_calibration_set(
        data_path=args.data_path,
        output_dir=args.output,
        target_size=args.size
    )

    if "error" in result:
        print(f"\nError: {result['error']}")
    else:
        print("\n✅ Calibration set prepared successfully!")
        print("\nNext steps:")
        print("1. Review the trajectories in the output directory")
        print("2. Launch the annotation tool: streamlit run annotation_tool/app_chinese.py")
        print("3. Provide annotator IDs from the assignments file")
        print("4. Begin double-blind annotation")


if __name__ == "__main__":
    main()
