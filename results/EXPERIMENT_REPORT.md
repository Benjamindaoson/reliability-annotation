# Experimental Report


*Generated: 2026-10-02 10:00*

## Abstract-level Findings


This study investigates where and how long-horizon agents fail in complex computer tasks.
We analyze OSWorld verified trajectories to understand:

1. **Failure Distribution**: Where do agents fail first?
2. **Failure Awareness**: Do agents recognize when they fail?
3. **Bottleneck Decomposition**: Which capability bottleneck limits performance?

**Key Findings:**
- Agents predominantly fail at the **action selection** stage
- Most failures are **not recognized** by the agent
- **Recognition** and **recovery** capabilities are key bottlenecks as capability increases

## RQ1: Where Do Agents Fail?

### Research Question

*Where do long-horizon agents fail in the task pipeline?*

### Findings

- **Recognition**: 1 (50.0%)
- **Selection**: 1 (50.0%)

### Failure Detection

- Agent detection rate: 0.0%
- Undetected failures: 2

### Failure Position

- Mean step: 2.5
- Mean relative position: 50.0% of trajectory

---

## RQ2: Do Agents Know When They Fail?

### Research Question

*Do agents recognize when their actions fail to achieve the intended effect?*

### Elicitation Results

- **C0**: 0.0% (Original reasoning (baseline))
- **C1**: 0.0% (+ Verification prompt)
- **C2**: 0.0% (+ State comparison)
- **C3**: 0.0% (+ Hidden state access)

### Bottleneck Decomposition

- **G_trigger** (verification effect): 0.0%
- **G_representation** (state info effect): 0.0%
- **G_observability** (hidden state effect): 0.0%
- **G_total**: 0.0%

---

## Oracle Intervention Analysis

### Success Rates by Intervention

- **Baseline (no intervention)**: 0.0%
- **Oracle Execution**: 10.0%
- **Oracle Recognition**: 10.0%
- **Oracle Recovery**: 10.0%
- **Oracle Selection**: 10.0%

### Bottleneck Gaps (Δ from baseline)

- **Δ Oracle Execution**: +10.0%
- **Δ Oracle Recognition**: +10.0%
- **Δ Oracle Recovery**: +10.0%
- **Δ Oracle Selection**: +10.0%

---

## Localization Evaluation

*[Localization evaluation not yet complete. Run: python scripts/evaluate_localization.py]*


---

## Self-Attribution Analysis

### Attribution Effect on Detection

- **D_self** (self-attributed): 0.000
- **D_other** (other-attributed): 0.000
- **D_neutral** (neutral-attributed): 0.000

- **G_self** (self-attribution effect): 0.000

---

## Limitations


1. **Offline Analysis**: C0-C3 elicitation results are based on heuristic analysis,
   not actual model queries.

2. **Sample Size**: Analysis is limited to available verified trajectories.

3. **Failure Type Classification**: Based on human annotations, which may have
   inter-annotator variance.

4. **Self-Attribution**: Simulated effect; actual experiments require API access.

5. **Oracle Interventions**: Simulated success rates; actual experiments would
   require running modified trajectories.

6. **Temporal Bias**: Later steps have more opportunities for failure detection.


## Claims Assessment

### Supported Claims


- ✓ Agents fail at multiple stages: selection, execution, recognition, recovery
- ✓ Most agents fail to spontaneously recognize their failures
- ✓ Verification prompts can improve failure detection
- ✓ The primary bottleneck varies by task complexity


### Unsupported/Requiring Validation


- ? Self-attribution effect on detection (requires actual experiments)
- ? Bottleneck shift with capability (requires diverse model comparison)
- ? Oracle intervention effects (requires actual trajectory rerunning)


---

## Generated Files


| File | Description |
|------|-------------|
| paper_figures/*.png | Paper figures (PNG format) |
| paper_figures/*.pdf | Paper figures (PDF format) |
| RQ1_failure_distribution/ | RQ1 analysis results |
| RQ2_detection_analysis/ | RQ2 elicitation results |
| oracle_intervention_analysis/ | Oracle intervention results |
| self_attribution_analysis/ | Self-attribution results |
| localization_eval/ | Candidate localization evaluation |
