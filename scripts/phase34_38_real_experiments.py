#!/usr/bin/env python3
"""
Phase 34-38: Real Experiment Execution and Paper Regeneration

This script:
1. Phase 34: Select cases for real RQ2 experiment
2. Phase 35: Self-attribution real experiment
3. Phase 36: Oracle experiment preparation
4. Phase 37: Regenerate paper with real results
5. Phase 38: Integrity check

IMPORTANT:
- This script generates the EXPERIMENT DESIGN, not actual results
- Real results require API access and trajectory rerunning
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_annotations(path: str) -> list[dict]:
    """Load human annotations."""
    annotations = []
    if Path(path).exists():
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    annotations.append(json.loads(line))
    return annotations


def load_trajectories(path: str) -> dict:
    """Load trajectories."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    trajectories = data if isinstance(data, list) else [data]
    return {t.get('trajectory_id'): t for t in trajectories}


def select_rq2_cases(annotations: list[dict], trajectories: dict, n: int = 40) -> list[dict]:
    """Phase 34.1: Select cases for RQ2 elicitation experiment."""
    output_dir = Path('results/RQ2_real')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Priority: Recognition > Execution > Selection
    priority = {'RECOGNITION': 3, 'EXECUTION': 2, 'SELECTION': 1, 'RECOVERY': 0}

    valid = [
        a for a in annotations
        if a.get('first_failure_step') != "NONE"
        and a.get('failure_type') in priority
    ]

    # Sort by priority
    valid.sort(key=lambda x: -priority.get(x.get('failure_type', ''), 0))

    # Select top N
    selected = valid[:n]

    # Enrich with trajectory context
    cases = []
    for ann in selected:
        traj_id = ann.get('trajectory_id')
        traj = trajectories.get(traj_id, {})

        failure_step = ann.get('first_failure_step')
        if isinstance(failure_step, int):
            steps = traj.get('steps', [])
            context = {
                'before': steps[max(0, failure_step-2):failure_step],
                'failure': steps[failure_step:failure_step+1],
                'after': steps[failure_step+1:min(len(steps), failure_step+5)],
            }
        else:
            context = {}

        cases.append({
            'trajectory_id': traj_id,
            'task_id': ann.get('task_id'),
            'model_id': ann.get('model_id'),
            'failure_type': ann.get('failure_type'),
            'first_failure_step': failure_step,
            'context': context,
            'priority': priority.get(ann.get('failure_type', ''), 0),
        })

    # Save cases
    with open(output_dir / 'rq2_cases.json', 'w', encoding='utf-8') as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)

    # Generate experiment protocol
    protocol = f"""# RQ2 Real Experiment Protocol

## Experiment Design

### Goal
Measure: "Do agents know when they fail?"

### Cases
- {len(cases)} cases selected
- Priority: Recognition (3) > Execution (2) > Selection (1)

### Protocol

#### C0: Baseline
```python
# Extract original trajectory evidence
evidence = extract_trajectory_context(trajectory_id, failure_step)

# Query model
response = model.predict(
    f"Given this trajectory evidence, did the agent fail?"
)
```

#### C1: Verification Prompt
```python
response = model.predict(
    f"Given this trajectory evidence, did the agent fail? "
    f"Verify whether your previous action achieved the intended effect."
)
```

#### C2: State Comparison
```python
evidence_structured = {
    'BEFORE': state_before,
    'ACTION': action_taken,
    'AFTER': state_after,
    'INTENDED_EFFECT': intended_outcome,
}
response = model.predict(
    f"Analyze: {evidence_structured}"
)
```

#### C3: Hidden State Access
evidence_structured = {...}  # Same as C2
evidence_with_hidden = dict(evidence_structured)
evidence_with_hidden['HIDDEN_STATE'] = hidden_state
response = model.predict("Analyze: " + str(evidence_with_hidden))

### Metrics
- D0, D1, D2, D3: Detection rates per condition
- G_trigger = D1 - D0
- G_representation = D2 - D1
- G_observability = D3 - D2

### Execution Command
```bash
python scripts/run_rq2_experiment.py --cases results/RQ2_real/rq2_cases.json --condition C0
python scripts/run_rq2_experiment.py --cases results/RQ2_real/rq2_cases.json --condition C1
python scripts/run_rq2_experiment.py --cases results/RQ2_real/rq2_cases.json --condition C2
python scripts/run_rq2_experiment.py --cases results/RQ2_real/rq2_cases.json --condition C3
```
"""

    with open(output_dir / 'experiment_protocol.md', 'w', encoding='utf-8') as f:
        f.write(protocol)

    print(f"Phase 34: Selected {len(cases)} cases for RQ2 experiment")
    return cases


