# Result Traceability Report

**Audit Date:** 2026-10-02

This document traces every numerical claim in `results/paper1_results_report.md` back to its source.

---

## RQ1 Claims

### Claim: RECOGNITION 68.7%, RECOVERY 20.8%, SELECTION 10.5%

| Field | Value |
|-------|-------|
| **Evidence:** | `{RECOGNITION: 248, RECOVERY: 75, SELECTION: 38} / 361` |
| **Source CSV:** | `results/analysis/rq1_by_task_type.csv` |
| **Generation Script:** | `scripts/analyze_results.py` |
| **Annotation Source:** | `data/human_annotations/auto_annotations.jsonl` (heuristic) |
| **Evidence Quality:** | ❌ **Unsupported** (automatic annotation, not human-validated) |

### Claim: RECOGNITION ranges from 54% (os) to 96% (vs_code)

| Field | Value |
|-------|-------|
| **Evidence:** | Per-task failure type counts from auto_annotations.jsonl |
| **Source:** | Calculated in `scripts/analyze_results.py` |
| **Evidence Quality:** | ❌ **Unsupported** (same annotation source) |

---

## RQ2 Claims

### Claim: Average Detection Rate 16.9%

| Field | Value |
|-------|-------|
| **Evidence:** | Derived from RECOVERY count / total |
| **Calculation:** | `75 / 361 = 20.8%` (this is the recovery rate, not detection rate) |
| **Source:** | `scripts/analyze_results.py` |
| **Annotation Source:** | `auto_annotations.jsonl` |
| **Evidence Quality:** | ❌ **Unsupported** |
| **Note:** | The claim conflates "RECOVERY" with "detected". RECOVERY means agent tried to recover (implies detection), but detection rate cannot be directly measured from action patterns alone. |

### Claim: vs_code has lowest detection rate (4.3%)

| Field | Value |
|-------|-------|
| **Evidence:** | RECOVERY count / total for vs_code task type |
| **Source:** | `scripts/analyze_results.py` |
| **Evidence Quality:** | ❌ **Unsupported** |

---

## RQ3 Claims

### Claim: RECOGNITION has highest potential improvement (68.7%)

| Field | Value |
|-------|-------|
| **Evidence:** | Proportion of RECOGNITION failures |
| **Source:** | `scripts/analyze_results.py` |
| **Annotation Source:** | `auto_annotations.jsonl` |
| **Evidence Quality:** | ❌ **Unsupported** |
| **Critical Issue:** | **No oracle intervention was actually executed.** RQ3 requires controlled experiments where each bottleneck is removed. This is purely hypothetical projection. |

---

## Dataset Claims

### Claim: 361 trajectories from Claude-4-Sonnet on OSWorld

| Field | Value |
|-------|-------|
| **Evidence:** | Count of traj.jsonl files found |
| **Source:** | `DATA_DIR` = `data/external/osworld_verified/claude-4-sonnet-15steps/claude-4-sonnet-20250514-15steps` |
| **Evidence Quality:** | ✅ **Validated** (verified file count) |

### Claim: Final Success Rate 0%

| Field | Value |
|-------|-------|
| **Evidence:** | `final_result` field = "failure" for all 361 trajectories |
| **Source:** | `auto_annotations.jsonl` |
| **Evidence Quality:** | ✅ **Validated** (data observation) |

---

## Summary: Evidence Quality Matrix

| Claim | Evidence Quality | Reason |
|-------|-----------------|--------|
| 361 trajectories | ✅ Validated | Verified file count |
| 0% success rate | ✅ Validated | Data observation |
| RECOGNITION 68.7% | ❌ Unsupported | Heuristic annotation |
| RECOVERY 20.8% | ❌ Unsupported | Heuristic annotation |
| SELECTION 10.5% | ❌ Unsupported | Heuristic annotation |
| Detection rate by task | ❌ Unsupported | Heuristic + conflation |
| RQ3 headroom analysis | ❌ Unsupported | No oracle intervention |

---

## Missing Evidence

| RQ | Required Evidence | Current Status |
|----|-------------------|----------------|
| RQ1 | Human-labeled failure types | ❌ Not available |
| RQ2 | Agent detection evidence (reasoning traces) | ❌ Not available in data |
| RQ3 | Oracle intervention results | ❌ Not executed |

---

*This document is part of the Paper 1 Evidence Audit.*
