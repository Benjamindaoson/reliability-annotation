# Paper Status Report

**Generated: 2026-10-02**

## Human-Grounded Validation Phase Status

---

## Phase 28: Synthetic Invalidation

✅ COMPLETE
- Created `results/synthetic_status.md` documenting synthetic limitations
- Moved synthetic results to `results/exploratory_only/`
- All paper claims must be regenerated from human annotations

---

## Phase 29: Annotation Interface Upgrade

✅ COMPLETE
- Upgraded `annotation_tool/app.py` for human-grounded validation
- New schema: SELECTION/EXECUTION/RECOGNITION/RECOVERY
- Added detection evidence requirement
- Added causal window visualization
- Added recovery attempt tracking

---

## Phase 30: Quality Control

✅ READY (requires annotations)
- `scripts/phase30_annotation_qc.py` implemented
- Checks: missing labels, invalid types, detection timing
- Generates `results/human_annotation_qc.md`

---

## Phase 31: Inter-Annotator Agreement

✅ READY (requires annotations)
- `scripts/phase31_inter_annotator.py` implemented
- Cohen's Kappa for failure type
- Binary Kappa for detection
- Step localization MAE

---

## Phase 32: RQ1 with Human Labels

✅ FRAMEWORK READY
- `scripts/phase32_regenerate_rq1.py` implemented
- Generates `results/RQ1_human/` with:
  - Failure distribution table
  - By-model breakdown
  - By-trajectory-length breakdown
  - Detection statistics (D0, UFR)

**STATUS**: Awaiting human annotations

---

## Phase 33: Reliability Profile

✅ FRAMEWORK READY
- `scripts/phase33_reliability_profile.py` implemented
- Computes: A, UFR, D0, DD, RS
- Generates `results/reliability_human/`

**STATUS**: Awaiting human annotations

---

## Phase 34: RQ2 Real Experiment

✅ DESIGN READY
- `scripts/phase34_38_real_experiments.py` implemented
- Selects 40 high-priority cases
- Creates experiment protocol for C0-C3

**BLOCKER**: Requires API access

---

## Phase 35: Self-Attribution Experiment

✅ DESIGN READY
- Experiment protocol created
- Self/Other/Neutral conditions

**BLOCKER**: Requires API access

---

## Phase 36: Oracle Experiments

✅ DESIGN READY
- `scripts/oracle_runner.py` created
- Four intervention types

**BLOCKER**: Requires OSWorld environment access

---

## Phase 37: Paper Regeneration

✅ PARTIAL
- `paper/results_human.md` created (template)
- `paper/paper_status.md` this file

**STATUS**: Awaiting human annotations

---

## Phase 38: Integrity Check

✅ COMPLETE
- `results/RESULT_TRACEABILITY.md` created
- Documents every claim's evidence source
- Pipeline commands documented

---

## Current Data Status

| Metric | Value |
|--------|-------|
| Total Trajectories | 200 |
| Human Annotated | 0 |
| Synthetic (pipeline test only) | 200 |

---

## What Paper 1 Needs

### For RQ1 (Where do agents fail?)
- [ ] 50+ human annotations
- [ ] Failure type distribution
- [ ] Detection rate (D0, UFR)

### For RQ2 (Do agents know when they fail?)
- [ ] 30-50 annotated recognition/execution failures
- [ ] API access for C0-C3 elicitation
- [ ] Detection rate measurements

### For RQ3 (Which bottleneck matters?)
- [ ] OSWorld environment access
- [ ] Trajectory rerunning capability
- [ ] Oracle intervention results

---

## Key Scientific Question

**If human annotations confirm:**
- UFR >> 0 (agents don't detect most failures)
- Selection failures dominate

**Then Paper 1 thesis is supported.**

---

## Next Immediate Action

```bash
# Launch annotation tool
streamlit run annotation_tool/app.py

# Annotate minimum 50 trajectories
# Then run analysis:
python scripts/phase32_regenerate_rq1.py
```

---

*End of status report*
