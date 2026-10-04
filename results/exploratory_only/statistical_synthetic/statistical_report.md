# Statistical Analysis Report

## Methodology

- Bootstrap confidence intervals (n=1000 resamples)
- Paired comparisons where applicable
- Effect sizes reported with 95% CI

## RQ1: Failure Distribution

| Metric | Estimate | 95% CI | Notes |
|--------|----------|--------|-------|
| Selection failure rate | 40.0% | [35.2%, 44.8%] | Most common |
| Execution failure rate | 25.0% | [20.1%, 29.9%] | Second most |
| Recognition failure rate | 25.0% | [20.1%, 29.9%] | Similar to execution |
| Recovery failure rate | 10.0% | [6.8%, 13.2%] | Least common |

## RQ2: Detection Rates

| Condition | Detection Rate | 95% CI | Effect Size |
|-----------|----------------|--------|-------------|
| C0 (Baseline) | 15.0% | [11.2%, 18.8%] | - |
| C1 (+Verification) | 27.0% | [22.4%, 31.6%] | +12.0% |
| C2 (+State) | 35.0% | [29.8%, 40.2%] | +20.0% |
| C3 (+Hidden) | 41.0% | [35.4%, 46.6%] | +26.0% |

### Bottleneck Decomposition

| Bottleneck | Effect | 95% CI |
|------------|--------|--------|
| G_trigger | +12.0% | [7.2%, 16.8%] |
| G_representation | +8.0% | [4.1%, 11.9%] |
| G_observability | +6.0% | [2.8%, 9.2%] |

## Self-Attribution Effect

| Condition | Detection Rate | 95% CI |
|-----------|----------------|--------|
| Self-attributed | 18.0% | [13.8%, 22.2%] |
| Neutral | 25.0% | [20.1%, 29.9%] |
| Other-attributed | 28.0% | [22.8%, 33.2%] |

**G_self = 10.0%** (Other vs Self attribution)

## RQ3: Oracle Intervention

| Intervention | Success Rate | 95% CI | Δ from Baseline |
|--------------|--------------|--------|-----------------|
| Baseline (S0) | 15.0% | [10.8%, 19.2%] | - |
| Oracle Selection | 50.0% | [43.8%, 56.2%] | +35.0% |
| Oracle Execution | 40.0% | [33.8%, 46.2%] | +25.0% |
| Oracle Recognition | 45.0% | [38.8%, 51.2%] | +30.0% |
| Oracle Recovery | 40.0% | [33.8%, 46.2%] | +25.0% |

## Important Notes

1. **All results are simulated** - require actual experiments for validation
2. **Single model** - Claude-4-Sonnet only
3. **Synthetic annotations** - not human-labeled
4. **No multiple comparison correction** - would need Bonferroni/Holm for real analysis

## [TBD] After Real Experiments

- Actual p-values and confidence intervals
- Effect size computation (Cohen's d, odds ratios)
- Power analysis for sample size determination
- Multiple comparison correction
