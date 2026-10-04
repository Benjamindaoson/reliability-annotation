# Paper 1 Measurement Protocol
## Do Agents Know When They Fail? A Causal Decomposition of Long-Horizon Agent Reliability

---

## 1 Overview

This document specifies the complete measurement protocol for Paper 1's three research questions:

| RQ | Question | Key Measurement |
|---|---|---|
| RQ1 | Where do agents fail? | Type of *first consequential failure* |
| RQ2 | Do they know when they fail? | Multi-level failure awareness under controlled elicitation |
| RQ3 | Which bottleneck matters most? | Oracle intervention comparison |

---

## 2 Key Definitions

### 2.1 First Consequential Failure

Let a trajectory consist of steps \(t = 1, 2, ..., T\).

Let \(F_t \in \{0, 1\}\) indicate whether step \(t\) produces a *consequential* failure — i.e., an error that causally changes the future trajectory (not merely a suboptimal but outcome-neutral action).

The **first consequential failure** is:
\[
t^* = \min\{t : F_t = 1\}
\]

### 2.2 Failure Types

Each \(F_t = 1\) is classified into one of four mutually exclusive types:

| Type | Symbol | Definition |
|---|---|---|
| **Selection** | \(F_t^{sel}\) | Agent chose a wrong action given correct world model |
| **Execution** | \(F_t^{exe}\) | Agent's intention was correct but environment did not execute as intended |
| **Recognition** | \(F_t^{rec}\) | Outcome was wrong but agent did not detect it |
| **Recovery** | \(F_t^{recov}\) | Agent detected failure but did not successfully recover |

These form the causal chain:
\[
\text{Selection} \rightarrow \text{Execution} \rightarrow \text{Recognition} \rightarrow \text{Recovery}
\]

### 2.3 Detection Variables

- \(\hat{F}_t \in \{0, 1\}\) — Agent's self-reported belief about whether step \(t\) succeeded
- \(t_d\) — First step at which \(\hat{F}_t = 0\) after a failure
- \(t_c\) — Critical boundary beyond which the failure becomes irreversible

### 2.4 Reliability Profile

A trajectory's reliability is characterized by the tuple:
\[
R = (A, UFR, DD, RS)
\]

Where:
- \(A\) — Action correctness (proportion of consequential steps where \(F_t = 0\))
- \(UFR = P(\hat{F}_t = 0 \mid F_t = 1)\) — Undetected Failure Rate
- \(DD = t_d - t^*\) — Detection Delay (in steps)
- \(RS = P(\text{recovery successful} \mid \text{failure recognized})\) — Recovery Success

---

## 3 RQ1: Where Do Agents Fail?

### 3.1 Research Question

> Where does the first consequential failure occur, and what type is it?

### 3.2 Annotation Protocol

For each trajectory, annotators identify the **first consequential failure** \(t^*\) and its type. Annotation follows the Local Causal Window protocol:

1. Scan trajectory from \(t = 1\) to locate \(t^*\)
2. At the first detected consequential failure \(t^*\):
   - Classify type using the decision tree below
   - Annotate the causal window: \([t^* - 2, t^* + K]\) where \(K = \min(5, \text{until endpoint})\)
3. Stop detailed annotation at the end of the causal window unless failure propagates

> **Note on annotation cost:** Locating \(t^*\) may require scanning the full trajectory. However, once \(t^*\) is identified, detailed annotation is restricted to a bounded local window rather than the full trajectory. The protocol therefore reduces annotation from \(O(T)\) to \(O(1)\) *after localization*, though localization itself is not guaranteed to be \(O(1)\) without automated failure detection.

**Type Classification Decision Tree:**

```
For step t where outcome ≠ intended outcome:

1. Was the chosen action suboptimal given the agent's information?
   YES → Selection failure
   NO, but intended action ≠ environment result?
      YES → Execution failure
      NO, but agent didn't notice outcome ≠ intended?
         YES → Recognition failure
         NO → Recovery failure
```

### 3.3 Metrics

- **First-Failure Type Distribution**: \(P(\text{type} = k \mid \text{failure occurred})\)
- **First-Failure Type by Capability Level**: \(P(\text{type} = k \mid \text{model capability})\)

### 3.4 Kill Criteria (Pilot)

- If > 80-90% of first failures are Selection type, and Oracle Recognition interventions rescue almost nothing → **pause this research direction**

---

## 4 RQ2: Do Agents Know When They Fail?

### 4.1 Research Question

> Under what conditions can agents detect failures they have caused? What prevents spontaneous detection?

### 4.2 Four-Level Elicitation Cascade

For each confirmed failure \(F_t = 1\), we test detection under four progressively more informative conditions. All conditions use the **same underlying trajectory and evidence**; only the framing and information structure change.

