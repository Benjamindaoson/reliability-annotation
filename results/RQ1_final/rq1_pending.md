# RQ1 Results: Where Do Agents Fail?

## Status: AWAITING HUMAN ANNOTATIONS

**This analysis requires human-labeled failure data.**

---

## What We Know

- 200 trajectories available from OSWorld
- Each trajectory has 15 steps
- Model: Claude-4-Sonnet

## What We Need

- Human annotations for failure type (SELECTION/EXECUTION/RECOGNITION/RECOVERY)
- Detection evidence (agent_detected_failure: YES/NO/UNCLEAR)
- Recovery attempt information

## How to Annotate

```bash
streamlit run annotation_tool/app.py
```

Target: Minimum 50 annotated trajectories for preliminary results.

---

## Expected Pipeline

After annotation, run:
```bash
python scripts/analyze_rq1.py
```

---

## Research Question

*Where do long-horizon agents fail in the task pipeline?*

**Answer pending human validation.**
