"""
OSWorld Trajectory Annotation Tool - Human-Grounded Validation Version

Streamlit app for human annotation of failure types in agent trajectories.
This version is designed for real scientific evidence production.

Usage:
    streamlit run annotation_tool/app.py

IMPORTANT:
- Annotations here are for REAL paper evidence
- Every label must be grounded in observable evidence
- Do not infer hidden mental states
- Only use explicit reasoning/action evidence

Annotation Schema:
    - trajectory_id: str
    - task_id: str
    - model_id: str
    - first_failure_step: int | "NONE"
    - failure_type: SELECTION|EXECUTION|RECOGNITION|RECOVERY
    - agent_detected_failure: YES|NO|UNCLEAR
    - detection_step: int | null
    - detection_evidence: str
    - recovery_attempted: YES|NO
    - recovery_success: YES|NO|NA
    - annotator_notes: str
    - confidence: high|medium|low
"""

import json
import logging
import os
import random
from pathlib import Path
from typing import Optional

import streamlit as st

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trajectory_analyzer.data_loader import OSWorldLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ANNOTATION_OUTPUT_DIR = Path("data/human_annotations")
ANNOTATION_FILE = ANNOTATION_OUTPUT_DIR / "annotations.jsonl"

# Failure type definitions (MUST be shown to annotators)
FAILURE_TYPE_DEFINITIONS = """
**SELECTION**: Agent selected the WRONG action given available information.
The agent chose an action that was incorrect for achieving the goal, but the action was properly executed.

**EXECUTION**: Agent selected the CORRECT action but the environment did NOT execute it as intended.
The action intent was correct but implementation failed (e.g., wrong coordinates, command error).

**RECOGNITION**: The outcome was WRONG but the agent FAILED to notice it.
The agent continued as if nothing was wrong - no acknowledgment of failure.

**RECOVERY**: Agent DETECTED the failure but FAILED to recover properly.
The recovery strategy was wrong or ineffective.
"""

# Detection evidence markers
DETECTION_MARKERS = [
    "failed", "didn't work", "wrong", "incorrect", "error", "mistake",
    "that didn't", "this didn't", "was wrong", "went wrong", "problem",
    "let me try", "should try", "need to try", "let me redo", "retry"
]


def load_annotations() -> list[dict]:
    """Load existing annotations."""
    if not ANNOTATION_FILE.exists():
        return []

    annotations = []
    with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                annotations.append(json.loads(line))
    return annotations


def save_annotation(annotation: dict):
    """Save a single annotation to file."""
    ANNOTATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(ANNOTATION_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(annotation, ensure_ascii=False) + '\n')


def get_unlabeled_trajectories(
    trajectories: list[dict],
    annotations: list[dict]
) -> list[dict]:
    """Get trajectories that haven't been annotated yet."""
    annotated_ids = {a.get("trajectory_id") for a in annotations}
    return [t for t in trajectories if t.get("trajectory_id") not in annotated_ids]


def format_action(action: dict) -> str:
    """Format action for display."""
    action_type = action.get("action_type", "unknown")
    args = action.get("action_arguments", {})

    if not args:
        return action_type

    arg_strs = []
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 100:
            value = value[:97] + "..."
        arg_strs.append(f"{key}={value}")

    return f"{action_type}({', '.join(arg_strs[:3])})"


def check_detection_in_reasoning(reasoning: str) -> list[str]:
    """Check if reasoning contains explicit failure acknowledgment."""
    if not reasoning:
        return []

    reasoning_lower = reasoning.lower()
    found = []
    for marker in DETECTION_MARKERS:
        if marker in reasoning_lower:
            found.append(marker)

    return found


