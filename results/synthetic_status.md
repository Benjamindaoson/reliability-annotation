# Synthetic Annotation Status

**Generated: 2026-10-02**

## Purpose

These files contain **synthetic annotations only** — randomly generated labels used solely for **pipeline validation**.

**They are NOT scientific evidence.**

## Why Synthetic Annotations Exist

1. To test the annotation pipeline
2. To validate analysis scripts
3. To ensure figure generation works
4. To verify report templates

## What Cannot Be Claimed From These

- Any specific failure distribution
- Any detection rate statistics
- Any causal relationship
- Any model comparison

## Files Affected

All files in this directory contain synthetic data:

- `results/annotations/` — synthetic failure labels
- `results/RQ*/` — statistics based on synthetic labels
- `results/PAPER_RESULTS.md` — draft claims, not validated
- `paper/` — draft sections, pending real data

## Moving to Exploratory-Only

```bash
mv results/annotations results/exploratory_only/
mv results/RQ1 results/exploratory_only/RQ1_synthetic
mv results/RQ2 results/exploratory_only/RQ2_synthetic
mv results/RQ3 results/exploratory_only/RQ3_synthetic
mv results/reliability_profile results/exploratory_only/reliability_synthetic
mv results/statistical results/exploratory_only/statistical_synthetic
```

## Next Steps

1. Create human annotation workflow (Phase 29)
2. Run human annotation campaign
3. Regenerate all statistics from human labels
4. Update paper with real evidence

---

**End of synthetic status document**
