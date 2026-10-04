# Research Plan: Paper 1
## Do Agents Know When They Fail?
### A Causal Decomposition of Long-Horizon Agent Reliability

---

## 1 Research Thesis

**Hypothesis (H):** The dominant reliability bottleneck in long-horizon agents may shift from action selection toward recognition and recovery as agent capability increases.

**What this means in concrete terms:**

- Weak agents fail because they take wrong actions.
- Strong agents take correct actions more often — but when they fail, they may not detect the failure, or may not recover successfully.
- If H holds, future agent reliability work should prioritize self-monitoring and recovery over action generation.

**What Paper 1 is designed to do:**

Paper 1 is a **diagnostic study**: it is designed to falsify or support H, not to assume it. We measure where agents fail first, whether they detect failures, and which bottleneck removal most improves final task success. The data will determine whether H is supported, partially supported, or refuted.

**What Paper 1 explicitly does NOT assume:**

- That recognition is the primary bottleneck (this is the empirical question)
- That the bottleneck is the same across all capability levels
- That action generation is solved in current agents

---

## 2 Research Gap

### 2.1 What Existing Work Has Addressed

Existing agent benchmarks and reliability research have made significant progress on:

- Measuring task success rates across models and environments (WebArena, OSWorld, etc.)
- Identifying that agents fail at high rates in long-horizon tasks
- Showing that action errors decrease with model capability

### 2.2 What Remains Unaddressed

Despite this progress, three critical questions remain causally un-decomposed:

**Gap 1 — Where, precisely, do failures originate?** Prior work counts total failures or attributes them to coarse categories. No study has isolated the *first consequential failure* and measured its causal propagation through the rest of the trajectory.

**Gap 2 — Do agents know when they fail?** Prior work measures whether agents eventually succeed or fail, but not whether failures are detected at the moment they occur. The gap between "failed" and "knew they failed" is unmeasured.

**Gap 3 — Which bottleneck, if removed, would most improve reliability?** No study has applied controlled oracle interventions to isolate the causal effect of each bottleneck type on final task success.

### 2.3 What Paper 1 Does NOT Claim

- Paper 1 does not claim that RLHF causes models to avoid admitting failures — the self-attribution asymmetry, if observed, is reported as an empirical phenomenon; its mechanism is an open question for Paper 2.
- Paper 1 does not claim all agents have a self-monitoring problem — failure modes may vary by capability level, task type, and domain.
- Paper 1 does not claim to solve agent reliability — it is a diagnostic contribution that identifies where the problem lies.

---

## 3 Research Questions

| RQ | Question | Type |
|---|---|---|
| RQ1 | Where does the first consequential failure occur, and what type is it? | Descriptive / diagnostic |
| RQ2 | Under what conditions can agents detect failures they have caused? | Diagnostic / causal |
| RQ3 | Which bottleneck, if individually removed, most improves final task success? | Causal / comparative |

---

## 4 Formal Definitions

### 4.1 First Consequential Failure

Let a trajectory consist of steps \(t = 1, 2, ..., T\).

Let \(F_t \in \{0, 1\}\) indicate whether step \(t\) produces a *consequential* failure — an error that causally changes the future trajectory (not merely a suboptimal but outcome-neutral action).

The **first consequential failure** is:
\[
t^* = \min\{t : F_t = 1\}
\]

**Note:** This definition requires a causal, not merely correlational, criterion. An action is consequential if correcting it would change the final task outcome. This is adjudicated by human annotators using the Local Causal Window protocol (Section 6.2).

### 4.2 Failure Types

Each \(F_t = 1\) is classified into one of four mutually exclusive types:

| Type | Symbol | Definition |
|---|---|---|
| **Selection** | \(F_t^{sel}\) | Agent chose a wrong action given its correct world model |
| **Execution** | \(F_t^{exe}\) | Agent's intended action was correct but the environment did not execute as intended |
| **Recognition** | \(F_t^{rec}\) | Outcome was wrong but the agent did not detect it |
| **Recovery** | \(F_t^{recov}\) | Agent detected the failure but did not successfully recover |