def render_local_context(
    trajectory: dict,
    candidate_step: int,
    context_before: int = 2,
    context_after: int = 3
):
    """Render local causal window around candidate failure step."""
    steps = trajectory.get('steps', [])
    total_steps = len(steps)

    start_idx = max(0, candidate_step - context_before)
    end_idx = min(total_steps, candidate_step + context_after + 1)

    st.markdown(f"#### Causal Window: Steps {start_idx} to {end_idx-1}")

    for i in range(start_idx, end_idx):
        step = steps[i]
        is_candidate = (i == candidate_step)

        # Step header with indicator
        indicator = "🔴 **FAILURE**" if is_candidate else f"Step {i}"
        with st.expander(f"{indicator}: {format_action(step.get('action', {}))}", expanded=True):

            # Feedback signal if available
            feedback = step.get('feedback', {})
            if feedback:
                col1, col2 = st.columns(2)
                with col1:
                    success = feedback.get('success', None)
                    if success is not None:
                        color = "green" if success else "red"
                        st.markdown(f"**Feedback:** :{color}[{'Success' if success else 'Failed'}]")
                with col2:
                    reward = feedback.get('reward', 0)
                    if reward != 0:
                        st.markdown(f"**Reward:** {reward}")

            # Reasoning trace
            reasoning = step.get('reasoning', '')
            if reasoning:
                detection_markers = check_detection_in_reasoning(reasoning)
                if detection_markers:
                    st.success(f"🔍 **Detection signals found:** {', '.join(detection_markers)}")
                    st.markdown(f"**Reasoning:**\n\n{reasoning[:1000]}")
                else:
                    st.markdown(f"**Reasoning:**\n\n{reasoning[:1000]}")
            else:
                st.markdown("*No reasoning trace*")

            # Action details
            action = step.get('action', {})
            action_type = action.get('action_type', 'unknown')
            action_args = action.get('action_arguments', {})

            if action_args:
                st.markdown("**Action Arguments:**")
                for k, v in list(action_args.items())[:5]:
                    if isinstance(v, str) and len(v) > 200:
                        v = v[:197] + "..."
                    st.code(f"{k}: {v}")

            # Observation hint
            obs = step.get('observation', {})
            if obs:
                obs_text = obs.get('text', '')
                screenshot = obs.get('screenshot_file', '')
                if screenshot:
                    st.markdown(f"📷 Screenshot: `{screenshot}`")
                if obs_text:
                    st.markdown(f"**Obs:** {obs_text[:300]}...")


def render_full_trajectory(trajectory: dict, max_steps: int = 15):
    """Render full trajectory metadata and overview."""
    st.subheader("📋 Trajectory Metadata")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Trajectory ID", trajectory.get('trajectory_id', 'N/A')[:20] + "...")
    with col2:
        st.metric("Task ID", trajectory.get('task_id', 'N/A')[:20] + "...")
    with col3:
        st.metric("Model", trajectory.get('model_id', 'N/A'))
    with col4:
        result = trajectory.get('final_result', 'unknown')
        color = "green" if result == "success" else "red"
        st.metric("Result", f":{color}[{result}]")

    # Task description
    task_desc = trajectory.get('task_description', 'No description available')
    with st.expander("📝 Task Description"):
        st.markdown(task_desc[:500] if len(task_desc) > 500 else task_desc)

    # Trajectory stats
    steps = trajectory.get('steps', [])
    st.markdown(f"**Total Steps:** {len(steps)}")

    return steps