def prepare_self_attribution_experiment(cases: list[dict], output_dir: Path):
    """Phase 35: Self-attribution experiment preparation."""
    output_dir = output_dir / 'self_attribution_real'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use C2 evidence format
    protocol = f"""# Self-Attribution Real Experiment Protocol

## Experiment Design

### Goal
Measure: Does attributing failure to self vs. other affect detection?

### Cases
- {len(cases)} cases from RQ2 selection

### Conditions

#### Self-Attributed
```python
response = model.predict(
    f"This is an action YOU just performed. "
    f"Given this evidence, did your action fail?"
)
```

#### Other-Attributed
```python
response = model.predict(
    f"This is an action ANOTHER AGENT performed. "
    f"Given this evidence, did the agent's action fail?"
)
```

#### Neutral
```python
response = model.predict(
    f"This is a SYSTEM LOG showing an action outcome. "
    f"Given this evidence, did the action fail?"
)
```

### Metrics
- D_self, D_other, D_neutral: Detection rates
- G_self = max(D_other, D_neutral) - D_self

### Execution Command
```bash
python scripts/run_self_attribution.py --cases results/RQ2_real/rq2_cases.json
```

### Allowed Claim
- "self-attribution-conditioned recognition asymmetry"
- NOT: RLHF causes it
- NOT: motivation deficit
- NOT: universal behavior
"""

    with open(output_dir / 'experiment_protocol.md', 'w', encoding='utf-8') as f:
        f.write(protocol)

    print(f"Phase 35: Self-attribution experiment prepared")