These form the causal chain:
\[
\text{Selection} \rightarrow \text{Execution} \rightarrow \text{Recognition} \rightarrow \text{Recovery}
\]

### 4.3 Detection Variables

- \(\hat{F}_t \in \{0, 1\}\) — Agent's self-reported belief about whether step \(t\) succeeded
- \(t_d\) — First step at which \(\hat{F}_t = 0\) after a failure
- \(t_c\) — Critical boundary beyond which the failure becomes irreversible

### 4.4 Derived Metrics

| Variable | Definition |
|---|---|
| Undetected Failure Rate (UFR) | \(UFR = P(\hat{F}_t = 0 \mid F_t = 1)\) |
| Detection Delay (DD) | \(DD = t_d - t^*\) (in steps) |
| Recovery Window | \(W_r = t_c - t^*\) |
| Recovery Success (RS) | \(RS = P(\text{recovery successful} \mid \text{failure recognized})\) |

### 4.5 Reliability Profile

A trajectory's reliability is characterized by the tuple:
\[
R = (A, UFR, DD, RS)
\]

Where \(A\) is action correctness (proportion of consequential steps where \(F_t = 0\)).

---

## 5 Measurement Protocol

*See companion document: `paper1-measurement-protocol.md` for the full protocol.*

This section provides a compressed reference; detailed procedures, prompts, and decision trees are in the protocol document.

### 5.1 RQ1 Protocol Summary

For each trajectory, annotators:
1. Scan from \(t = 1\) to locate \(t^*\) (first consequential failure)
2. Classify the failure type using the Selection → Execution → Recognition → Recovery decision tree
3. Annotate the local causal window \([t^* - 2, t^* + K]\) where \(K = \min(5, \text{until endpoint})\)

### 5.2 RQ2 Protocol Summary

For each confirmed failure \(F_t = 1\), test detection under four progressively more informative conditions:

| Condition | Description | Measures |
|---|---|---|
| C0 | Spontaneous — agent's natural monitoring | \(D_0\) |
| C1 | Check trigger — add neutral instruction to verify each action | \(D_1\) |
| C2 | Evidence normalization — structure Before/Action/After, no new evidence | \(D_2\) |
| C3 | State oracle — add ground-truth hidden state | \(D_3\) |

Gap decomposition:
\[
G_{\text{trigger}} = D_1 - D_0 \quad
G_{\text{representation}} = D_2 - D_1 \quad
G_{\text{observability}} = D_3 - D_2
\]

Self-attribution control (using C2 evidence):
\[
G_{\text{self}} = \max(D_{\text{other}}, D_{\text{neutral}}) - D_{\text{self}}
\]

### 5.3 RQ3 Protocol Summary

Oracle interventions applied at the first occurrence of each failure type:

| Oracle | Trigger | Intervention |
|---|---|---|
| Oracle Selection | Agent's next action is a Selection failure | Provide the correct action |
| Oracle Execution | Agent's intention was correct but execution failed | Force correct execution |
| Oracle Recognition | Failure confirmed but not detected | Tell agent the action failed (no recovery hint) |
| Oracle Recovery | Failure detected but recovery failed | Provide the correct recovery action |

After each intervention, the trajectory continues autonomously.

---

## 6 Pilot Design

### 6.1 Scope

\[
23 \text{ tasks} \times 3 \text{ capability levels} = 69 \text{ trajectories}
\]

The pilot uses 23 tasks (expanded from the original 15 to ensure full attribute coverage; see Section 6.3).

### 6.2 Models

Three capability levels, to be determined based on availability at pilot time. Candidate levels:

- **Weak:** Open-source model (e.g., 7B-class) with agent scaffolding
- **Medium:** Frontier model (e.g., GPT-4o-class) with standard agent harness
- **Strong:** State-of-the-art model (e.g., Claude 3.5 Sonnet / GPT-4.5-class) with standard harness