def main():
    """Main annotation interface for human-grounded validation."""

    st.set_page_config(
        page_title="Human Annotation - Paper 1",
        page_icon="🏷️",
        layout="wide"
    )

    st.title("🏷️ Human-Grounded Trajectory Annotation")
    st.markdown("""
    **This tool produces real scientific evidence for Paper 1.**

    ## Instructions

    1. Review the **task description** and **trajectory metadata**
    2. Examine the **causal window** around candidate failure steps
    3. For each annotation, provide:
       - First consequential failure step
       - Failure type (exactly one)
       - Agent detection evidence
       - Recovery information

    ## Failure Type Definitions

    """ + FAILURE_TYPE_DEFINITIONS)

    st.markdown("---")

    # Initialize session state
    if 'trajectories' not in st.session_state:
        st.session_state.trajectories = []
        st.session_state.current_idx = 0
        st.session_state.annotations = []

    # Sidebar: Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        data_path = st.text_input(
            "Data Path",
            value="data/raw/osworld_claude4_converted.json",
            help="Path to trajectory data file"
        )

        load_button = st.button("📂 Load Data", type="primary")

        st.markdown("---")

        # Statistics
        if load_button or st.session_state.trajectories:
            if load_button:
                with st.spinner("Loading trajectories..."):
                    loader = OSWorldLoader(data_path)
                    st.session_state.trajectories = list(loader.load(data_path))
                    st.session_state.annotations = load_annotations()
                    st.success(f"Loaded {len(st.session_state.trajectories)} trajectories")

            # Stats
            unlabeled = get_unlabeled_trajectories(
                st.session_state.trajectories,
                st.session_state.annotations
            )

            st.markdown(f"**Total:** {len(st.session_state.trajectories)}")
            st.markdown(f"**Annotated:** {len(st.session_state.annotations)}")
            st.markdown(f"**Remaining:** {len(unlabeled)}")

            # Progress bar
            if len(st.session_state.trajectories) > 0:
                progress = len(st.session_state.annotations) / len(st.session_state.trajectories)
                st.progress(progress)

            st.markdown("---")

            # Navigation
            st.subheader("🧭 Navigation")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("◀ Prev") and st.session_state.current_idx > 0:
                    st.session_state.current_idx -= 1
            with col2:
                if st.button("Next ▶"):
                    st.session_state.current_idx = min(
                        st.session_state.current_idx + 1,
                        len(unlabeled) - 1
                    )

            if st.button("🎲 Random"):
                st.session_state.current_idx = random.randint(0, len(unlabeled) - 1)

            st.number_input(
                "Jump to index",
                min_value=0,
                max_value=max(0, len(unlabeled) - 1),
                value=st.session_state.current_idx,
                key="jump_idx"
            )
            if st.button("Go to index"):
                st.session_state.current_idx = st.session_state.jump_idx

            # Quick stats
            st.markdown("---")
            st.subheader("📊 Current Stats")

            if st.session_state.annotations:
                by_type = {}
                for ann in st.session_state.annotations:
                    ft = ann.get('failure_type', 'unknown')
                    by_type[ft] = by_type.get(ft, 0) + 1

                for ft, count in sorted(by_type.items(), key=lambda x: -x[1]):
                    st.markdown(f"  - {ft}: {count}")

    # Main content
    if not st.session_state.trajectories:
        st.info("👈 Load trajectory data from the sidebar to begin annotation.")
        return

    # Get unlabeled trajectories
    unlabeled = get_unlabeled_trajectories(
        st.session_state.trajectories,
        st.session_state.annotations
    )

    if not unlabeled:
        st.success("✅ All trajectories have been annotated!")
        st.balloons()
        return

    # Get current trajectory
    current_traj = unlabeled[st.session_state.current_idx]
    traj_id = current_traj.get('trajectory_id', 'unknown')
    steps = current_traj.get('steps', [])

    # Render metadata
    render_full_trajectory(current_traj)

    st.markdown("---")

    # Candidate failure step selection
    st.subheader("🔍 Candidate Failure Analysis")

    # Heuristic candidate detection
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
            candidates.append({'step': i, 'score': score})

    # Sort by score
    candidates.sort(key=lambda x: -x['score'])

    # Show top candidates
    if candidates:
        st.markdown("**Top candidate failure steps (heuristic):**")
        for cand in candidates[:5]:
            st.markdown(f"  - Step {cand['step']} (score: {cand['score']})")

        selected_candidate = st.selectbox(
            "Select candidate to examine:",
            options=[c['step'] for c in candidates],
            format_func=lambda x: f"Step {x} (score: {next(c['score'] for c in candidates if c['step']==x)})"
        )
    else:
        selected_candidate = st.selectbox(
            "Select step to examine:",
            options=list(range(len(steps))),
            format_func=lambda x: f"Step {x}"
        )

    # Render local causal window
    st.markdown("---")
    render_local_context(current_traj, selected_candidate)

    # Annotation form
    st.markdown("---")
    st.subheader("📝 Annotation Form")

    with st.form(key="human_annotation_form"):

        # A. First Consequential Failure
        st.markdown("#### A. First Consequential Failure")

        col1, col2 = st.columns(2)
        with col1:
            first_failure_step = st.number_input(
                "First failure step (0-indexed):",
                min_value=0,
                max_value=len(steps) - 1,
                value=selected_candidate,
                help="The step where the first consequential failure occurred"
            )

            no_failure = st.checkbox("No consequential failure in this trajectory")

            if no_failure:
                first_failure_step = "NONE"

        with col2:
            confidence = st.selectbox(
                "Annotation confidence:",
                options=["high", "medium", "low"],
                index=1,
                help="How confident are you in this annotation?"
            )

        # B. Failure Type
        st.markdown("#### B. Failure Type")
        st.caption("**Select exactly ONE failure type.**")

        failure_type = st.radio(
            "Failure Type:",
            options=["SELECTION", "EXECUTION", "RECOGNITION", "RECOVERY"],
            captions=[
                "Wrong action chosen given available info",
                "Right action but wrong execution",
                "Failed to notice wrong outcome",
                "Detected but failed to recover"
            ],
            horizontal=True
        )

        # C. Agent Detection
        st.markdown("#### C. Agent Failure Awareness")
        st.caption("**Did the agent explicitly acknowledge the failure?**")

        col1, col2 = st.columns(2)
        with col1:
            agent_detected = st.radio(
                "Agent detected failure?",
                options=["YES", "NO", "UNCLEAR"],
                horizontal=True
            )

        with col2:
            if agent_detected == "YES":
                detection_step = st.number_input(
                    "Detection step:",
                    min_value=first_failure_step if isinstance(first_failure_step, int) else 0,
                    max_value=len(steps) - 1,
                    value=min(first_failure_step + 1 if isinstance(first_failure_step, int) else 1, len(steps) - 1)
                )
            else:
                detection_step = None

        detection_evidence = st.text_area(
            "Detection evidence (quote from reasoning/actions):",
            placeholder="e.g., 'agent said: the action failed to...'",
            help="Only use EXPLICIT evidence from the trajectory"
        )

        # D. Recovery
        st.markdown("#### D. Recovery Attempt")

        col1, col2 = st.columns(2)
        with col1:
            recovery_attempted = st.radio(
                "Recovery attempted?",
                options=["YES", "NO"],
                horizontal=True
            )

        with col2:
            if recovery_attempted == "YES":
                recovery_success = st.radio(
                    "Recovery successful?",
                    options=["YES", "NO"],
                    horizontal=True
                )
            else:
                recovery_success = "NA"

        # Notes
        notes = st.text_area(
            "Annotator notes:",
            placeholder="Any additional observations...",
            height=80
        )

        st.markdown("---")

        # Submit
        submitted = st.form_submit_button("✅ Submit Annotation", type="primary")

        if submitted:
            if no_failure and first_failure_step == "NONE":
                final_failure_step = "NONE"
            else:
                final_failure_step = first_failure_step

            annotation = {
                "trajectory_id": traj_id,
                "task_id": current_traj.get('task_id'),
                "model_id": current_traj.get('model_id'),
                "first_failure_step": final_failure_step,
                "failure_type": failure_type,
                "agent_detected_failure": agent_detected,
                "detection_step": detection_step,
                "detection_evidence": detection_evidence,
                "recovery_attempted": recovery_attempted,
                "recovery_success": recovery_success,
                "confidence": confidence,
                "annotator_notes": notes,
                "annotated_at": str(Path.cwd()),
            }

            save_annotation(annotation)
            st.session_state.annotations.append(annotation)

            st.success(f"✅ Annotated: {traj_id}")

            # Auto-advance
            if st.session_state.current_idx < len(unlabeled) - 1:
                st.session_state.current_idx += 1
                st.rerun()
            else:
                st.balloons()
                st.info("🎉 All trajectories annotated!")


if __name__ == "__main__":
    main()