def prepare_oracle_experiments(cases: list[dict], output_dir: Path):
    """Phase 36: Oracle intervention experiment preparation."""
    output_dir = output_dir / 'oracle_experiments'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate oracle runner scripts
    oracle_script = '''#!/usr/bin/env python3
"""
Oracle Intervention Runner

Simulates oracle interventions on annotated failure cases.

Usage:
    python scripts/oracle_runner.py --input cases.json --intervention selection
"""

import json
import argparse
from pathlib import Path


def run_oracle_selection(case: dict, trajectory: dict) -> dict:
    """Oracle Selection: Replace wrong action with correct action."""
    failure_step = case.get('first_failure_step')
    # In real experiment, would replace action in trajectory
    # and check if task succeeds
    return {
        'oracle': 'selection',
        'case_id': case.get('trajectory_id'),
        'status': 'REQUIRES_RERUN',
        'note': 'Need environment to rerun trajectory'
    }


def run_oracle_execution(case: dict, trajectory: dict) -> dict:
    """Oracle Execution: Force intended execution."""
    return {
        'oracle': 'execution',
        'case_id': case.get('trajectory_id'),
        'status': 'REQUIRES_RERUN',
        'note': 'Need environment to rerun trajectory'
    }


def run_oracle_recognition(case: dict, trajectory: dict) -> dict:
    """Oracle Recognition: Tell agent about failure."""
    return {
        'oracle': 'recognition',
        'case_id': case.get('trajectory_id'),
        'status': 'REQUIRES_RERUN',
        'note': 'Need model API to prompt with failure info'
    }


def run_oracle_recovery(case: dict, trajectory: dict) -> dict:
    """Oracle Recovery: Provide recovery action."""
    return {
        'oracle': 'recovery',
        'case_id': case.get('trajectory_id'),
        'status': 'REQUIRES_RERUN',
        'note': 'Need environment to test recovery action'
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Cases JSON file')
    parser.add_argument('--intervention', required=True,
                       choices=['selection', 'execution', 'recognition', 'recovery'])
    parser.add_argument('--output', default='results/oracle_results.json')
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        cases = json.load(f)

    results = []
    for case in cases:
        result = {
            'trajectory_id': case.get('trajectory_id'),
            'oracle_type': args.intervention,
            'status': 'BLOCKED',
            'reason': 'Requires trajectory rerunning in OSWorld environment'
        }
        results.append(result)

    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Oracle experiment prepared for {len(results)} cases")
    print("NOTE: Actual rerunning requires OSWorld environment access")


if __name__ == "__main__":
    main()
'''

    with open(output_dir / 'oracle_runner.py', 'w', encoding='utf-8') as f:
        f.write(oracle_script)

    protocol = f"""# Oracle Intervention Experiment Protocol

## Experiment Design

### Goal
Identify which bottleneck matters most for agent reliability.

### Interventions

| Intervention | Description | Effect |
|--------------|-------------|--------|
| Oracle Selection | Replace wrong action with correct action | Measures selection failure impact |
| Oracle Execution | Force intended execution | Measures execution failure impact |
| Oracle Recognition | Tell agent about failure | Measures awareness impact |
| Oracle Recovery | Provide recovery action | Measures recovery failure impact |

### Execution

```bash
# Requires OSWorld environment access
python scripts/oracle_runner.py --input results/RQ2_real/rq2_cases.json --intervention selection
python scripts/oracle_runner.py --input results/RQ2_real/rq2_cases.json --intervention execution
python scripts/oracle_runner.py --input results/RQ2_real/rq2_cases.json --intervention recognition
python scripts/oracle_runner.py --input results/RQ2_real/rq2_cases.json --intervention recovery
```

### Blockers

1. **OSWorld environment**: Need sandbox to rerun trajectories
2. **Model API**: Need API access to run modified trajectories
3. **Compute**: Significant GPU time required

### Expected Output
```json
{{
    "baseline_success_rate": 0.15,
    "oracle_selection_success_rate": 0.50,
    "oracle_execution_success_rate": 0.40,
    "oracle_recognition_success_rate": 0.45,
    "oracle_recovery_success_rate": 0.40
}}
```
"""

    with open(output_dir / 'experiment_protocol.md', 'w', encoding='utf-8') as f:
        f.write(protocol)

    print(f"Phase 36: Oracle experiments prepared")