Model selection should be finalized before the pilot, with the constraint that the three levels span a meaningful capability range on standard benchmarks.

### 6.3 Task Multi-Label Attribute Design

Tasks are **multi-label**: each task exercises one or more orthogonal attributes simultaneously. This avoids the confound of forcing tasks into mutually exclusive categories.

**Seven orthogonal attributes:**

| Attribute | Description |
|---|---|
| Observable | Failure consequence is directly visible in the environment |
| Hidden | Failure requires inspecting internal state (file, log, config) |
| Delayed | Failure manifests several steps after the incorrect action |
| Recoverable | Agent can undo or correct the error within the recovery window |
| Irreversible | Failure crosses a point of no return (submit, send, delete) |
| Cross-App | Failure affects or requires state in a different application |
| External | External event changes state mid-trajectory |

**Coverage requirements:** Each attribute must appear in at least 3 tasks; at least 6 attributes should reach 4 tasks.

**Full task pool and attribute matrix:** See companion document `paper1-pilot-tasks.md`.

### 6.4 Local Causal Window Annotation Protocol

For each trajectory:

1. **Locate \(t^*\):** Scan from \(t = 1\). The first consequential failure is \(t^*\).
   > **Note:** Locating \(t^*\) may require scanning the full trajectory and is not guaranteed to be O(1) without automated failure detection.

2. **Classify type:** Apply the Selection → Execution → Recognition → Recovery decision tree to the step at \(t^*\).

3. **Annotate causal window:** Annotate in detail the steps \([t^* - 2, t^* + K]\) where \(K\) ends at the first of:
   - Agent detects the failure
   - Agent successfully recovers
   - Failure becomes irreversible
   - Failure clearly propagates beyond the window
   - Trajectory ends

4. **Run RQ2 elicitation:** Apply C0–C3 cascade and self/other/neutral conditions to \(t^*\).

This protocol reduces annotation from O(T) to O(1) **after \(t^*\) is localized**, without claiming that locating \(t^*\) itself is O(1).

---

## 7 RQ2 Factorial Diagnostics

### 7.1 The Four-Level Cascade

The RQ2 elicitation cascade is factorial in structure: each condition adds a controlled increment of information or prompting, isolating a distinct failure mode.

| Contrast | What It Tests | What It Does NOT Test |
|---|---|---|
| C1 vs C0 | Does explicitly invoking a checking policy improve detection? | Whether the model *can* detect given the evidence |
| C2 vs C1 | Does restructuring evidence in canonical form improve detection? | Whether evidence is available in the environment |
| C3 vs C2 | Does providing hidden state improve detection? | Whether the model has consequence-understanding capability |
| C3 vs C0 | Aggregate detection improvement with full support | — |

### 7.2 Self-Attribution Control

The self/other/neutral intervention tests whether failure recognition depends on whether the action is attributed to the agent itself.

| Contrast | What It Tests | What It Does NOT Test |
|---|---|---|
| Other/Neutral vs Self | Does attribution framing change detection rates with identical evidence? | Why the asymmetry exists (capability vs motivation vs training) |
| Other vs Neutral | Does "another agent" vs "system log" framing matter? | — |

### 7.3 Diagnostic Tree

When an agent fails to detect a confirmed failure at C0:

```
C0 (spontaneous): detected?
  YES
  └── Monitoring policy is the bottleneck.
      Key lever: G_trigger

  NO → C1 (check trigger): detected?
    YES
    └── Harness doesn't invoke checking even when information exists.
        Key lever: monitoring policy / harness architecture

    NO → C2 (normalized evidence): detected?
      YES
      └── State representation problem — evidence is present but scattered.
          Key lever: memory compression / context management

      NO → C3 (oracle state): detected?
        YES
        └── Observability failure — evidence absent from environment.
            Key lever: perception / environment instrumentation

        NO
        └── Consequence-understanding capability failure.
            Key lever: model training / action consequence modeling
```

