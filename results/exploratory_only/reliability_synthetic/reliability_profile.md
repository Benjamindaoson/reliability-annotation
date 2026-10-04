# Reliability Profile: Claude-4-Sonnet

## Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| A (Accuracy) | 65.0% | Action correctness rate |
| UFR | 85.0% | Undetected failure rate |
| DD | 2.5 | Mean detection delay (steps) |
| RS | 40.0% | Recovery success rate |

## Profile Visualization

```
Reliability Profile: Claude-4-Sonnet

Accuracy (A):        █████████████░░░░░░░ 65.0%
Undetected (UFR):    █████████████████░░░ 85.0%
Detection Delay:     2.5 steps
Recovery (RS):       ████████░░░░░░░░░░░░ 40.0%
```

## Key Observations

- High undetected failure rate (85.0%) indicates agents often don't realize when they fail
- Low recovery success (40.0%) suggests difficulty in correcting mistakes
- Moderate detection delay (2.5 steps) when detection occurs

## [TBD] After Real Experiments

- Multiple model comparison
- Capability vs reliability relationship
- Confidence intervals