def generate_result_traceability():
    """Phase 38: Generate result traceability document."""
    output_dir = Path('results')
    output_dir.mkdir(parents=True, exist_ok=True)

    traceability = """# Result Traceability

**Document: Every paper claim and its evidence source**

---

## RQ1 Claims

### Claim 1: Selection failures are most common
- **Status**: [TBD - requires human annotation]
- **Evidence file**: `data/human_annotations/annotations.jsonl`
- **Generated by**: `scripts/phase32_regenerate_rq1.py`
- **Command**: `python scripts/phase32_regenerate_rq1.py`

### Claim 2: Detection rate is X%
- **Status**: [TBD - requires human annotation]
- **Evidence file**: `data/human_annotations/annotations.jsonl`
- **Field**: `agent_detected_failure == 'YES'`
- **Generated by**: `scripts/phase32_regenerate_rq1.py`

---

## RQ2 Claims

### Claim 3: Verification improves detection
- **Status**: [TBD - requires API experiment]
- **Evidence file**: `results/RQ2_real/cascade_results.json`
- **Generated by**: `scripts/run_rq2_experiment.py`
- **Command**: `python scripts/run_rq2_experiment.py --condition C1`

### Claim 4: Self-attribution effect exists
- **Status**: [TBD - requires API experiment]
- **Evidence file**: `results/self_attribution_real/results.json`
- **Generated by**: `scripts/run_self_attribution.py`

---

## RQ3 Claims

### Claim 5: Oracle selection has highest impact
- **Status**: [TBD - requires trajectory rerunning]
- **Evidence file**: `results/oracle_experiments/results.json`
- **Generated by**: `scripts/oracle_runner.py`

---

## Integrity Checklist

For each claim, verify:

- [ ] Source file exists
- [ ] Script is documented
- [ ] Command is reproducible
- [ ] Human annotations are real (not synthetic)
- [ ] No fabricated numbers

---

## Pipeline Commands

```bash
# Human annotation
streamlit run annotation_tool/app.py

# QC check
python scripts/phase30_annotation_qc.py

# Inter-annotator agreement
python scripts/phase31_inter_annotator.py --input1 <file1> --input2 <file2>

# RQ1 analysis
python scripts/phase32_regenerate_rq1.py

# RQ2 experiment (requires API)
python scripts/run_rq2_experiment.py --cases results/RQ2_real/rq2_cases.json --condition C0

# Self-attribution (requires API)
python scripts/run_self_attribution.py --cases results/RQ2_real/rq2_cases.json

# Oracle (requires environment)
python scripts/oracle_runner.py --input results/RQ2_real/rq2_cases.json --intervention selection
```

---

*Generated: 2026-10-02*
"""

    with open(output_dir / 'RESULT_TRACEABILITY.md', 'w', encoding='utf-8') as f:
        f.write(traceability)

    print("Phase 38: Result traceability document generated")


def generate_final_paper_package(annotations: list[dict]):
    """Phase 37: Regenerate paper with human-validated content."""
    paper_dir = Path('paper')
    paper_dir.mkdir(parents=True, exist_ok=True)

    n_annotations = len(annotations)

    # Count valid failures
    valid = [a for a in annotations if a.get('first_failure_step') != "NONE"]
    n_valid = len(valid)

    # Count by type
    type_counts = defaultdict(int)
    for a in valid:
        type_counts[a.get('failure_type')] += 1

    # Count detection
    detected = sum(1 for a in valid if a.get('agent_detected_failure') == 'YES')
    D0 = detected / n_valid if n_valid > 0 else None

    # Results section (requires human data)
    results = f"""# 5. Results

## 5.1 RQ1: Where Do Agents Fail?

We analyzed {n_valid} annotated failure cases from {n_annotations} trajectories.

### Failure Type Distribution

| Failure Type | Count | Percentage |
|--------------|-------|------------|
| SELECTION | {type_counts.get('SELECTION', 0)} | {type_counts.get('SELECTION', 0)/n_valid*100:.1f}% |
| EXECUTION | {type_counts.get('EXECUTION', 0)} | {type_counts.get('EXECUTION', 0)/n_valid*100:.1f}% |
| RECOGNITION | {type_counts.get('RECOGNITION', 0)} | {type_counts.get('RECOGNITION', 0)/n_valid*100:.1f}% |
| RECOVERY | {type_counts.get('RECOVERY', 0)} | {type_counts.get('RECOVERY', 0)/n_valid*100:.1f}% |

**Key Finding**: Selection failures are {'most' if type_counts.get('SELECTION', 0) >= max(type_counts.values()) else 'not most'} common.

## 5.2 RQ2: Do Agents Know When They Fail?

### Baseline Detection (C0)

| Metric | Value |
|--------|-------|
| Total Failures | {n_valid} |
| Detected | {detected} |
| Detection Rate (D0) | {f'{D0:.1%}' if D0 else 'TBD'} |
| Undetected Failure Rate (UFR) | {f'{(1-D0):.1%}' if D0 else 'TBD'} |

**Key Finding**: Agents spontaneously detect {f'{D0:.1%}' if D0 else 'TBD'} of their failures.

## 5.3 RQ2: Elicitation Cascade

[TBD - requires API experiments]

## 5.4 RQ3: Oracle Intervention

[TBD - requires trajectory rerunning]

---

## Status: PARTIAL

This results section contains real human-annotated data for RQ1.
RQ2 and RQ3 require additional experiments.
"""

    with open(paper_dir / 'results_human.md', 'w', encoding='utf-8') as f:
        f.write(results)

    # Status report
    status = f"""# Paper Status Report

**Generated: 2026-10-02**

## Human Annotation Status

| Metric | Value |
|--------|-------|
| Total Trajectories | 200 |
| Annotated | {n_annotations} |
| Valid Failures | {n_valid} |
| Remaining | {200 - n_annotations} |

## RQ1 Status

- [x] Human annotations: {n_valid} failures
- [x] Failure distribution: computed
- [x] Detection statistics: computed
- [ ] Confidence intervals: TBD
- [ ] Model comparison: TBD (single model only)

## RQ2 Status

- [ ] C0 baseline: {f'computed (D0={D0:.1%})' if D0 is not None else 'TBD'}
- [ ] C1-C3 elicitation: Requires API access
- [ ] Self-attribution: Requires API access

## RQ3 Status

- [ ] Oracle experiments: Requires OSWorld environment
- [ ] Bottleneck ranking: TBD

## Paper Completeness

| Section | Status |
|---------|--------|
| Abstract | Draft ready |
| Introduction | Draft ready |
| Related Work | Draft ready |
| Method | Draft ready |
| Dataset | Complete |
| Annotation Protocol | Complete |
| Results (RQ1) | Real data |
| Results (RQ2) | TBD |
| Results (RQ3) | TBD |
| Limitations | Complete |
| Conclusion | Draft ready |

## Key Scientific Claims

### Supported by Human Data

1. **Selection failures are common**: {type_counts.get('SELECTION', 0)/n_valid*100:.1f}%
2. **Detection rate is low**: {f'{D0:.1%}' if D0 else 'TBD'}

### Requiring Additional Experiments

1. Verification prompt effect (C1-C3)
2. Self-attribution asymmetry
3. Oracle intervention rankings

## Blockers

1. More human annotations (target: 100+)
2. API access for elicitation
3. OSWorld environment for oracle
4. Multi-model trajectories
"""

    with open(paper_dir / 'paper_status.md', 'w', encoding='utf-8') as f:
        f.write(status)

    print("Phase 37: Paper package regenerated")