### 7.4 What Each RQ2 Result Commits Paper 2 To

| RQ2 Finding | Paper 2 Direction |
|---|---|
| Large \(G_{\text{trigger}}\) | Study when/how to invoke latent monitoring capability (harness design) |
| Large \(G_{\text{representation}}\) | Study state reconstruction, memory compression, context architecture |
| Large \(G_{\text{observability}}\) | Study action consequence perception, environment instrumentation |
| Large \(G_{\text{self}}\) | Study self-attribution-conditioned evaluation (mechanism deferred to controlled experiments) |
| All gaps small at C3 | Study consequence-understanding as a model capability |

---

## 8 Oracle Intervention Design

### 8.1 Oracle Trigger Rules

To prevent oracle leakage (different oracles providing different amounts of information), each oracle has a strict trigger and fixed intervention:

**Oracle Selection:**
- Trigger: Annotator classifies the agent's next action as a Selection failure (\(F_t^{sel} = 1\))
- Intervention: Replace the agent's action with the correct action. Agent continues from there.
- Information leaked: The correct action — same as what a human would provide in a minimal correction.

**Oracle Execution:**
- Trigger: Agent's intended action was correct (not a Selection failure) but the environment failed to execute it
- Intervention: Force the correct execution in the environment. Agent continues from there.
- Information leaked: The execution outcome — no decision-making information is provided.

**Oracle Recognition:**
- Trigger: A failure has occurred (\(F_t = 1\)) and the agent has not detected it (\(\hat{F}_t = 1\))
- Intervention: Send the agent the message: *"The previous action did not achieve its intended effect."* No additional hint about what went wrong or how to recover.
- Information leaked: That a failure occurred — but not where, why, or how to fix it.

**Oracle Recovery:**
- Trigger: Agent has detected a failure (\(\hat{F}_t = 0\)) but its recovery attempt fails
- Intervention: Provide the correct recovery action.
- Information leaked: Both that a failure occurred and the specific recovery action.

### 8.2 Ordering and Interaction Effects

Oracle interventions are applied **at the first occurrence** of each failure type, then the trajectory continues. This design enables:

- Measuring the isolated causal effect of each bottleneck
- Detecting whether removing an upstream bottleneck reveals a downstream one
- Testing whether bottlenecks are independent, sequential, or substitutive

### 8.3 Baseline and Normalization

**Baseline:** \(S_0\) = final task success rate without any oracle intervention.

**Absolute oracle lift:**
\[
\Delta_{\text{type}} = S_{\text{type}} - S_0
\]

**Normalized oracle lift (Recovered Gap):**
\[
\text{Recovered Gap}_{\text{type}} = \frac{S_{\text{type}} - S_0}{1 - S_0}
\]

The normalized metric is necessary for comparing oracle effects across baseline conditions. A 10-point absolute lift is very different when the baseline is 20% versus 80%.

---

## 9 Metrics and Statistical Analysis

### 9.1 Primary Metrics

| Metric | Definition | Level |
|---|---|---|
| First-Failure Type Distribution | \(P(\text{type} = k \mid \text{failure occurred})\) | Aggregate |
| Undetected Failure Rate (UFR) | \(\frac{1}{N}\sum_i P(\hat{F}_t = 0 \mid F_t = 1)_i\) | Aggregate |
| Gap Decomposition | \(G_{\text{trigger}}, G_{\text{rep}}, G_{\text{obs}}, G_{\text{self}}\) | Aggregate |
| Oracle Lift | \(\Delta_{\text{sel}}, \Delta_{\text{exe}}, \Delta_{\text{recog}}, \Delta_{\text{recover}}\) | Aggregate |
| Normalized Oracle Lift | \(\text{Recovered Gap}_{\text{type}}\) | Aggregate |
| Detection Delay (DD) | \(t_d - t^*\) (steps) | Per-trajectory |
| Recovery Window (Wr) | \(t_c - t^*\) (steps) | Per-trajectory |

### 9.2 Statistical Analysis

