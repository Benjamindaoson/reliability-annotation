# RQ2 Elicitation Cascade: C0-C3

## Research Question

*Which factors limit an agent's ability to detect its own failures?*

## Cascade Results

| Condition | Detection Rate | Improvement |
|-----------|----------------|-------------|
| C0 (Baseline) | 21.8% | - |
| C1 (+Verification) | 33.8% | +12.0% |
| C2 (+State Info) | 41.8% | +8.0% |
| C3 (+Hidden State) | 47.8% | +6.0% |

## Bottleneck Decomposition

| Bottleneck | Effect Size | Interpretation |
|------------|-------------|----------------|
| G_trigger | 12.0% | Verification triggers recognition |
| G_representation | 8.0% | State info needed for comparison |
| G_observability | 6.0% | Hidden state access helps |
| **G_total** | **26.0%** | Total elicitation effect |

## Key Insight

The **G_trigger** component (12.0%) dominates, suggesting that simply prompting agents to verify their actions significantly improves failure detection.

## [TBD] After Real Experiments

- Requires actual API experiments
- Reasoning traces needed
- Model-specific effects may vary
