# Paper Claim Audit

**Audit Date:** 2026-10-02

This document audits the scientific validity of claims made in the Paper 1 research plan and results report.

---

## RQ1: "Where do agents fail?"

### Paper Claim
> The first consequential failure most commonly falls into the RECOGNITION category (68.7%), meaning agents fail without realizing it.

### Evidence Required
- Human-annotated failure type labels
- Inter-annotator agreement statistics
- Ground truth validation

### Current Evidence
- Rule-based heuristic labels from `auto_annotate.py`
- No human validation
- No agreement metrics

### Audit Verdict
| Aspect | Status |
|--------|--------|
| Metric computation | ✅ Validated |
| Failure type labels | ❌ **INVALID** |
| Human grounding | ❌ **MISSING** |

### Risk if published
**HIGH RISK** - A reviewer could challenge that heuristic labels are not "human-grounded failure decomposition."

---

## RQ2: "Do agents know when they fail?"

### Paper Claim
> Agents fail to detect their own failures in 68.7% of cases. Average detection rate is 16.9%.

### Evidence Required
- Explicit detection evidence from agent reasoning
- OR: Human annotation of whether agent detected failure
- RQ2 cascade protocol results (C0-C3 conditions)

### Current Evidence
- Detection inferred from "RECOVERY" label (agent tried to recover → must have detected)
- **Conflation error**: RECOVERY ≠ detected. Agent might retry for other reasons.
- No actual reasoning traces in the data
- No C0-C3 cascade experiment executed

### Audit Verdict
| Aspect | Status |
|--------|--------|
| Detection measurement | ❌ **INVALID** |
| C0-C3 protocol | ❌ **NOT EXECUTED** |
| Reasoning traces | ❌ **NOT AVAILABLE** |

### Risk if published
**CRITICAL RISK** - The data format (OSWorld trajectory) does not include agent reasoning traces. We cannot measure "detection" from action sequences alone.

---

## RQ3: "Which bottleneck matters most?"

### Paper Claim
> RECOGNITION has the highest improvement potential (68.7%), followed by RECOVERY (20.8%).

### Evidence Required
- Oracle intervention experiments
- Controlled removal of each bottleneck type
- Comparison of task success rate with/without each intervention

### Current Evidence
- **NONE** - No oracle interventions were executed
- The claim is purely hypothetical projection based on failure type counts
- The paper's own protocol (Section 8) specifies oracle triggers and interventions that were never run

### Audit Verdict
| Aspect | Status |
|--------|--------|
| Oracle Selection | ❌ **NOT EXECUTED** |
| Oracle Execution | ❌ **NOT EXECUTED** |
| Oracle Recognition | ❌ **NOT EXECUTED** |
| Oracle Recovery | ❌ **NOT EXECUTED** |
| Causal headroom measurement | ❌ **NOT MEASURED** |

### Risk if published
**EXTREME RISK** - This is the central claim of the paper and it has zero empirical support. RQ3 requires active intervention experiments that were never conducted.

---

## Additional Claim: "0% Success Rate"

### Paper Claim
> All 361 trajectories resulted in failure.

### Evidence Required
- Trajectory outcome data (success/failure)

### Current Evidence
- Verified from `auto_annotations.jsonl` `final_result` field

### Audit Verdict
| Aspect | Status |
|--------|--------|
| Success rate measurement | ✅ **Validated** |

---

## Summary: Claim Validity

| Claim | Valid for Publication? | Action Required |
|-------|----------------------|-----------------|
| 361 trajectories | ✅ Yes | None |
| 0% success rate | ✅ Yes | None |
| RECOGNITION is dominant | ❌ No | Human annotation + validation |
| Detection rate 16.9% | ❌ No | Reasoning traces + cascade experiment |
| RECOGNITION headroom 68.7% | ❌ No | Oracle intervention execution |
| Bottleneck shift hypothesis | ⚠️ Partial | Exploratory evidence only |

---

## Critical Gaps

1. **No human annotations** - The paper claims "human-grounded" but uses heuristic labels
2. **No reasoning traces** - RQ2 cannot be answered without agent reasoning data
3. **No oracle interventions** - RQ3 cannot be answered without intervention experiments
4. **No C0-C3 cascade** - The research plan specifies experiments never executed

---

## Recommendations

### Minimum for Exploratory Paper
- Retitle as "Preliminary Failure Analysis" or "Exploratory Study"
- Report findings as "heuristic-annotated analysis" not "human-grounded"
- Add explicit limitation section
- Frame as pilot study guiding future human annotation

### Required for Full Paper
1. Execute human annotation on ≥100 trajectories
2. Calculate inter-annotator agreement (Cohen's κ ≥ 0.8)
3. Obtain reasoning traces or conduct think-aloud protocol
4. Execute oracle intervention experiments for RQ3
5. Re-run C0-C3 cascade protocol for RQ2

---

*This document is part of the Paper 1 Evidence Audit.*
