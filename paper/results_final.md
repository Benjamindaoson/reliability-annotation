# 5. Results

## 5.1 RQ1: Where Do Agents Fail?

### Data
- Human-annotated failures: 0
- Source: `data/human_annotations/annotations.jsonl`

### Failure Type Distribution

| Failure Type | Count | Percentage | Status |
|--------------|-------|------------|--------|
| SELECTION | TBD | 0.0% | ❌ Pending |
| EXECUTION | TBD | 0.0% | ❌ Pending |
| RECOGNITION | TBD | 0.0% | ❌ Pending |
| RECOVERY | TBD | 0.0% | ❌ Pending |

### Key Finding (RQ1)

**Failure distribution pending human validation.**

---

## 5.2 RQ2: Do Agents Know When They Fail?

### Baseline Detection (C0)

| Metric | Value | Status |
|--------|-------|--------|
| Detection Rate (D0) | TBD | ❌ Pending |
| Undetected Failure Rate (UFR) | TBD | ❌ Pending |

**Pending human validation.**

---

## 5.3 RQ2: Elicitation Cascade

### C0-C3 Results

| Condition | Detection Rate | Effect | Status |
|-----------|----------------|--------|--------|
| C0 (Baseline) | TBD | - | ❌ Pending API |
| C1 (+Verification) | TBD | G_trigger | ❌ Pending API |
| C2 (+State Info) | TBD | G_representation | ❌ Pending API |
| C3 (+Hidden State) | TBD | G_observability | ❌ Pending API |

**Status**: Requires API experiments. See `scripts/rq2_api_runner.py`

---

## 5.4 RQ3: Which Bottleneck Matters Most?

### Oracle Intervention Results

| Intervention | Success Rate | Δ from Baseline | Status |
|--------------|--------------|-----------------|--------|
| Baseline (S0) | TBD | - | ❌ Pending |
| Oracle Selection | TBD | TBD | ❌ Pending |
| Oracle Execution | TBD | TBD | ❌ Pending |
| Oracle Recognition | TBD | TBD | ❌ Pending |
| Oracle Recovery | TBD | TBD | ❌ Pending |

**Status**: Requires OSWorld environment. See `scripts/oracle/runner.py`

---

## Summary of Findings

### Confirmed (Human Validated)
- RQ1: Failure type distribution (pending annotations)
- RQ2: Detection rate baseline (pending annotations)

### Preliminary (Pipeline Tested)
- Failure taxonomy framework
- Annotation protocol
- Analysis pipeline

### Pending (Blocked)
- RQ2 elicitation cascade
- RQ3 oracle interventions
- Multi-model comparison