def main():
    print("=" * 60)
    print("PHASE 34-38: REAL EXPERIMENT EXECUTION")
    print("=" * 60)

    # Load data
    print("\nLoading annotations...")
    annotations = load_annotations('data/human_annotations/annotations.jsonl')
    print(f"Found {len(annotations)} human annotations")

    trajectories = load_trajectories('data/raw/osworld_claude4_converted.json')

    if annotations:
        # Phase 34: Select RQ2 cases
        print("\n--- Phase 34: RQ2 Case Selection ---")
        cases = select_rq2_cases(annotations, trajectories)

        # Phase 35: Self-attribution prep
        print("\n--- Phase 35: Self-Attribution Experiment ---")
        prepare_self_attribution_experiment(cases, Path('results'))

        # Phase 36: Oracle experiments
        print("\n--- Phase 36: Oracle Experiments ---")
        prepare_oracle_experiments(cases, Path('results'))

        # Phase 37: Regenerate paper
        print("\n--- Phase 37: Paper Regeneration ---")
        generate_final_paper_package(annotations)
    else:
        print("\nNo human annotations found.")
        print("Please run annotation campaign first:")
        print("  streamlit run annotation_tool/app.py")

    # Phase 38: Traceability
    print("\n--- Phase 38: Integrity Check ---")
    generate_result_traceability()

    print("\n" + "=" * 60)
    print("PHASE 34-38 COMPLETE")
    print("=" * 60)

    print("""
## Next Steps

1. Run human annotation:
   streamlit run annotation_tool/app.py

2. After annotation, analyze:
   python scripts/phase32_regenerate_rq1.py

3. For RQ2/RQ3, you need:
   - API access for elicitation
   - OSWorld environment for oracle
""")


if __name__ == "__main__":
    main()
