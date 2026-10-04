# NAACL Submission Readiness Report

**Generated:** 2026-10-02
**Status:** NOT READY FOR SUBMISSION

---

## Executive Summary

Based on the evidence audit, Paper 1 **CANNOT currently be submitted to NAACL** because critical claims lack human-validated evidence.

---

## Confirmed Evidence

Evidence that can be used without qualification:

### 1. Dataset Description
| Item | Status |
|------|--------|
| 361 trajectories from Claude-4-Sonnet on OSWorld | ✅ Confirmed |
| 10 task types | ✅ Confirmed |
| Final success rate: 0% | ✅ Confirmed |

**Usage:** Can be included in dataset description and experimental setup.

---

## Preliminary Evidence

Evidence that suggests a direction but requires validation:

### 1. Failure Type Distribution (Heuristic-Analyzed)
| Finding | Sample Size | Method | Validation Needed |
|---------|-------------|--------|-------------------|
| RECOGNITION: 68.7% | 361 | Heuristic | Human annotation |
| RECOVERY: 20.8% | 361 | Heuristic | Human annotation |
| SELECTION: 10.5% | 361 | Heuristic | Human annotation |

**Usage:** Can frame as "heuristic analysis of 361 trajectories suggests..." with explicit caveat.

### 2. Task Variation in Failure Patterns
| Finding | Sample Size | Method | Validation Needed |
|---------|-------------|--------|-------------------|
| RECOGNITION ranges 54%-96% by task | 361 | Heuristic | Human annotation |

**Usage:** Can be reported as exploratory observation, not confirmed finding.

---

## Unsupported Claims

Claims that **CANNOT** be made without additional evidence:

### 1. RQ1: "Agents fail without realizing it"
| Status | ❌ UNSUPPORTED |
|--------|---------------|
| **Required:** | Human-annotated failure types |
| **Available:** | Heuristic rule-based labels |
| **Gap:** | No ground truth validation |

**Current evidence:** Heuristic labels suggest this pattern, but cannot claim as scientific finding.

### 2. RQ2: "Agents fail to detect their own failures 68.7% of the time"
| Status | ❌ UNSUPPORTED |
|--------|---------------|
| **Required:** | Reasoning traces OR human annotation of detection |
| **Available:** | Action sequences only (no reasoning data) |
| **Gap:** | Cannot measure "detection" without reasoning traces |

**Critical issue:** The OSWorld trajectory data format does not include agent reasoning. We cannot measure whether the agent "knew" it failed.

### 3. RQ3: "RECOGNITION has the highest improvement potential"
| Status | ❌ UNSUPPORTED |
|--------|---------------|
| **Required:** | Oracle intervention experiments |
| **Available:** | None |
| **Gap:** | No interventions were executed |

**Critical issue:** RQ3 requires actively removing each bottleneck type and measuring success rate change. This was never done.

### 4. Hypothesis H: "Reliability bottleneck shifts from action to recognition"
| Status | ⚠️ PREMATURE |
|--------|--------------|
| **Required:** | Cross-capability comparison (weak vs strong agents) |
| **Available:** | Single model only (Claude-4-Sonnet) |
| **Gap:** | Cannot demonstrate "shift" without comparing capability levels |

---

## Required Remaining Work

### Tier 1: Critical (Must Do Before Submission)

| Task | Effort | Current Status |
|------|--------|----------------|
| Human annotation of ≥100 trajectories | 2-4 hours | Not started |
| Inter-annotator agreement (30 trajectories) | 1-2 hours | Not started |
| Validate heuristic labels against human labels | 1 hour | Not done |
| Add explicit limitation statement | 30 min | Not done |

### Tier 2: Important (Should Do for Stronger Paper)

| Task | Effort | Current Status |
|------|--------|----------------|
| Execute RQ2 cascade protocol (C0-C3) | 8-16 hours | Not started |
| Execute oracle interventions (RQ3) | 16-32 hours | Not started |
| Compare across model capabilities | 24-48 hours | No data |

### Tier 3: Nice to Have (For Robustness)

| Task | Effort | Current Status |
|------|--------|----------------|
| Statistical significance tests | 2 hours | Not done |
| Effect size calculations | 1 hour | Not done |
| Ablation studies | 8 hours | Not started |

---

## Submission Options

### Option A: Exploratory Paper (Current Evidence)

**Title:** "Do Agents Know When They Fail? A Preliminary Analysis of Failure Patterns in Long-Horizon Agents"

**Changes:**
1. Rename from "Results" to "Preliminary Findings"
2. Add explicit limitation section on every table/figure
3. Frame heuristic analysis as "initial exploration"
4. State clearly: "These findings are based on heuristic annotation and require human validation"

**NAACL Fit:** May be acceptable as short paper or workshop submission

### Option B: Full Paper (Requires Tier 1 Work)

**Requirements:**
1. Complete human annotation of ≥100 trajectories
2. Achieve inter-annotator agreement κ ≥ 0.8
3. Validate heuristic labels
4. Add limitation statements

**Timeline:** 1-2 weeks additional work

### Option C: Wait for RQ2/RQ3 (Requires Tier 2 Work)

**Requirements:**
1. Execute full RQ2 cascade protocol
2. Execute oracle interventions
3. Cross-model comparison

**Timeline:** 4-8 weeks additional work

---

## Recommendation

**Immediate action:** Proceed with Option A (Exploratory Paper) while planning Option B.

**Justification:** The heuristic analysis reveals a compelling pattern (68.7% RECOGNITION) that strongly motivates further research. Even as preliminary evidence, this is valuable for the research community.

**Key message:** "We found suggestive evidence that failure detection may be the dominant bottleneck, but this requires human validation."

---

## Checklist for Submission

- [ ] Rename paper to indicate preliminary nature
- [ ] Add limitation section to every section with heuristic data
- [ ] Report heuristic methodology explicitly
- [ ] State "human annotation required" in abstract
- [ ] Complete Tier 1 human annotation work
- [ ] Calculate inter-annotator agreement
- [ ] Validate heuristic accuracy

---

*This document is part of the Paper 1 Evidence Audit.*
*Author: Claude Code*
*Date: 2026-10-02*
