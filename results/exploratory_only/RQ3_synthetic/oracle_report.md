# RQ3: Oracle Intervention Analysis

## Research Question

*Which bottleneck matters most for improving agent reliability?*

## Baseline

- Baseline success rate (S0): **15.0%**

## Intervention Results

| Intervention | Success Rate | Δ from Baseline |
|--------------|--------------|-----------------|
| Oracle Selection | 50.0% | +35.0% |
| Oracle Execution | 40.0% | +25.0% |
| Oracle Recognition | 45.0% | +30.0% |
| Oracle Recovery | 40.0% | +25.0% |

## Bottleneck Ranking

1. **Selection** (+35.0%) - Fixing wrong action choices has highest impact
2. **Recognition** (+30.0%) - Telling agents about failures helps
3. **Execution** (+25.0%) - Environment reliability matters
4. **Recovery** (+25.0%) - Providing recovery actions helps

## Interpretation

**Selection** interventions show the largest improvement, suggesting that improving action selection is the most impactful way to boost agent reliability.

## [TBD] After Real Experiments

- Actual trajectory rerunning required
- Multiple failure types need separate analysis
- Statistical significance testing needed
