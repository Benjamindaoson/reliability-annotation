# Oracle Experiment Blocker Report

## Status: BLOCKED

### Blockers

1. **OSWorld Environment Access**
   - Trajectory rerunning requires OSWorld sandbox
   - Cannot execute oracle interventions without environment
   - Contact: XLang Lab for environment access

2. **Compute Resources**
   - Rerunning trajectories requires significant GPU time
   - Estimate: 50 trajectories × 4 interventions = 200 runs

3. **Action Database**
   - Oracle Selection and Recovery need correct action database
   - Requires manual curation or model generation

### What Oracle Experiments Would Show

| Intervention | Expected Effect | Measures |
|--------------|-----------------|----------|
| Oracle Selection | +35% success | Selection failure impact |
| Oracle Execution | +25% success | Execution failure impact |
| Oracle Recognition | +30% success | Awareness failure impact |
| Oracle Recovery | +25% success | Recovery failure impact |

### How to Unblock

1. Request OSWorld environment access from XLang Lab
2. Set up compute budget for rerunning
3. Create action database for selection/recovery

### Alternative: Simulation

If environment access is unavailable, can simulate oracle effects:
- Use human judgment to estimate intervention outcomes
- Clearly label as "simulated oracle" not "experimental oracle"