**Confidence intervals:** Report 95% confidence intervals for all aggregate metrics using bootstrap resampling (10,000 iterations) due to expected small sample sizes in the pilot.

**Within-model paired comparisons:** For RQ2, each failure instance is tested under multiple conditions. Use McNemar's test for paired binary comparisons (C0 vs C1, C1 vs C2, etc.).

**Oracle comparisons:** Use paired t-tests (or bootstrap) for comparing \(S_0\) vs \(S_{\text{type}}\), since the same task-model pairs are used across conditions.

**Cross-capability comparisons:** Test whether the bottleneck type distribution (from RQ1) and UFR (from RQ2) change systematically with model capability using a chi-squared test for RQ1 and a correlation analysis for UFR.

**Multiple comparison correction:** Apply Bonferroni correction across oracle comparisons (4 comparisons) and gap decomposition comparisons (3 comparisons for G-trigger, G-rep, G-obs; plus 3 for self/other/neutral). Report both raw and corrected p-values.

### 9.3 Pre-Registration

To prevent p-hacking and post-hoc narrative fitting, the following are **pre-registered** before the pilot runs:

- The three kill/go criteria (Section 10)
- The primary metrics and their definitions
- The statistical tests to be used
- The oracle intervention trigger rules

Any analysis that is not pre-registered will be clearly labeled as exploratory in the paper.

---

## 10 Go / No-Go Criteria

These criteria are written **before the pilot runs** and will not be modified based on results. They determine whether Paper 1 proceeds to a full-scale study.

### 10.1 Kill Criteria (Stop This Research Direction)

| # | Kill Signal | Threshold | Action |
|---|---|---|---|
| **Kill 1** | >80–90% of first failures are Selection type; Oracle Recognition barely improves success (<5 percentage points) | Any single condition met | Pause the recognition/recovery research direction. Action generation remains the dominant bottleneck. |
| **Kill 2** | Nearly all failures are self-detected at C0 (spontaneous detection rate >80%) | Both conditions met | Consequence recognition is not the primary reliability problem. Redirect to recovery strategies. |
| **Kill 3** | Undetected failures (UFR) only appear under artificially injected failures, not in natural OSWorld trajectories | Met | Cannot claim a fundamental long-horizon bottleneck. Reframe as a robustness study only. |

### 10.2 Go Criteria (Expand to Full Study)

| # | Go Signal | Threshold | Action |
|---|---|---|---|
| **Go 1** | Natural long-horizon trajectories show a Failure → NotDetected → Continue pattern in ≥20% of failures | Met | Strong signal that recognition is a genuine bottleneck, not artifact |
| **Go 2** | Oracle Recognition substantially improves final task success | \(\Delta_{\text{recog}} > 10\) percentage points and Recovered Gap \(> 0.15\) | Confirms recognition as a causally meaningful bottleneck |
| **Go 3** | Action errors decrease with model capability but UFR decreases more slowly | Capability × Failure Type interaction significant at p < 0.05 | **Reliability Bottleneck Shift confirmed** — strongest possible result for this paper |

Meeting **Go 1 alone** is sufficient to proceed. Go 2 and Go 3 provide increasingly strong evidence.

### 10.3 Conditional Paths

| Pilot Result | Interpretation | Next Step |
|---|---|---|
| Kill 1 only | Action generation is still the dominant bottleneck | Pause Paper 1; return when agents are stronger |
| Kill 2 only | Detection is not the problem; study recovery | Reframe RQ2/RQ3 around recovery strategies |
| Kill 3 only | Undetected failures are artifacts | Reframe as robustness against adversarial state corruption |
| Go 1 + not Kill 1/2/3 | Recognition is a genuine bottleneck | Proceed to full study |
| Go 1 + Go 2 | Recognition has large causal headroom | Strong paper; emphasize the intervention result |
| Go 1 + Go 3 | Reliability Bottleneck Shift confirmed | **Elevated claim:** paper argues for a scaling-phase transition in agent reliability bottlenecks |

