"""
Gemini API Batch Annotator

Uses Gemini API to annotate trajectories with causal analysis (v2 format).

Usage:
    python scripts/gemini_annotate.py --batch annotation_batches_calibration/batch_001.json --output gemini_batch001.jsonl
    python scripts/gemini_annotate.py --batch annotation_batches_calibration/batch_001.json --output gemini_batch001.jsonl --api_key YOUR_KEY
"""

import json
import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Gemini API
try:
    import google.genai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

PROMPT_TEMPLATE = """You are analyzing a trajectory from an AI agent performing a task in a computer environment (OSWorld).

## Your Task
Identify the FIRST CONSEQUENTIAL FAILURE and classify its type.

## CRITICAL: Causal Attribution First, Classification Second

Your task is NOT to classify. Your task is CAUSAL ATTRIBUTION.

You MUST trace the causal chain before assigning any label:
1. What happened?
2. Why does this affect the future trajectory?
3. What label best explains this causal chain?

## Failure Type Definitions

### SELECTION
The agent selected the WRONG action given available information.
- Clicked wrong element
- Took action that contradicts task objective

### EXECUTION
The agent selected the CORRECT action but execution failed.
- Environmental error
- Wrong parameters despite correct intent

### RECOGNITION
The outcome was WRONG but the agent did NOT notice it.
- Agent continued as if nothing was wrong
- No acknowledgment in subsequent steps

### RECOVERY
The agent DETECTED the failure but failed to recover.
- Agent acknowledged error
- Recovery attempt was incorrect

### UNCERTAIN
Cannot determine with confidence. Use low confidence (< 0.5).

## Output Format

Output ONLY a valid JSON object:

```json
{{
  "trajectory_id": "the trajectory identifier",
  "annotator_id": "gemini-2-5-pro",
  "annotator_model": "gemini-2-5-pro",
  "annotator_type": "LLM",
  "timestamp": "ISO 8601 timestamp",
  "trajectory_hash": "from trajectory data",

  "causal_analysis": {{
    "first_failure_step": N,
    "what_happened": "description of failure event",
    "why_consequential": "how this affects subsequent trajectory",
    "why_this_step": "why this is the first consequential failure"
  }},

  "label": {{
    "type": "SELECTION|EXECUTION|RECOGNITION|RECOVERY|UNCERTAIN",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
  }},

  "agent_awareness": {{
    "detected": "YES|NO|UNCLEAR",
    "detection_step": N or null,
    "evidence": "description"
  }},

  "evidence_steps": [N1, N2, ...],
  "evidence_text": "detailed evidence from trajectory",
  "annotator_notes": "optional notes"
}}
```

## Trajectory Data

{trajectory_json}

## Output ONLY the JSON object. No explanation.
"""


def load_batch(batch_file: Path) -> list:
    """Load trajectory batch from JSON file"""
    with open(batch_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("trajectories", [])


def format_trajectory_for_prompt(traj: dict) -> str:
    """Format trajectory data for prompt"""
    steps = traj.get("steps", [])
    formatted_steps = []

    for step in steps:
        step_num = step.get("step_num", "?")
        action = step.get("action", "unknown")
        reward = step.get("reward", 0)
        done = step.get("done", False)

        formatted_steps.append(f"Step {step_num}: {action} | reward={reward} done={done}")

    return f"""Trajectory ID: {traj.get('trajectory_id', 'unknown')}
Task Type: {traj.get('task_type', 'unknown')}
Task Description: {traj.get('task_description', 'unknown')}
Final Result: {traj.get('final_result', 'unknown')}
Total Steps: {traj.get('total_steps', len(steps))}

Steps:
{chr(10).join(formatted_steps)}
"""


def annotate_with_gemini(
    trajectory: dict,
    api_key: str,
    model: str = "gemini-2.5-pro-exp-08-07"
) -> Optional[dict]:
    """Annotate a single trajectory with Gemini"""
    if not GEMINI_AVAILABLE:
        print("Error: google-genai not installed. Run: pip install google-genai")
        return None

    try:
        from google.genai import Client

        # Create client
        client = Client(api_key=api_key)

        # Build prompt
        trajectory_text = format_trajectory_for_prompt(trajectory)
        prompt = PROMPT_TEMPLATE.format(trajectory_json=trajectory_text)

        # Generate response using chats
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": 0.1,
                "max_output_tokens": 2048
            }
        )

        # Parse JSON from response
        response_text = response.text if hasattr(response, 'text') else str(response)

        # Extract JSON
        json_str = extract_json(response_text)
        if not json_str:
            print(f"  Warning: Could not parse JSON from response")
            return None

        annotation = json.loads(json_str)

        # Add trajectory hash
        annotation["trajectory_hash"] = trajectory.get("trajectory_hash", "")
        annotation["timestamp"] = datetime.now().isoformat()

        return annotation

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_json(text: str) -> Optional[str]:
    """Extract JSON from response text"""
    # Try direct JSON parse first
    try:
        json.loads(text)
        return text
    except:
        pass

    # Try to find JSON in markdown code block
    import re
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()

    # Try to find JSON object pattern
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return match.group(0)

    return None


def annotate_batch(
    batch_file: Path,
    output_file: Path,
    api_key: str,
    model: str = "gemini-2.5-pro-exp-08-07",
    delay: float = 1.0
) -> tuple[int, int]:
    """Annotate entire batch with Gemini"""
    trajectories = load_batch(batch_file)

    print(f"Loaded {len(trajectories)} trajectories from {batch_file}")
    print(f"Output: {output_file}")
    print(f"Model: {model}")
    print()

    total = len(trajectories)
    success = 0
    failed = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, traj in enumerate(trajectories):
            traj_id = traj.get("trajectory_id", f"traj_{i}")
            print(f"[{i+1}/{total}] Annotating: {traj_id[:50]}...")

            annotation = annotate_with_gemini(traj, api_key, model)

            if annotation:
                f.write(json.dumps(annotation, ensure_ascii=False) + '\n')
                success += 1
                print(f"  -> {annotation.get('label', {}).get('type', 'UNKNOWN')}")
            else:
                failed += 1
                print(f"  -> FAILED")

            # Rate limiting
            if i < total - 1:
                time.sleep(delay)

    print()
    print("=" * 60)
    print(f"Annotation complete: {success} success, {failed} failed")
    print(f"Output saved to: {output_file}")

    return success, failed


def main():
    parser = argparse.ArgumentParser(description="Annotate trajectories with Gemini API")
    parser.add_argument("--batch", type=str, required=True,
                       help="Input batch JSON file")
    parser.add_argument("--output", type=str, required=True,
                       help="Output JSONL file")
    parser.add_argument("--api_key", type=str,
                       default="AIzaSyAQ.Ab8RN6JXVO64MAyYST2SodWVZDFKKe8X0BrQzullpLX3MH0Nog",
                       help="Gemini API key")
    parser.add_argument("--model", type=str, default="gemini-2.5-pro-exp-08-07",
                       help="Gemini model to use")
    parser.add_argument("--delay", type=float, default=1.0,
                       help="Delay between requests (seconds)")

    args = parser.parse_args()

    if not GEMINI_AVAILABLE:
        print("Error: google-genai not installed.")
        print("Run: pip install google-genai")
        sys.exit(1)

    batch_file = Path(args.batch)
    if not batch_file.exists():
        print(f"Error: Batch file not found: {batch_file}")
        sys.exit(1)

    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    success, failed = annotate_batch(
        batch_file,
        output_file,
        args.api_key,
        args.model,
        args.delay
    )

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