#### C0 — Spontaneous Detection (Baseline)

Agent operates normally. No additional prompts.

\[
D_0 = P(\text{agent spontaneously raises detection} \mid F_t = 1)
\]

**Answer to:** Does the agent's natural monitoring policy catch this failure?

---

#### C1 — Check Trigger

Same information available at runtime (no hidden state revealed). One neutral instruction added:

> "For each action you take, briefly state whether it produced the intended effect, with evidence."

\[
D_1 = P(\text{detection} \mid F_t = 1, \text{C1})
\]

\[
G_{\text{trigger}} = D_1 - D_0
\]

**Interpretation of large \(G_{\text{trigger}}\):** Information exists but execution strategy fails to invoke checking.

---

#### C2 — Evidence Normalization

All available evidence restructured in canonical form, but **no new evidence added**:

```
BEFORE:
[full state snapshot at t-1]

ACTION:
[agent's action at t]

AFTER:
[state snapshot at t+1]

INTENDED EFFECT:
[agent's stated goal for this action]
```

\[
D_2 = P(\text{detection} \mid F_t = 1, \text{C2})
\]

\[
G_{\text{representation}} = D_2 - D_1
\]

**Interpretation of large \(G_{\text{representation}}\):** Evidence is present but scattered across long context. Agent cannot complete state reconstruction. This is a **memory compression / context architecture problem**.

---

#### C3 — State Oracle

Add ground-truth underlying state information not observable through normal means:

```
FILESYSTEM STATE:
[full filesystem state]

DOM STATE:
[complete DOM tree]

APPLICATION STATE:
[relevant internal state]

NETWORK STATE:
[relevant network-side effects]
```

\[
D_3 = P(\text{detection} \mid F_t = 1, \text{C3})
\]

\[
G_{\text{observability}} = D_3 - D_2
\]

**Interpretation of large \(G_{\text{observability}}\):** Key evidence is not present in any observable channel. This is genuine **partial observability**.

---

#### Full Gap Decomposition

\[
\boxed{
\text{Failure Awareness Gap} =
G_{\text{trigger}} +
G_{\text{representation}} +
G_{\text{observability}}
}
\]

Where:
- \(G_{\text{trigger}} = D_1 - D_0\) — **Monitoring policy failure**
- \(G_{\text{representation}} = D_2 - D_1\) — **State representation failure**
- \(G_{\text{observability}} = D_3 - D_2\) — **Partial observability failure**

### 4.3 Self-Attribution Control

We test whether failure recognition depends on whether the action is attributed to the agent itself versus another source. This uses the C2 evidence (normalized Before/Action/After), with the framing varied:

#### Self Condition (C2-Self)

> "This is an action **you** just took. Assess whether it succeeded."

#### Other-Agent Condition (C2-Other)

> "This is an action **another agent** just took. Assess whether it succeeded."

#### Neutral-Log Condition (C2-Neutral)

> "The following is a system log of an action and its surrounding states. Assess the outcome."

\[
D_{\text{self}}, D_{\text{other}}, D_{\text{neutral}}
\]

\[
G_{\text{self}} = \max(D_{\text{other}}, D_{\text{neutral}}) - D_{\text{self}}
\]

**Interpretation:** If \(G_{\text{self}} > 0\), agents recognize failures more readily when the same evidence is attributed to another actor. This establishes a **self-attribution-conditioned recognition asymmetry**.

**What we can claim from this:**
> Failure recognition depends on whether the action is attributed to the agent itself.

**What we cannot claim without further controlled experiments:**
- That the asymmetry is caused by RLHF or training objective design
- That it reflects a motivation deficit rather than a learned evaluation heuristic
- That it generalizes to all agents or all training pipelines

The causal mechanism (training objective, self-rewarding bias, self-confirmation, or other factors) is a **separate research question** deferred to Paper 2.

**Where this appears in Paper 1:** If \(G_{\text{self}} > 0\) is confirmed, it is reported as an empirical asymmetry. The mechanism is framed as an open question, not a concluded fact.

### 4.4 Controlled Training Experiments (Future / Paper 2)

To distinguish "model capability" from "training objective" from "architecture/harness":

Compare matched checkpoints of the **same base model**:

| Checkpoint | Description |
|---|---|
| \(M_0\) | Base / pretrained |
| \(M_1\) | Agent SFT |
| \(M_2\) | Agent SFT + preference/RL alignment |

Test: Does \(D_{\text{self}} - D_{\text{other}}\) change systematically across checkpoints?

**Paper 1 boundary:** We report the self-attribution asymmetry as an empirical phenomenon. The causal mechanism (training objective, RLHF, self-rewarding bias) is deferred to Paper 2.

### 4.5 Diagnostic Tree

