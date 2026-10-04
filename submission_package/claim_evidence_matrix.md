# Claim-Evidence Matrix

## Paper: Do Agents Know When They Fail?

| Claim | Evidence Required | Evidence Available | Status |
|-------|-------------------|-------------------|--------|
| Selection failures are most common | Human annotations (50+) | 0 | ❌ Pending |
| UFR >> 0 (agents miss failures) | Human annotations | 0 | ❌ Pending |
| Verification improves detection | API experiments | None | ❌ Pending |
| Self-attribution asymmetry exists | API experiments | None | ❌ Pending |
| Selection interventions highest impact | Oracle reruns | None | ❌ Pending |

---

## Pipeline Commands

```bash
# 1. Annotate trajectories
streamlit run annotation_tool/app.py

# 2. Run RQ1 analysis
python scripts/phase32_regenerate_rq1.py

# 3. Run RQ2 experiments (requires API)
python scripts/rq2_api_runner.py --cases results/RQ2_real/rq2_cases.json --condition C0 --api-key KEY

# 4. Run oracle experiments (requires environment)
python scripts/oracle/runner.py --input results/RQ2_real/rq2_cases.json --intervention selection
```

---

## Reproducibility

- [x] Code repository organized
- [x] Scripts documented
- [ ] Human annotations available (TBD)
- [ ] API results available (TBD)
- [ ] Environment access documented (TBD)

---

## Limitations

1. **Single model**: Only Claude-4-Sonnet analyzed
2. **Limited annotations**: Awaiting human labeling
3. **No reasoning traces**: Cannot measure internal beliefs directly
4. **Simulated experiments**: RQ2/RQ3 require API/environment access

---

*Generated: 2026-10-02*
