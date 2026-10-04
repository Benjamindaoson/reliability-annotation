# Annotation Provenance Report

**Audit Date:** 2026-10-02
**Auditor:** Claude Code (Automated Evidence Audit)

---

## Annotation Source

| Field | Value |
|-------|-------|
| File | `data/human_annotations/auto_annotations.jsonl` |
| **Annotation source:** | **Rule-based heuristic algorithm** |
| **Generation method:** | `scripts/auto_annotate.py` |
| Number of samples | 361 trajectories |
| **Can be used as paper evidence:** | **NO** (requires human validation) |

---

## Provenance Evidence

From the annotation file itself:

```json
{
  "trajectory_id": "chrome/030eeff7-b492-4218-b312-701ec99ee0cc",
  "failure_type": "RECOGNITION",
  "agent_detected": "N/A",
  "reasoning": "未检测到重试或选择错误模式，智能体可能未察觉失败",
  "annotated_by": "auto"   ← <-- EXPLICIT MARKER
}
```

Every single annotation has `"annotated_by": "auto"`.

---

## Annotation Method Details

The `auto_annotate.py` script uses:

### RECOGNITION Detection
- No retry patterns in action sequence
- No awareness keywords in action data
- No correction attempts detected

### RECOVERY Detection
- Retry patterns: repeated clicks at similar coordinates (< 20 pixels apart)
- Multiple attempts (≥2 retries) at same action

### SELECTION Detection
- High coordinate dispersion (> 70% spread across screen)
- Edge clicks (> 30% of clicks at screen boundaries)

### EXECUTION Detection
- Coordinate out of bounds (< 0 or > 3000)
- Parameter errors

---

## Limitation Assessment

| Limitation | Severity | Impact |
|------------|----------|--------|
| No ground truth validation | HIGH | Cannot verify accuracy |
| No inter-annotator agreement | HIGH | No reliability metric |
| Binary classification | MEDIUM | Multi-bottleneck failures not captured |
| Pattern-based only | HIGH | No semantic understanding |
| Single heuristic pass | MEDIUM | No confidence scoring |

---

## Conclusion

**These annotations are NOT human-grounded evidence.**

They can be used as:
- ✅ Exploratory analysis to guide hypothesis formation
- ✅ Pilot study to estimate effect sizes
- ✅ Sample selection for human annotation
- ❌ Paper evidence for RQ1/RQ2/RQ3 claims
- ❌ Ground truth for NAACL submission

---

## Required Next Steps

1. **Human Annotation**: A human annotator must label a representative sample (minimum 50-100 trajectories) using the Streamlit annotation tool
2. **Inter-annotator Agreement**: At least 2 annotators must label the same 30 trajectories
3. **Validation**: Compare human annotations against heuristic annotations to estimate accuracy
4. **Report**: Calculate agreement rate (Cohen's κ) and accuracy

---

*This document is part of the Paper 1 Evidence Audit.*