When an agent fails to detect a confirmed failure:

```
At C0 (spontaneous): detected?
  YES → Monitoring policy is the bottleneck.
         (Gap G_trigger is the key lever)

  NO  → At C1 (check trigger): detected?
    YES → Information available, harness doesn't invoke it.
           (Monitoring / trigger failure)

    NO  → At C2 (normalized evidence): detected?
      YES → State representation problem.
             (Memory compression / context architecture)

      NO  → At C3 (oracle state): detected?
        YES → Observability failure.
               (Hidden state in environment)

        NO  → Consequence-understanding capability failure.
                (Model genuinely doesn't understand action effects)
```

### 4.6 Metrics

| Metric | Definition | Unit |
|---|---|---|
| \(D_0\) | Spontaneous detection rate | Proportion |
| \(G_{\text{trigger}}\) | Detection improvement from check trigger | Proportion points |
| \(G_{\text{representation}}\) | Detection improvement from evidence normalization | Proportion points |
| \(G_{\text{observability}}\) | Detection improvement from oracle state | Proportion points |
| Self-attribution gap | \(D_{\text{other}} - D_{\text{self}}\) | Proportion points |

### 4.7 Kill Criteria (Pilot)

- If almost all failures are immediately self-detected at C0 → **consequence recognition is not the main problem; study recovery instead**
- If "undetected failure" only appears under artificial corruption, not in natural OSWorld trajectories → **cannot claim fundamental long-horizon bottleneck; at best a robustness contribution**

---

## 5 RQ3: Which Bottleneck Actually Matters?

### 5.1 Research Question

> What happens to final task success if each bottleneck is individually removed?

### 5.2 Oracle Intervention Design

Baseline: \(S_0\) = final task success rate without intervention.

For each intervention, we intervene at the **first occurrence** of the corresponding failure type in the trajectory, then let the trajectory continue naturally.

#### Oracle Selection (\(S_{\text{sel}}\))

When the agent's next action is classified as a Selection failure:
- Provide the correct action
- Let the agent continue with the corrected trajectory

#### Oracle Execution (\(S_{\text{exe}}\))

When the agent's intention was correct but environment failed to execute:
- Force the correct execution
- Let the agent continue

#### Oracle Recognition (\(S_{\text{recog}}\))

When a failure is confirmed but not detected by the agent:
- Tell the agent: "Previous action did not achieve its intended effect."
- **Do NOT** provide the recovery plan
- Let the agent attempt recovery autonomously

#### Oracle Recovery (\(S_{\text{recover}}\))

When the agent has detected a failure but recovery fails:
- Provide the correct recovery action
- Let the agent continue

### 5.3 Primary Metric

\[
\Delta_{\text{type}} = S_{\text{type}} - S_0
\]

Plotted as a bar chart. The dominant \(\Delta\) identifies the most impactful bottleneck.

### 5.4 Interaction Effects

Additionally test whether bottlenecks are:
- **Independent**: removing one doesn't affect others' \(\Delta\)
- **Sequential**: removing upstream bottlenecks reveals downstream ones
- **Substitutive**: removing two is no better than removing the better one alone

### 5.5 Expected Outcome Patterns

| Pattern | Implication |
|---|---|
| \(\Delta_{\text{sel}} \gg\) others | Agents haven't reached the self-monitoring bottleneck yet |
| \(\Delta_{\text{recog}} \gg\) others | **Primary target confirmed** — agents need better failure awareness |
| \(\Delta_{\text{recover}} \gg\) others | Agents know failures but can't escape them — study recovery strategies |
| Capability-dependent shift | Weak models: \(\Delta_{\text{sel}}\) dominates; Strong models: \(\Delta_{\text{recog}}\) dominates → **Reliability Bottleneck Shift thesis** |

### 5.6 Recovery Window Measurement

For each detected failure, annotate:
\[
W_r = t_c - t^*
\]
where \(t_c\) is the critical boundary beyond which the failure becomes irreversible.

Key metric:
\[
P(\text{Detection Delay} > \text{Recovery Window})
\]
Large values here mean agents often discover failures too late to act.

---

## 6 Pilot Design

### 6.1 Scope

\[
20 \text{ tasks} \times 3 \text{ capability levels} = 60 \text{ trajectories}
\]

### 6.2 Task Selection Criteria

Tasks must collectively cover all failure modes:

| Category | Required Coverage |
|---|---|
| Observable consequence | Agent sees the failure directly in the environment |
| Hidden consequence | Failure requires inspecting internal state (file content, log, config) |
| Delayed consequence | Failure only manifests after several subsequent steps |
| Recoverable failure | Agent can undo or correct the error within the window |
| Irreversible boundary | Failure crosses a point of no return (submit, send, delete) |
| Cross-application state | Failure affects or requires state in a different application |
| External interruption | External event changes state mid-trajectory |

