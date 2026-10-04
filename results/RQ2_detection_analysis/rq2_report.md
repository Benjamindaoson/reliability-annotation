# RQ2: Do Agents Know When They Fail?

## Research Question

*Do agents recognize when their actions fail to achieve the intended effect?*

## Summary

- Total failures analyzed: 2

## Detection Rate by Elicitation Condition

| Condition | Description | Detection Rate |
|-----------|-------------|----------------|
| C0 | Original reasoning (baseline) | 0.0% |
| C1 | + Verification prompt | 0.0% |
| C2 | + State comparison | 0.0% |
| C3 | + Hidden state access | 0.0% |

## Bottleneck Decomposition

| Gain Component | Value | Interpretation |
|----------------|-------|----------------|
| G_trigger | 0.0% | Detection triggered by prompt |
| G_representation | 0.0% | Detection improved by state info |
| G_observability | 0.0% | Detection improved by hidden state |
| G_total | 0.0% | Total detection gap |

## Interpretation

- **Minor trigger gap**: Most agents attempt self-verification
- **Minor representation gap**: State comparison is generally effective
- **Minor observability gap**: Observable state is sufficient for detection
