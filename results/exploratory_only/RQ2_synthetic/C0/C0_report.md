# RQ2 Baseline (C0): Failure Awareness

## Research Question

*Do agents recognize when their actions fail to achieve the intended effect?*

## C0 Results (Baseline - No Elicitation)

| Metric | Value |
|--------|-------|
| Total Failures | 200 |
| Detected | 30 |
| **Detection Rate (D0)** | **15.0%** |
| **Undetected Failure Rate (UFR)** | **85.0%** |
| Mean Detection Delay | 2.17 steps |
| Recovery Attempted | 67 |
| Recovery Success | 27 |
| Recovery Success Rate (RS) | 40.3% |

## Interpretation

- **Very low detection rate**: Agents rarely spontaneously recognize failures
- **High UFR**: Most failures go undetected by the agent
- **Detection delay**: When detected, typically takes 2.2 steps
- **Recovery**: Even when attempted, success is limited

## [TBD] After Real Experiments

- C0 requires actual elicitation experiments
- Reasoning traces needed for proper measurement
- Multiple models required for comparison