**Minimum per category:** at least 2 tasks.

### 6.3 Annotation Procedure

For each trajectory:

1. **Fast scan:** Identify \(t^*\) (first consequential failure)
2. **Causal window annotation:** Annotate \([t^* - 2, t^* + K]\) where \(K\) ends at the first of:
   - Agent detects failure
   - Agent successfully recovers
   - Failure becomes irreversible
   - Failure clearly propagates to later steps
   - Trajectory ends
3. **Type classification:** Apply decision tree from Section 3.2
4. **RQ2 elicitation:** Run C0-C3 cascade on \(t^*\)
5. **Role intervention:** Run C2-Self/Other/Neutral on \(t^*\)

**Annotation cost per trajectory:** O(1), not O(T).

### 6.4 Pilot Kill Criteria

| # | Signal | Action |
|---|---|---|
| Kill 1 | >80-90% of failures are Selection type; Oracle Recognition barely improves success | Pause this research direction |
| Kill 2 | Nearly all failures are immediately self-detected at C0 | Study recovery instead of recognition |
| Kill 3 | Undetected failures only appear under artificial corruption, not natural trajectories | Reframe as robustness study |

### 6.5 Pilot Go Criteria

| # | Signal | Action |
|---|---|---|
| Go 1 | Natural long-horizon trajectories show Failure → NotDetected → Continue patterns | Strong signal for RQ2 |
| Go 2 | Oracle Recognition substantially improves final task success | Confirms recognition as bottleneck |
| Go 3 | Action errors decrease with model capability but UFR decreases more slowly | **Reliability Bottleneck Shift confirmed** |

---

## 7 Metrics Summary

### 7.1 Per Trajectory

| Symbol | Name | Type |
|---|---|---|
| \(t^*\) | First consequential failure step | Integer |
| \(\text{Type}(t^*)\) | First failure type | Categorical |
| \(D_0\) | Spontaneous detection | Boolean |
| \(D_1, D_2, D_3\) | Detection under C1, C2, C3 | Boolean each |
| \(D_{\text{self}}, D_{\text{other}}, D_{\text{neutral}}\) | Self-attribution conditions | Boolean each |
| \(W_r\) | Recovery window | Integer |
| \(DD\) | Detection delay | Integer |
| \(RS\) | Recovery success | Boolean |

### 7.2 Aggregate Metrics

| Metric | Formula | Interpretation |
|---|---|---|
| First-Failure Type Distribution | \(P(\text{type} \mid \text{failure})\) | Where do agents fail first? |
| Undetected Failure Rate | \(\bar{UFR} = \frac{1}{N}\sum UFR_i\) | How often do failures go unnoticed? |
| Gap Decomposition | \(G_{\text{trigger}}, G_{\text{rep}}, G_{\text{obs}}\) | What blocks detection? |
| Oracle Lift | \(\Delta_{\text{sel}}, \Delta_{\text{recog}}, \Delta_{\text{recover}}\) | Which bottleneck matters most? |
| Bottleneck Shift Index | Correlation(model capability, bottleneck type) | Does the bottleneck migrate with scaling? |

---

## 8 Ethical and Scope Constraints

### 8.1 What Paper 1 Does NOT Claim

- Paper 1 does **not** claim "RLHF causes models not to admit failures" — this is deferred to Paper 2 with controlled experiments
- Paper 1 does **not** claim all agents have a self-monitoring problem — failure modes vary by capability level and task type
- Paper 1 does **not** claim to solve reliability — it is a diagnostic contribution

### 8.2 What Paper 1 Does Claim

- A causal decomposition of where long-horizon agent reliability breaks down
- An empirical measurement of failure awareness under controlled conditions
- An oracle intervention study showing which bottleneck most impacts final task success
- An exploratory analysis of whether the bottleneck shifts with model capability

### 8.3 Citation Obligations

This protocol references three empirical findings from the literature:

1. **Self-attribution asymmetry:** 2026 work showing identical error content framed as "own reasoning" vs "external source" produces different self-correction rates — evidence that self-correction failure involves attribution beyond pure capability
2. **Training reward conflicts:** OpenAI "confessions" work demonstrating that adding honest failure reporting as an explicit reward target reduces false negatives in behavioral violations — motivation for separating capability from training objective
3. **Self-rewarding RL bias:** ICML 2026 finding of self-confirming bias in self-rewarding RL — evidence that RL training can create situations where high-confidence errors receive high self-reward

These references should be cited precisely and with appropriate hedging when the self-attribution asymmetry finding is discussed.

---

## 9 Document History

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2026-10-01 | Initial protocol based on Paper 1 framework discussion |

