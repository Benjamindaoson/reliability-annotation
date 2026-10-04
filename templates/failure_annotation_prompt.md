# Failure Annotation Prompt
# Paper 1: Do Agents Know When They Fail?

**Version:** v2
**Date:** 2026-10-02
**Purpose:** Guide LLM/Human annotators to classify failure types in OSWorld trajectories

---

## Core Principle: Causal Attribution First, Classification Second

Your task is **NOT** to classify. Your task is **causal attribution**.

Before assigning any label, you MUST trace the causal chain:
1. What happened?
2. Why does this affect the future trajectory?
3. What label best explains this causal chain?

---

## Task Overview

You will analyze a trajectory of an AI agent attempting to complete a task in a computer environment.
Your goal is to identify the **first consequential failure** and classify its type.

**Critical principle:** Every label must be grounded in observable evidence from the trajectory.

---

## Output Format

Output **ONLY** a valid JSON object with the following structure:

```json
{
  "trajectory_id": "the trajectory identifier",
  "annotator_id": "your identifier (e.g., claude-3-5-sonnet, gpt-4o, human_annotator_01)",
  "annotator_model": "model used (e.g., claude-3-5-sonnet-20241022, gpt-4o-20241113, or 'human')",
  "annotator_type": "LLM or HUMAN",
  "timestamp": "ISO 8601 timestamp",
  "trajectory_hash": "sha256 hash of trajectory content",

  "causal_analysis": {
    "first_failure_step": 2,
    "what_happened": "Description of the failure event",
    "why_consequential": "Explanation of how this failure affects subsequent trajectory state",
    "why_this_step": "Why this is the FIRST consequential failure, not an earlier/later step",
    "why_qualifies": "Why does this step qualify as the onset? (must be erroneous action itself)",
    "why_preceding_not": "Why does the immediately preceding step NOT qualify?"
  },

  "label": {
    "type": "RECOGNITION",
    "confidence": 0.85,
    "reasoning": "Brief explanation connecting causal analysis to classification"
  },

  "agent_awareness": {
    "detected": "NO",
    "detection_step": null,
    "evidence": "Description of whether/when agent acknowledged failure"
  },

  "evidence_steps": [2, 3, 4],
  "evidence_text": "At step 2, the agent clicked on X instead of Y. At step 3, the agent continued without acknowledging the error...",
  "annotator_notes": "Optional notes about edge cases or uncertainties"
}
```

**IMPORTANT:** The `causal_analysis` field is REQUIRED. Do not skip directly to the label.

---

## Failure Type Definitions

### SELECTION
**Definition:** The agent selected the **WRONG action** given the available information.

**Evidence indicators:**
- Agent chose an action that clearly does not help achieve the goal
- Agent clicked on the wrong element/area
- Agent took an action that contradicts the task objective

**Example:** Task is "open the File Manager" but agent clicks on "Trash" icon instead.

---

### EXECUTION
**Definition:** The agent selected the **CORRECT action** but the environment **failed to execute it properly**.

**Evidence indicators:**
- Agent's intended action was correct
- Environmental error (wrong coordinates, command syntax, etc.)
- The action was properly executed but with wrong parameters

**Example:** Agent wanted to click at (100, 200) but the click happened at (100, 250).

---

### RECOGNITION
**Definition:** The outcome was **WRONG** but the agent **did not notice it**.

**Evidence indicators:**
- Agent continued acting as if nothing was wrong
- No acknowledgment of failure in subsequent steps
- Agent proceeded with incorrect state

**Example:** Agent saved a file to the wrong location but reported "File saved successfully" without noticing the error.

---

### RECOVERY
**Definition:** The agent **detected the failure** but **failed to recover properly**.

**Evidence indicators:**
- Agent explicitly acknowledged failure (e.g., "that didn't work", "let me try again")
- Agent attempted to fix the error
- The recovery attempt was incorrect or insufficient

**Example:** Agent said "I clicked the wrong button, let me redo" and clicked the adjacent button instead.

---

### UNCERTAIN
**Definition:** Cannot determine the failure type with confidence.

**When to use:**
- Insufficient evidence
- Multiple possible interpretations
- Trajectory is ambiguous

**Required:** Provide `confidence: 0.3` or lower and explain uncertainty in `annotator_notes`.

---

## Step-by-Step Analysis Protocol

### Step 1: Understand the Task
Read the task description carefully.
- What is the goal?
- What are the success criteria?

### Step 2: Scan the Trajectory
Go through each step chronologically:
- What action did the agent take?
- What was the result?
- Was the result expected?

### Step 3: Identify Candidate Failures
Look for steps where:
- The action result differs from expectation
- The agent shows confusion or uncertainty
- The trajectory diverges from optimal path

### Step 4: Locate the First Consequential Failure
Find the **first step** where:
- A failure occurred
- This failure causally affects subsequent steps
- The trajectory cannot recover without addressing this failure

**Note:** Not every wrong action is consequential. A minor detour that self-corrects is not a "first consequential failure."

## Onset Step Definition (CRITICAL)

**Choose the earliest action or execution event that is itself erroneous and whose correction would plausibly prevent the downstream deviation.**

