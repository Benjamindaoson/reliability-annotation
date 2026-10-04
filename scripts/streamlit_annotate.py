"""
Streamlit Annotation Tool for Batch 001

Run: streamlit run scripts/streamlit_annotate.py
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="OSWorld Annotation Tool",
    page_icon="📝",
    layout="wide"
)

# Load data
@st.cache_data
def load_batch():
    with open("annotation_batches_calibration/batch_001.json", "r", encoding="utf-8") as f:
        return json.load(f)

batch_data = load_batch()
trajectories = batch_data["trajectories"]

# Initialize session state
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "annotations" not in st.session_state:
    st.session_state.annotations = {}
if "saved_files" not in st.session_state:
    st.session_state.saved_files = []

# Sidebar
st.sidebar.title("OSWorld Annotation")
st.sidebar.markdown("---")

# Progress
st.sidebar.markdown(f"**Progress:** {st.session_state.current_idx + 1}/{len(trajectories)}")

# Navigation
col1, col2 = st.sidebar.columns(2)
if col1.button("Previous"):
    if st.session_state.current_idx > 0:
        st.session_state.current_idx -= 1
        st.rerun()

if col2.button("Next"):
    if st.session_state.current_idx < len(trajectories) - 1:
        st.session_state.current_idx += 1
        st.rerun()

# Jump to
traj_num = st.sidebar.number_input(
    "Jump to trajectory #",
    min_value=1,
    max_value=len(trajectories),
    value=st.session_state.current_idx + 1
)
if traj_num != st.session_state.current_idx + 1:
    st.session_state.current_idx = traj_num - 1
    st.rerun()

st.sidebar.markdown("---")

# Current trajectory
traj = trajectories[st.session_state.current_idx]
traj_id = traj["trajectory_id"]

st.sidebar.markdown(f"**Task Type:** {traj['task_type']}")
st.sidebar.markdown(f"**Steps:** {traj['total_steps']}")
st.sidebar.markdown(f"**Result:** {traj['final_result']}")

# Main content
st.title(f"📝 Annotation: {traj_id[:40]}...")

# Trajectory info
st.markdown("### Trajectory Steps")
st.markdown(f"""
| Property | Value |
|----------|-------|
| Trajectory ID | `{traj_id}` |
| Task Type | {traj['task_type']} |
| Total Steps | {traj['total_steps']} |
| Final Result | {traj['final_result']} |
""")

# Display steps
st.markdown("### Actions")
for step in traj["steps"]:
    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
    with col1:
        st.markdown(f"**Step {step['step_num']}**")
    with col2:
        st.code(step["action"], language=None)
    with col3:
        badge = "✓" if step["done"] else "✗"
        color = "green" if step["done"] else "red"
        st.markdown(f":{color}[{badge}]")
    with col4:
        st.markdown(f"reward={step['reward']}")

st.markdown("---")

# Annotation form
st.markdown("## Failure Analysis")

# Check if already annotated
existing = st.session_state.annotations.get(traj_id, {})

# Causal Analysis
st.markdown("### Causal Analysis")

col1, col2 = st.columns(2)
with col1:
    first_failure_step = st.number_input(
        "First Failure Step (t*)",
        min_value=1,
        max_value=traj["total_steps"],
        value=existing.get("first_failure_step", 1)
    )

with col2:
    st.markdown("&nbsp;")  # spacing

what_happened = st.text_area(
    "What happened?",
    value=existing.get("what_happened", ""),
    placeholder="Describe the failure event...",
    height=80
)

why_consequential = st.text_area(
    "Why consequential?",
    value=existing.get("why_consequential", ""),
    placeholder="How does this failure affect subsequent trajectory?",
    height=80
)

why_qualifies = st.text_area(
    "Why does this step qualify as onset?",
    value=existing.get("why_qualifies", ""),
    placeholder="This step is the first erroneous action because...",
    height=80
)

why_preceding_not = st.text_area(
    "Why does preceding step NOT qualify?",
    value=existing.get("why_preceding_not", ""),
    placeholder="The preceding step was valid because...",
    height=80
)

st.markdown("---")

# Label
st.markdown("### Failure Classification")

failure_types = ["SELECTION", "EXECUTION", "RECOGNITION", "RECOVERY", "UNCERTAIN"]
failure_type = st.radio(
    "Failure Type",
    options=failure_types,
    index=failure_types.index(existing.get("failure_type", "SELECTION")) if existing.get("failure_type") in failure_types else 0,
    horizontal=True
)

confidence = st.slider(
    "Confidence",
    min_value=0.0,
    max_value=1.0,
    value=float(existing.get("confidence", 0.7)),
    step=0.1
)

reasoning = st.text_area(
    "Reasoning",
    value=existing.get("reasoning", ""),
    placeholder="Brief explanation connecting causal analysis to classification...",
    height=80
)

st.markdown("---")

# Agent awareness
st.markdown("### Agent Awareness")

detected_options = ["YES", "NO", "UNCLEAR"]
detected = st.radio(
    "Did agent detect the failure?",
    options=detected_options,
    index=detected_options.index(existing.get("detected", "NO")) if existing.get("detected") in detected_options else 1,
    horizontal=True
)

detection_step = None
if detected == "YES":
    detection_step = st.number_input(
        "Detection Step",
        min_value=1,
        max_value=traj["total_steps"],
        value=existing.get("detection_step", first_failure_step + 1)
    )

awareness_evidence = st.text_area(
    "Evidence for awareness (or lack thereof)",
    value=existing.get("awareness_evidence", ""),
    placeholder="Describe observable evidence...",
    height=60
)

st.markdown("---")

# Save annotation
if st.button("Save Annotation", type="primary", use_container_width=True):
    annotation = {
        "trajectory_id": traj_id,
        "annotator_id": "streamlit-user",
        "annotator_model": "streamlit-ui",
        "annotator_type": "HUMAN",
        "timestamp": datetime.now().isoformat(),
        "trajectory_hash": traj["trajectory_hash"],

        "causal_analysis": {
            "first_failure_step": first_failure_step,
            "what_happened": what_happened,
            "why_consequential": why_consequential,
            "why_this_step": f"Step {first_failure_step} is the first consequential failure.",
            "why_qualifies": why_qualifies,
            "why_preceding_not": why_preceding_not
        },

        "label": {
            "type": failure_type,
            "confidence": confidence,
            "reasoning": reasoning
        },

        "agent_awareness": {
            "detected": detected,
            "detection_step": detection_step,
            "evidence": awareness_evidence
        },

        "evidence_steps": list(range(first_failure_step, min(first_failure_step + 3, traj["total_steps"] + 1))),
        "evidence_text": f"Failure at step {first_failure_step}: {what_happened}. {why_consequential}",
        "annotator_notes": ""
    }

    st.session_state.annotations[traj_id] = annotation
    st.success(f"Saved annotation for {traj_id[:40]}...")

    # Auto-save to file
    save_to_file()

st.markdown("---")

# Export all
st.markdown("### Export")

if st.button("Export All Annotations (JSONL)", use_container_width=True):
    output_file = save_to_file()
    st.success(f"Exported to: {output_file}")

# Show saved files
if st.session_state.saved_files:
    st.markdown("**Saved files:**")
    for f in st.session_state.saved_files:
        st.markdown(f"- {f}")

# Progress overview
st.sidebar.markdown("---")
st.sidebar.markdown("### Annotation Status")
for i, t in enumerate(trajectories):
    tid = t["trajectory_id"]
    status = "✅" if tid in st.session_state.annotations else "⬜"
    label = ""
    if tid in st.session_state.annotations:
        label = st.session_state.annotations[tid]["label"]["type"]
    st.sidebar.markdown(f"{status} {i+1}. {label}")

completed = len(st.session_state.annotations)
total = len(trajectories)
st.sidebar.progress(completed / total, text=f"{completed}/{total} completed")


def save_to_file():
    """Save all annotations to JSONL file"""
    output_dir = Path("data/annotations/raw/human")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"streamlit_batch001_{timestamp}.jsonl"

    with open(output_file, "w", encoding="utf-8") as f:
        for ann in st.session_state.annotations.values():
            f.write(json.dumps(ann, ensure_ascii=False) + "\n")

    if str(output_file) not in st.session_state.saved_files:
        st.session_state.saved_files.append(str(output_file))

    return output_file
