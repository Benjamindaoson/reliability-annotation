# Dataset Inventory

## Summary

| Metric | Value |
|--------|-------|
| Total Trajectories | 200 |
| Unique Models | 1 |
| Unique Tasks | 200 |
| Total Steps | 3000 |
| Avg Trajectory Length | 15.0 |

## Models

| claude-4-sonnet-20250514 | 200 |

## Trajectory Length Distribution

| 15 | 200 |

## Action Types

| left_click | 1289 |
| key | 614 |
| type | 443 |
| scroll | 206 |
| screenshot | 173 |
| triple_click | 64 |
| double_click | 61 |
| left_click_drag | 51 |
| wait | 47 |
| right_click | 36 |

## Feedback Statistics

| Metric | Count |
|--------|-------|
| Successful steps | 0 |
| Non-zero reward | 0 |
| State changed | 0 |

## Data Availability

| Data Type | Available |
|-----------|-----------|
| Reasoning traces | **NOT AVAILABLE** |
| Evaluator signals | **NOT AVAILABLE** |
| Screenshots | Available |
| Action history | Available |
| Feedback signals | Available |

## Limitations

1. **No reasoning traces**: Model reasoning is not available in this dataset
2. **No evaluator signals**: Ground-truth task completion signals are not provided
3. **Single model**: Only Claude-4-Sonnet trajectories available
4. **Synthetic annotations needed**: Failure annotations require human labeling

## Implications for Analysis

- RQ2 (Failure Awareness): **Cannot be measured directly** - requires reasoning traces
- RQ1 (Failure Distribution): **Can infer from feedback patterns**
- RQ3 (Oracle Intervention): **Requires annotated failures**