---

## 11 Full-Scale Study Trigger

The full-scale study is **not pre-committed**. It is triggered only if the pilot meets at least one Go criterion and no Kill criteria.

**Full-scale study parameters (indicative, to be finalized after pilot):**

| Parameter | Pilot | Full-Scale (Indicative) |
|---|---|---|
| Tasks | 23 | 80–120 |
| Capability levels | 3 | 5 (spanning 7B to frontier) |
| Repetitions per (task, model) | 1 | 3–5 |
| Total trajectories | 69 | 1,200–3,000 |

**What the full-scale study enables:**

- Sufficient power to detect medium effect sizes in oracle comparisons
- Cross-task generalization analysis for each bottleneck type
- Regression analysis of UFR vs model capability with task-level covariates
- Analysis of bottleneck migration across the full capability spectrum

---

## 12 Paper Claims Matrix

This matrix specifies, for each empirical result, exactly what claim is supported and what claim is **forbidden**. It is a reviewer-defense instrument: every forbidden claim has a known confound that the experiment does not control.

| Evidence | Allowed Claim | Forbidden Claim |
|---|---|---|
| \(D_1 > D_0\) (large \(G_{\text{trigger}}\)) | Explicit checking instruction unlocks detection that spontaneous monitoring misses | Harness is the sole reason for detection failures |
| \(D_2 > D_1\) (large \(G_{\text{representation}}\)) | Structuring evidence in canonical form improves detection | Model lacks working memory or memory capacity |
| \(D_3 > D_2\) (large \(G_{\text{observability}}\)) | Additional hidden state information improves detection | Pure observation-based agents can never detect these failures |
| \(D_{\text{other}} > D_{\text{self}}\) (positive \(G_{\text{self}}\)) | Failure recognition depends on whether the action is attributed to the agent itself | RLHF causes models to avoid admitting their own failures |
| \(\Delta_{\text{recog}} > \Delta_{\text{sel}}\) | Under the tested conditions, recognition removal has larger causal headroom than selection removal | Recognition is the universal first bottleneck for all agents |
| Bottleneck shifts with capability | The dominant failure type migrates as agent capability increases | Scaling will eventually solve action generation and leave only recognition as the problem |
| UFR decreases slower than action errors | Failure awareness improves more slowly than action correctness with capability | Self-monitoring capability is fundamentally unlearnable |

---

## 13 Related Work and Positioning

*To be completed. Key references to include:*

- **Agent benchmarks:** OSWorld, WebArena, VisualWebArena, WindowsAgentArena — establish the task environment landscape
- **Agent reliability:** Prior work on agent error rates, failure mode analysis, and the observation that agents fail frequently in long-horizon tasks
- **Self-correction in LLMs:** Literature on self-repair, self-verification, and critique capabilities in language models
- **Self-attribution asymmetry:** 2026 work on differential evaluation of own vs other agents' outputs (cite precisely; hedge as "anonymized for review")
- **Training objective conflicts:** OpenAI confessions work on honest failure reporting as a separate reward target
- **Self-rewarding RL:** ICML 2026 finding of self-confirming bias in self-rewarding settings
- **Causal decomposition methods:** Literature on oracle interventions for identifying causal bottlenecks in complex systems

---

## 14 Timeline and Deliverables

| Phase | Duration | Deliverable |
|---|---|---|
| Protocol finalization | Week 1–2 | Measurement protocol and task pool finalized |
| Pilot execution | Week 3–6 | 69 trajectories collected and annotated |
| Pilot analysis | Week 7–8 | Evaluate kill/go criteria; decide on full study |
| Full study (if triggered) | Week 9–20 | Full-scale data collection |
| Analysis and writing | Week 21–28 | Paper drafted and submitted |

---

## 15 Document History

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2026-10-01 | Initial research plan |
| 0.2 | 2026-10-01 | Multi-label task design; self-attribution claim boundary clarified; O(1) annotation claim corrected |

