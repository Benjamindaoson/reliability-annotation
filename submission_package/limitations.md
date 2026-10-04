# Limitations

## Study Limitations

### 1. Sample Size
- Current analysis: 200 trajectories
- Annotated: 0 (pending human labeling)
- Target: 50+ for preliminary, 100+ for full analysis

### 2. Model Coverage
- Current: Claude-4-Sonnet only
- Missing: GPT-4, Gemini, Claude 3.5, etc.
- Implication: Cannot generalize to all agents

### 3. Reasoning Traces
- OSWorld verified trajectories lack reasoning
- Cannot directly measure internal beliefs
- Must infer from observable evidence only

### 4. Elicitation Experiments
- Require API access (cost considerations)
- Require model availability
- Results may vary by model version

### 5. Oracle Experiments
- Require OSWorld environment access
- Require compute resources
- Not feasible without collaboration

### 6. Temporal Coverage
- 15-step trajectories only
- Missing: long-horizon (50+ step) patterns
- Missing: multi-session tasks

---

## Research Integrity

- ❌ No fabricated results
- ❌ No synthetic annotations as evidence
- ✅ Clear distinction between validated/preliminary/pending
- ✅ All scripts documented and reproducible
- ✅ Limitations explicitly stated

---

*Documented: 2026-10-02*
