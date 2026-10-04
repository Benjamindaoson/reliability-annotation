# Oracle Intervention Analysis

## Methodology


Oracle interventions simulate ideal assistance at each bottleneck:

| Intervention | Description | When Effective |
|--------------|-------------|-----------------|
| S0 (Baseline) | No intervention | - |
| S_selection | Correct wrong action | Selection failures |
| S_execution | Force intended execution | Execution failures |
| S_recognition | Tell failure occurred | Recognition failures |
| S_recovery | Provide recovery action | Recovery failures |

**Note**: This is a simulation framework. Actual results require running interventions.

## Success Rates

| Intervention | Success Rate | Δ from Baseline |
|--------------|-------------|-----------------|
| s0 | 0.0% | +0.0% |
| s_execution | 10.0% | +10.0% |
| s_recognition | 10.0% | +10.0% |
| s_recovery | 10.0% | +10.0% |
| s_selection | 10.0% | +10.0% |

## Bottleneck Ordering

| Rank | Bottleneck | Δ Success Rate |
|------|------------|---------------|
| 1 | s_selection | +10.0% |
| 2 | s_execution | +10.0% |
| 3 | s_recognition | +10.0% |
| 4 | s_recovery | +10.0% |

## Interpretation

- **Primary bottleneck**: s_selection (Δ = +10.0%)
- **Secondary bottleneck**: s_execution (Δ = +10.0%)

**Implication**: Improving oracle intervention at the primary bottleneck
would yield the largest improvement in overall success rate.
