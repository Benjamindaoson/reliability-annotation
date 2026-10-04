#!/usr/bin/env python3
"""
Batch Annotation Tool - Command-line interface for fast trajectory annotation.

This tool provides a streamlined annotation interface for experienced annotators
who prefer keyboard shortcuts and minimal UI overhead.

Usage:
    python scripts/batch_annotation_tool.py --batch annotation_batches/batch_001.json
    python scripts/batch_annotation_tool.py --resume  # Resume from last position
    python scripts/batch_annotation_tool.py --stats   # Show current progress
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'
CLEAR = '\033[2J'

ANNOTATION_FILE = Path("data/human_annotations/annotations.jsonl")
ANNOTATION_DIR = Path("data/human_annotations")


@dataclass
class Annotation:
    trajectory_id: str
    task_id: str
    model_id: str
    first_failure_step: int
    failure_type: str
    agent_detected: str
    detection_step: Optional[int]
    detection_evidence: str
    recovery_attempted: str
    recovery_success: str
    confidence: str
    notes: str


def load_trajectories(data_path: str, trajectory_ids: list[str] = None) -> dict:
    """Load trajectories into lookup dict."""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    trajectories = data if isinstance(data, list) else [data]
    traj_dict = {t['trajectory_id']: t for t in trajectories}

    if trajectory_ids:
        return {tid: traj_dict[tid] for tid in trajectory_ids if tid in traj_dict}
    return traj_dict


def load_existing_annotations() -> set[str]:
    """Get set of already-annotated trajectory IDs."""
    if not ANNOTATION_FILE.exists():
        return set()

    annotated = set()
    with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                ann = json.loads(line)
                annotated.add(ann.get('trajectory_id'))
    return annotated


def save_annotation(ann: Annotation):
    """Save a single annotation."""
    ANNOTATION_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "trajectory_id": ann.trajectory_id,
        "task_id": ann.task_id,
        "model_id": ann.model_id,
        "first_failure_step": ann.first_failure_step,
        "failure_type": ann.failure_type,
        "agent_detected_failure": ann.agent_detected,
        "detection_step": ann.detection_step,
        "detection_evidence": ann.detection_evidence,
        "recovery_attempted": ann.recovery_attempted,
        "recovery_success": ann.recovery_success,
        "confidence": ann.confidence,
        "annotator_notes": ann.notes,
    }

    with open(ANNOTATION_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def format_trajectory_summary(traj: dict) -> str:
    """Format a brief summary of trajectory for display."""
    traj_id = traj.get('trajectory_id', '')[:20]
    model = traj.get('model_id', 'unknown').split('-')[-1]
    steps = len(traj.get('steps', []))
    result = traj.get('final_result', 'unknown')

    # Count failures heuristically
    failed_steps = sum(
        1 for s in traj.get('steps', [])
        if s.get('feedback', {}).get('success') == False
    )

    status_icon = f"{GREEN}✓ success{RESET}" if result == "success" else f"{RED}✗ failed{RESET}"

    return f"""
{BOLD}Trajectory:{RESET} {traj_id}...
{BOLD}Model:{RESET} {model}
{BOLD}Steps:{RESET} {steps}
{BOLD}Failed Steps:{RESET} {failed_steps}
{BOLD}Result:{RESET} {status_icon}
"""


def show_candidate_failures(traj: dict) -> list[tuple[int, int]]:
    """Identify candidate failure steps with heuristic scoring."""
    steps = traj.get('steps', [])
    candidates = []
    prev_action = None

    for i, step in enumerate(steps):
        fb = step.get('feedback', {})
        action = step.get('action', {}).get('action_type')

        score = 0
        if fb.get('reward', 0) == 0:
            score += 2
        if fb.get('success') == False:
            score += 2
        if action == prev_action and i > 2:
            score += 1
        prev_action = action

        if score > 0:
            candidates.append((i, score))

    candidates.sort(key=lambda x: -x[1])
    return candidates[:5]


def format_step_detail(traj: dict, step_idx: int) -> str:
    """Format detailed view of a single step."""
    steps = traj.get('steps', [])
    if step_idx >= len(steps):
        return "Step not found"

    step = steps[step_idx]
    action = step.get('action', {})
    fb = step.get('feedback', {})
    reasoning = step.get('reasoning', '') or '(no reasoning)'

    action_type = action.get('action_type', 'unknown')
    args = action.get('action_arguments', {})

    # Build args string
    if args:
        args_str = ', '.join(f"{k}={v}" for k, v in list(args.items())[:3])
    else:
        args_str = '(none)'

    success = fb.get('success')
    reward = fb.get('reward', 0)

    success_str = f"{GREEN}success=True{RESET}" if success else f"{RED}success=False{RESET}"
    if reward != 0:
        success_str += f" {YELLOW}reward={reward}{RESET}"

    return f"""
{BOLD}Step {step_idx}:{RESET} {action_type}({args_str})
{BOLD}Result:{RESET} {success_str}
{BOLD}Reasoning:{RESET}
{reasoning[:500]}
"""


def get_annotation_stats() -> dict:
    """Get current annotation statistics."""
    annotated = load_existing_annotations()

    if not annotated:
        return {
            'total': 0,
            'annotated': 0,
            'remaining': 0,
            'by_type': {}
        }

    # Count by type
    by_type = {'SELECTION': 0, 'EXECUTION': 0, 'RECOGNITION': 0, 'RECOVERY': 0}
    detected = 0
    total = 0

    with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                ann = json.loads(line)
                ft = ann.get('failure_type')
                if ft in by_type:
                    by_type[ft] += 1
                    total += 1
                    if ann.get('agent_detected_failure') == 'YES':
                        detected += 1

    return {
        'total': total,
        'annotated': len(annotated),
        'remaining': 200 - len(annotated),
        'by_type': by_type,
        'detection_rate': detected / total if total > 0 else 0
    }


def show_progress_bar(current: int, total: int, width: int = 40):
    """Show a progress bar."""
    filled = int(width * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)
    pct = f"{100 * current / total:.1f}%" if total > 0 else "0%"
    return f"[{bar}] {pct}"


def interactive_annotate(trajectory_ids: list[str], data_path: str):
    """Interactive annotation loop."""
    print(CLEAR)

    # Load data
    print(f"{BLUE}Loading trajectories...{RESET}")
    trajectories = load_trajectories(data_path, trajectory_ids)
    existing = load_existing_annotations()

    # Filter to unannotated
    to_annotate = [tid for tid in trajectory_ids if tid not in existing]

    if not to_annotate:
        print(f"{GREEN}All trajectories in this batch are already annotated!{RESET}")
        return

    print(f"{GREEN}Loaded {len(trajectories)} trajectories{RESET}")
    print(f"Already annotated: {len(existing)}")
    print(f"To annotate: {len(to_annotate)}")
    print()

    # Annotation loop
    for idx, traj_id in enumerate(to_annotate):
        traj = trajectories.get(traj_id)
        if not traj:
            print(f"{RED}Trajectory not found: {traj_id}{RESET}")
            continue

        # Show progress
        print(CLEAR)
        print(f"{BOLD}Annotation Progress:{RESET}")
        print(f"  {idx + 1}/{len(to_annotate)} {show_progress_bar(idx + 1, len(to_annotate))}")
        print()

        # Show trajectory summary
        print(format_trajectory_summary(traj))

        # Show candidate failures
        candidates = show_candidate_failures(traj)
        if candidates:
            print(f"{BOLD}Candidate failure steps (heuristic):{RESET}")
            for step_idx, score in candidates:
                print(f"  {step_idx}: score={score}")
            print()

        # Let user select failure step
        print(f"{YELLOW}Enter first failure step (0-{len(traj.get('steps', [])) - 1}), or 'n' for no failure:{RESET}")

        while True:
            step_input = input(f"Step: ").strip()
            if step_input.lower() == 'n':
                failure_step = "NONE"
                break
            try:
                failure_step = int(step_input)
                if 0 <= failure_step < len(traj.get('steps', [])):
                    break
                print(f"Must be between 0 and {len(traj.get('steps', [])) - 1}")
            except ValueError:
                print("Enter a number or 'n'")

        # Show step detail
        if failure_step != "NONE":
            print(format_step_detail(traj, failure_step))
            print()

        # Select failure type
        print(f"{YELLOW}Select failure type:{RESET}")
        print("  1: SELECTION  - Wrong action chosen")
        print("  2: EXECUTION  - Right action, wrong execution")
        print("  3: RECOGNITION - Failed to notice wrong outcome")
        print("  4: RECOVERY   - Detected but failed to recover")

        type_map = {'1': 'SELECTION', '2': 'EXECUTION', '3': 'RECOGNITION', '4': 'RECOVERY'}
        while True:
            type_input = input("Type (1-4): ").strip()
            if type_input in type_map:
                failure_type = type_map[type_input]
                break
            print("Enter 1, 2, 3, or 4")

        # Detection
        print(f"\n{YELLOW}Did agent detect the failure?{RESET}")
        print("  1: YES")
        print("  2: NO")
        print("  3: UNCLEAR")

        det_map = {'1': 'YES', '2': 'NO', '3': 'UNCLEAR'}
        while True:
            det_input = input("Detected (1-3): ").strip()
            if det_input in det_map:
                detected = det_map[det_input]
                break
            print("Enter 1, 2, or 3")

        detection_step = None
        detection_evidence = ""
        if detected == 'YES':
            detection_step = failure_step + 1 if isinstance(failure_step, int) else None
            print(f"Detection step (default {detection_step}):", end=" ")
            ds_input = input().strip()
            if ds_input:
                detection_step = int(ds_input)
            print("Detection evidence (quote from trajectory):", end=" ")
            detection_evidence = input()

        # Recovery
        print(f"\n{YELLOW}Recovery attempted?{RESET}")
        print("  1: YES")
        print("  2: NO")

        while True:
            rec_input = input("Recovery (1-2): ").strip()
            if rec_input == '1':
                recovery_attempted = 'YES'
                print("  1: YES - Successful")
                print("  2: NO  - Failed")
                while True:
                    rs_input = input("Success (1-2): ").strip()
                    if rs_input == '1':
                        recovery_success = 'YES'
                        break
                    elif rs_input == '2':
                        recovery_success = 'NO'
                        break
                    print("Enter 1 or 2")
                break
            elif rec_input == '2':
                recovery_attempted = 'NO'
                recovery_success = 'NA'
                break
            print("Enter 1 or 2")

        # Confidence
        print(f"\n{YELLOW}Annotation confidence:{RESET}")
        print("  1: HIGH")
        print("  2: MEDIUM")
        print("  3: LOW")

        conf_map = {'1': 'high', '2': 'medium', '3': 'low'}
        while True:
            conf_input = input("Confidence (1-3): ").strip()
            if conf_input in conf_map:
                confidence = conf_map[conf_input]
                break
            print("Enter 1, 2, or 3")

        # Notes
        print("\nNotes (optional, Enter to skip):", end=" ")
        notes = input().strip()

        # Save
        ann = Annotation(
            trajectory_id=traj_id,
            task_id=traj.get('task_id'),
            model_id=traj.get('model_id'),
            first_failure_step=failure_step,
            failure_type=failure_type,
            agent_detected=detected,
            detection_step=detection_step,
            detection_evidence=detection_evidence,
            recovery_attempted=recovery_attempted,
            recovery_success=recovery_success,
            confidence=confidence,
            notes=notes
        )

        save_annotation(ann)
        print(f"\n{GREEN}✓ Saved annotation for {traj_id[:20]}...{RESET}")

        # Brief pause
        if idx < len(to_annotate) - 1:
            input("Press Enter to continue...")


def show_stats():
    """Show current annotation statistics."""
    stats = get_annotation_stats()

    print(f"""
{BOLD}Annotation Statistics{RESET}
{'=' * 40}

