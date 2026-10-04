# Human Gold Calibration - Current Research Status

**Last Updated:** 2026-10-04

**Current Phase:** E0 — Annotation Calibration / Measurement Tool Validation

---

## Phase Summary

We are currently in **Measurement Tool Validation (E0)**.

The goal of this phase is NOT to obtain paper results. The goal is ONLY to verify:

1. Failure onset can be judged stably
2. First consequential failure can be located stably
3. Selection vs Execution can be distinguished stably
4. Failure recognition can be judged stably
5. Recovery attempt/outcome can be judged stably
6. Ordinary people can use the annotation system correctly

---

## What Has Been Completed

### 1. Schema v3 ✅
- Full migration from old 4-type schema (SELECTION/EXECUTION/RECOGNITION/RECOVERY) to v3
- Recognition and Recovery are now **downstream variables**, not onset mechanisms
- Added gate question: `has_consequential_failure`
- Added evidence tracking and causal analysis
- Full test suite: 20 tests passing

### 2. Migration Script ✅
- `scripts/migrate_annotations_to_v3.py` - converts old annotations to v3
- Heuristic annotations marked with `annotator_type = HEURISTIC`
- Will NOT enter Human Gold

### 3. Chinese Annotation Tool ✅
- `annotation_tool/app_chinese.py` - fully Chinese interface
- Step-by-step wizard design
- No technical jargon visible to annotators
- Auto-save with draft recovery
- Progress tracking

### 4. Human Gold Agreement Analysis ✅
- `scripts/analyze_human_gold_agreement.py`
- Computes Cohen's kappa for mechanism, recognition, recovery
- Computes onset step exact/±1/±2/MAE
- Reports UNCLEAR rates
- Checks calibration gate

---

## What Needs to Be Done

### Phase E0a: Prepare Human Gold 60 (IMMEDIATE)
- [ ] Prepare 60 trajectories from real OSWorld data
- [ ] Stratified sampling across app types (Writer, Calc, GIMP, Chrome, etc.)
- [ ] Stratified sampling across trajectory lengths (short/medium/long)
- [ ] Create double-blind assignment (2 annotators per trajectory)
- [ ] Hide heuristic candidates from Human Gold annotators

### Phase E0b: Run Human Gold Annotation
- [ ] Launch Chinese annotation tool
- [ ] Recruit 2+ ordinary annotators
- [ ] Complete 60 double-blind annotations
- [ ] Track progress in real-time

### Phase E0c: Agreement Analysis
- [ ] Run `scripts/analyze_human_gold_agreement.py`
- [ ] Check calibration gate criteria:
  - Onset mechanism agreement >= 80%
  - Onset step ±1 agreement >= 80%
  - Recognition agreement >= 80%
- [ ] Generate disagreement report
- [ ] Run adjudication for disagreements

### Phase E0d: Gate Decision
- [ ] If gate passes → proceed to Large-Scale Annotation
- [ ] If gate fails → revise ontology and repeat E0

---

## Gate Criteria (Hard Stops)

| Metric | Threshold | Priority |
|--------|-----------|----------|
| Onset Mechanism Agreement | >= 80% | PRIMARY |
| Onset Step ±1 Agreement | >= 80% | PRIMARY |
| Recognition Agreement | >= 80% | PRIMARY |
| Recovery: No systematic category confusion | N/A | SECONDARY |
| Exact Onset Match | Diagnostic | DIAGNOSTIC |
| Onset MAE | Diagnostic | DIAGNOSTIC |
| UNCLEAR Rate | Report only | DIAGNOSTIC |

---

## Current Research Status: MEASUREMENT TOOL VALIDATION

**NOT:** Paper Results Complete
**NOT:** RQ1/RQ2/RQ3 Analysis
**NOT:** Large-Scale Findings

**IS:** Validating that our measurement instrument works before using it scientifically.

---

## Data Integrity Rules

1. **Heuristic labels CANNOT enter Human Gold**
   - They are marked `annotator_type = HEURISTIC`
   - Used only for pre-screening, not evidence

2. **Simulated data CANNOT be used for calibration**
   - Must use real OSWorld trajectories
   - Must use real human annotations

3. **AI annotations are for comparison only**
   - Not scientific evidence
   - Marked `annotator_type = LLM`
   - Compared against Human Gold after calibration

---

## Next Immediate Action

**Prepare 60 Human Gold trajectories for double-blind annotation.**

This is the ONLY blocker to proceeding to Large-Scale Scientific Measurement.

---

## Contact / Onboarding

For new annotators:
1. Open `annotation_tool/app_chinese.py`
2. Enter annotator ID (e.g., A001)
3. Complete 5 tutorial cases
4. Score >= 80% to begin
5. Annotate assigned trajectories
6. Data auto-saves

For administrators:
1. Append `?admin=true` to URL
2. View real-time progress
3. Monitor agreement rates
4. Trigger adjudication for disagreements
