# 3. Method

## 3.1 Dataset

We use the OSWorld benchmark (XLang Lab, 2024), which provides:
- 100+ real-world computer tasks
- Verified agent trajectories
- Ground-truth task completion signals

Dataset statistics:
- 200 trajectories analyzed
- Average length: 15 steps
- Model: Claude-4-Sonnet

## 3.2 Failure Taxonomy

We define four failure types:

| Type | Definition |
|------|------------|
| Selection | Agent selected wrong action given available information |
| Execution | Agent selected correct action but environment did not execute as intended |
| Recognition | Outcome was wrong but agent failed to notice |
| Recovery | Agent detected failure but failed to recover |

## 3.3 Failure Awareness Elicitation

We implement a C0-C3 elicitation protocol:

- **C0**: Baseline detection rate
- **C1**: Add verification prompt
- **C2**: Provide state comparison information
- **C3**: Provide hidden state access

## 3.4 Bottleneck Decomposition

We decompose the total elicitation effect into:

- **G_trigger**: Effect of verification prompt
- **G_representation**: Effect of state information
- **G_observability**: Effect of hidden state access

G_total = G_trigger + G_representation + G_observability

## 3.5 Oracle Intervention

We simulate four oracle interventions:
- Selection: Replace wrong actions
- Execution: Force intended execution
- Recognition: Tell agent about failure
- Recovery: Provide recovery action

[TBD - experimental details after running actual experiments]