Total Trajectories: 200
Already Annotated:   {stats['annotated']}
Remaining:           {stats['remaining']}

Progress: {show_progress_bar(stats['annotated'], 200)}

""")

    if stats['total'] > 0:
        print(f"Failure Type Distribution:")
        print(f"  SELECTION:  {stats['by_type']['SELECTION']}")
        print(f"  EXECUTION:  {stats['by_type']['EXECUTION']}")
        print(f"  RECOGNITION:{stats['by_type']['RECOGNITION']}")
        print(f"  RECOVERY:   {stats['by_type']['RECOVERY']}")
        print()
        print(f"Detection Rate: {100 * stats['detection_rate']:.1f}%")
    else:
        print("No annotations yet. Run the annotation tool to begin!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Batch annotation tool")
    parser.add_argument('--batch', help='Path to batch JSON file')
    parser.add_argument('--resume', action='store_true', help='Resume from last position')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    parser.add_argument('--data', default='data/raw/osworld_claude4_converted.json',
                        help='Path to trajectory data')

    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    if args.batch:
        with open(args.batch, 'r', encoding='utf-8') as f:
            batch_data = json.load(f)
        trajectory_ids = batch_data.get('priority_order', [])
    elif args.resume:
        # Get unannotated from queue
        with open('annotation_batches/annotation_queue.json', 'r', encoding='utf-8') as f:
            queue = json.load(f)
        trajectory_ids = queue.get('priority_order', [])
    else:
        print("Error: Provide --batch or --resume")
        print("Example: python scripts/batch_annotation_tool.py --batch annotation_batches/batch_001.json")
        sys.exit(1)

    interactive_annotate(trajectory_ids, args.data)


if __name__ == "__main__":
    # Fix Windows console encoding
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

    main()
