#!/usr/bin/env python3
"""
Human Annotation Campaign Runner

Comprehensive runner that guides users through the entire annotation campaign.

Usage:
    python scripts/run_annotation_campaign.py
    python scripts/run_annotation_campaign.py --step 1
    python scripts/run_annotation_campaign.py --auto
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

ANNOTATION_FILE = Path("data/human_annotations/annotations.jsonl")


def get_annotation_count() -> int:
    """Get current annotation count."""
    if not ANNOTATION_FILE.exists():
        return 0
    count = 0
    with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def run_step(step: int):
    """Run a specific step of the campaign."""
    n = get_annotation_count()

    print(f"""
{'='*60}
Human Annotation Campaign - Step {step}
{'='*60}
Current annotations: {n}
""")

    if step == 1:
        print("STEP 1: Launch Annotation Tool")
        print()
        print("Choose your interface:")
        print()
        print("Option A: Streamlit Web Interface")
        print("  - Best for beginners")
        print("  - Visual trajectory viewer")
        print("  - Point-and-click annotation")
        print()
        print("Option B: Command Line Tool")
        print("  - Fast for experienced annotators")
        print("  - Keyboard-driven")
        print("  - Batch processing")
        print()
        choice = input("Enter A or B: ").strip().upper()

        if choice == 'A':
            print("\nLaunching Streamlit...")
            print("Browser will open at http://localhost:8501")
            subprocess.run([sys.executable, "-m", "streamlit", "run",
                          "annotation_tool/app.py"])
        else:
            print("\nLaunching command-line tool...")
            subprocess.run([sys.executable, "scripts/batch_annotation_tool.py",
                          "--batch", "annotation_batches/batch_001.json"])

    elif step == 2:
        print("STEP 2: Quality Check")
        print()
        if n < 10:
            print(f"⚠️  Only {n} annotations. Need at least 10 for QC.")
            print("Continue annotating first.")
            return

        print("Running quality control...")
        result = subprocess.run([sys.executable, "scripts/phase30_annotation_qc.py"],
                               capture_output=True, text=True)
        print(result.stdout)

    elif step == 3:
        print("STEP 3: Progress Review")
        print()
        print("Running progress tracker...")
        subprocess.run([sys.executable, "scripts/annotation_progress_tracker.py"])

    elif step == 4:
        print("STEP 4: RQ1 Analysis")
        print()
        if n < 50:
            print(f"⚠️  Only {n} annotations. Need 50 for RQ1.")
            print(f"Need {50 - n} more annotations.")
            return

        print("Generating RQ1 human-grounded results...")
        subprocess.run([sys.executable, "scripts/run_human_analysis.py"])

    elif step == 5:
        print("STEP 5: Thesis Gate Decision")
        print()
        results_file = Path("results/RQ1_human_first50/thesis_gate_report.md")
        if not results_file.exists():
            print("⚠️  Run Step 4 first to generate results.")
            return

        with open(results_file, 'r', encoding='utf-8') as f:
            print(f.read())

    elif step == 6:
        print("STEP 6: Prepare RQ2 Experiments")
        print()
        candidates_file = Path("results/RQ1_human_first50/rq2_candidate_cases.json")
        if not candidates_file.exists():
            print("⚠️  Run Step 4 first to generate candidates.")
            return

        with open(candidates_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"RQ2 candidate cases: {data['n_candidates']}")
            print()
            for i, case in enumerate(data['candidates'][:5]):
                print(f"  {i+1}. {case['trajectory_id'][:20]}... - {case['failure_type']}")

    else:
        print(f"Unknown step: {step}")


def run_full_campaign():
    """Run the full annotation campaign automatically."""

    print("""
╔══════════════════════════════════════════════════════════════╗
║         Human Annotation Campaign - Full Runner              ║
║                                                              ║
║  50 Annotations → RQ1 Results → Thesis Gate Decision        ║
╚══════════════════════════════════════════════════════════════╝
""")

    n = get_annotation_count()
    print(f"Starting annotations: {n}")
    print()

    # Phase 1: Annotate to 50
    print("PHASE 1: Annotate to 50 trajectories")
    print("-" * 40)

    if n < 50:
        print(f"Need {50 - n} more annotations")
        print()
        print("Choose your interface:")
        print()
        print("1. Streamlit (Web UI)")
        print("2. Command Line (Fast)")
        print()
        choice = input("Enter 1 or 2: ").strip()

        if choice == '1':
            print("\nLaunching Streamlit...")
            subprocess.run([sys.executable, "-m", "streamlit", "run",
                          "annotation_tool/app.py"])
        else:
            print("\nLaunching command-line batch tool...")
            subprocess.run([sys.executable, "scripts/batch_annotation_tool.py",
                          "--batch", "annotation_batches/batch_001.json"])

    # Check after annotation
    n = get_annotation_count()

    if n >= 50:
        print(f"\n✅ Reached {n} annotations!")
        print()

        # Phase 2: Run RQ1 analysis
        print("PHASE 2: Running RQ1 Analysis")
        print("-" * 40)
        subprocess.run([sys.executable, "scripts/run_human_analysis.py"])

        # Phase 3: Show thesis gate
        print()
        print("PHASE 3: Thesis Gate Decision")
        print("-" * 40)

        results_file = Path("results/RQ1_human_first50/thesis_gate_report.md")
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Print just the decision part
                lines = content.split('\n')
                print('\n'.join(lines[:50]))

        # Phase 4: Next steps
        print()
        print("PHASE 4: Next Steps")
        print("-" * 40)
        print("""
Next actions:
1. Double-annotate 20 cases (inter-annotator agreement)
2. Run RQ2 API experiments (C0-C3)
3. Prepare Oracle experiments (RQ3)

See: results/RQ1_human_first50/ for full results
""")
    else:
        print(f"\n⏳ Still at {n} annotations. Continue annotating.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Human annotation campaign runner")
    parser.add_argument('--step', type=int, help='Run specific step')
    parser.add_argument('--auto', action='store_true', help='Run full campaign')
    parser.add_argument('--progress', action='store_true', help='Show progress only')

    args = parser.parse_args()

    if args.progress:
        n = get_annotation_count()
        print(f"Annotations: {n}/200 ({100*n/200:.1f}%)")
        return

    if args.step:
        run_step(args.step)
    elif args.auto:
        run_full_campaign()
    else:
        # Interactive menu
        while True:
            n = get_annotation_count()
            print(f"""
╔══════════════════════════════════════════════════════════════╗
║         Human Annotation Campaign                           ║
║                                                              ║
║  Annotations: {n:3d}/200 ({100*n/200:5.1f}%)                             ║
╚══════════════════════════════════════════════════════════════╝

Menu:
  1. Start/Continue Annotation
  2. Quality Control Check
  3. View Progress
  4. Run RQ1 Analysis (need 50+)
  5. View Thesis Gate
  6. View RQ2 Candidates
  0. Exit
""")
            choice = input("Enter choice: ").strip()

            if choice == '0':
                break
            elif choice == '1':
                run_step(1)
            elif choice == '2':
                run_step(2)
            elif choice == '3':
                run_step(3)
            elif choice == '4':
                run_step(4)
            elif choice == '5':
                run_step(5)
            elif choice == '6':
                run_step(6)


if __name__ == "__main__":
    # Fix Windows console encoding
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

    main()
