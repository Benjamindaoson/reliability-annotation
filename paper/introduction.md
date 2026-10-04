# 1. Introduction

Large language model (LLM) agents are increasingly deployed for complex, multi-step computer tasks. However, these agents often fail in ways that are difficult to detect and correct. Understanding *where* agents fail and *whether* they recognize their failures is crucial for building more reliable systems.

## 1.1 Motivation

Current evaluation benchmarks focus on task success rates but provide little insight into:
- **Where** failures occur in the task pipeline
- **Whether** agents can self-diagnose their failures
- **What** interventions would most improve reliability

## 1.2 Research Questions

**RQ1: Where do agents fail?**
We categorize failures into four types: selection, execution, recognition, and recovery.

**RQ2: Do agents know when they fail?**
We measure spontaneous failure detection and test elicitation techniques.

**RQ3: Which bottleneck matters most?**
We simulate oracle interventions to identify the highest-impact improvements.

## 1.3 Contributions

1. A failure taxonomy for long-horizon agent tasks
2. Empirical analysis of failure distribution in OSWorld
3. A causal decomposition of failure awareness bottlenecks
4. Evidence for self-attribution effects on failure detection
5. Oracle intervention analysis for reliability improvement

## 1.4 Limitations

[TBD after experiments - include confidence intervals, model comparison, etc.]