**RULES:**
1. Do NOT choose an earlier precursor that was still valid
2. Do NOT choose a later visible consequence if the causal error occurred earlier
3. The onset step must be an **action itself** (not a state or observation)

**Annotator MUST answer:**
- **Why does this step qualify as the onset?**
- **Why does the immediately preceding step NOT qualify?**

### Example

```
Step 1: open menu           <- valid action
Step 2: select wrong item   <- ONSET (first erroneous action)
Step 3: wrong dialog opens  <- consequence
```

**Correct answer:** t* = 2
**Common errors:**
- t* = 1 (precursor was valid, not erroneous)
- t* = 3 (visible consequence, not the causal error itself)

### Step 6: Document Evidence
For each classification:
- List the specific steps that support the classification
- Quote or paraphrase relevant agent reasoning
- Note any ambiguity or edge cases

### Step 7: Assess Confidence
Rate your confidence (0.0 to 1.0):
- 0.9-1.0: Very confident, clear evidence
- 0.7-0.9: Confident, good evidence
- 0.5-0.7: Somewhat confident, some ambiguity
- 0.3-0.5: Uncertain, significant ambiguity
- 0.0-0.3: Very uncertain, use UNCERTAIN type

---

## Evidence Requirements

**CRITICAL:** Without evidence, a label is invalid.

Your `evidence_text` must include:
1. **What happened** at the failure step
2. **Why it was a failure** (reference to task goal)
3. **Why the classification** is correct (reference to failure type definition)
4. **Agent awareness** (or lack thereof) in subsequent steps

If you cannot provide evidence, use `UNCERTAIN` with low confidence.

---

## Common Pitfalls to Avoid

### 1. Assuming hidden mental states
Only infer what the agent "knew" based on observable actions and explicit statements.

### 2. Forcing classification
If ambiguous, use UNCERTAIN rather than guessing.

### 3. Confusing selection and execution
- SELECTION = wrong choice
- EXECUTION = right choice, wrong execution

### 4. Missing the first consequential failure
The first failure may not be the most obvious one. Scan carefully.

### 5. Ignoring recovery attempts
Look for evidence of the agent trying to fix mistakes.

---

## Example Analysis

### Trajectory
```
Task: Open the file "report.txt" in LibreOffice Writer
Step 1: Agent opens LibreOffice Writer ✓
Step 2: Agent clicks File → Open ✓
Step 3: Agent types "report" in search box ✓
Step 4: Agent clicks "report.pdf" (wrong file!) ← FIRST FAILURE
Step 5: Agent clicks Open
Step 6: Error: "Cannot open PDF in Writer"
Step 7: Agent clicks OK, continues ← NO AWARENESS
```

### Causal Analysis (Required First)
```
Step 4: what_happened = "Agent selected 'report.pdf' from search results"
Step 4: why_consequential = "The wrong file extension causes step 6 error, and agent proceeds with wrong file state"
Step 4: why_this_step = "Step 4 is first wrong selection; steps 1-3 were correct"
```

### Annotation
```json
{
  "trajectory_id": "example_001",
  "annotator_id": "claude-3-5-sonnet",
  "annotator_model": "claude-3-5-sonnet-20241022",
  "annotator_type": "LLM",
  "timestamp": "2026-10-02T00:00:00Z",
  "trajectory_hash": "abc123",

  "causal_analysis": {
    "first_failure_step": 4,
    "what_happened": "Agent clicked on 'report.pdf' instead of 'report.txt' from search results",
    "why_consequential": "Wrong file type causes error at step 6, and agent proceeds with incorrect document state without recovery",
    "why_this_step": "Steps 1-3 were correct path actions. Step 4 is the first deviation from task goal."
  },

  "label": {
    "type": "SELECTION",
    "confidence": 0.9,
    "reasoning": "Agent had correct goal (open report.txt) but selected wrong file from available options. Not execution failure because the click worked correctly."
  },

  "agent_awareness": {
    "detected": "NO",
    "detection_step": null,
    "evidence": "Step 7 shows agent dismissed error and continued without acknowledging wrong file was selected"
  },

  "evidence_steps": [4, 5, 6, 7],
  "evidence_text": "At step 4, the agent clicked on 'report.pdf' instead of 'report.txt'. The task explicitly required opening 'report.txt'. At step 5, the agent clicked Open. At step 6, an error appeared. At step 7, the agent dismissed the error and continued without acknowledging the wrong file was selected.",
  "annotator_notes": ""
}
```

---

## Output Instructions

1. Analyze the provided trajectory following the protocol above
2. Output ONLY the JSON object (no markdown, no explanation)
3. Ensure the JSON is valid and complete
4. Include all required fields
5. If uncertain, set `failure_type` to "UNCERTAIN" and explain in `annotator_notes`

---

## Trajectory Data Format

The trajectory will be provided in the following format:

```json
{
  "trajectory_id": "...",
  "task_description": "...",
  "steps": [
    {
      "step_num": 1,
      "screenshot_file": "step_1.png",
      "action": {
        "type": "click",
        "coordinates": [x, y],
        "description": "..."
      },
      "observation": "...",
      "feedback": {
        "success": true/false,
        "reward": 0/-1,
        "message": "..."
      }
    },
    ...
  ]
}
```

---

**END OF PROMPT**
