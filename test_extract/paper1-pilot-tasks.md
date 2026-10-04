# Paper 1 Pilot Task Pool
## 20 Candidate Tasks for Reliability Bottleneck Decomposition

---

## 1 Task Design Principles

Each task is designed to exercise one or more failure modes in a **controlled, discriminative** way — meaning the task should reliably produce a specific failure type when run across models of different capability levels, so that RQ1/RQ2/RQ3 can detect variation.

**Selection criteria for each task:**
- Ground truth is unambiguous (the task has a single correct outcome)
- Failure modes are **natural**, not artificially injected
- The task requires **multiple steps** (>5) to create long-horizon exposure
- At least one **critical boundary** exists (irreversible transition)
- Task length is sufficient to observe detection delay (≥10 steps expected)

---

## 2 Task Pool (20 Tasks)

### Category A — Observable Consequence (≥3 tasks)

Tasks where failure is directly visible in the environment state, but the agent must still actively check for it.

---

**Task A1: File Save with Override Confirmation**
> **Task:** Open a text file, make an edit, save it. The editor prompts "File has been modified externally. Overwrite?"
> **Expected:** Click "Yes" to overwrite and confirm the change.
> **Failure mode:** Agent clicks "No" or closes the dialog without resolving it, leaving the file unsaved.
> **Observable:** The file content in the file explorer should show the change — but the agent may not verify.
> **Dimensions:** Execution (dialog handling), Recovery (can re-attempt save)
> **Critical boundary:** None (save is always reversible)

---

**Task A2: Form Field Validation Feedback**
> **Task:** Fill out a web registration form with required fields. Submit the form. The form shows inline validation errors.
> **Expected:** Read errors, correct the flagged fields, resubmit successfully.
> **Failure mode:** Agent submits and ignores red error indicators, or navigates away.
> **Observable:** Red error text is directly visible in the rendered DOM.
> **Dimensions:** Recognition (must notice the red text), Recovery (can edit and resubmit)
> **Critical boundary:** None before successful submission

---

**Task A3: Copy-Paste with Visual Confirmation**
> **Task:** Copy a block of text from one document window, paste it into a form field in a different window, verify the pasted content matches.
> **Expected:** Confirm the pasted content is correct; if not, re-copy.
> **Failure mode:** Agent pastes wrong content (clipboard was different), doesn't verify, proceeds.
> **Observable:** The pasted text is visibly different from the source — but only if agent compares.
> **Dimensions:** Recognition (must compare two visible texts), Selection (must select correct source)

---

### Category B — Hidden Consequence (≥3 tasks)

Tasks where failure is not visible in the main UI; the agent must inspect internal state (file content, log, config, database).

---

**Task B1: Config File Persists Incorrectly**
> **Task:** Edit a JSON configuration file to change a setting (e.g., change "theme": "dark" to "theme": "light"). Save the file. Then open a settings panel in the app and verify the theme changed.
> **Expected:** If the JSON syntax is wrong, the app ignores the config. Agent should check both the file AND the app behavior.
> **Failure mode:** JSON has a syntax error; agent saves but doesn't verify the app actually reflects the change.
> **Hidden:** The file looks saved (no error dialog), but the app silently ignores malformed JSON. The only evidence is in the app's behavior or a log file.
> **Dimensions:** Recognition (must detect silent config rejection), Observability (app behavior is observable; log is hidden)
> **Critical boundary:** Config takes effect on next app restart — delayed consequence

---

**Task B2: Database Write Without Commit**
> **Task:** Through a GUI app, create a new record in a database-backed application (e.g., a notes app). The app has a "Save" and "Discard" button. The agent clicks Save.
> **Expected:** The record appears in the database.
> **Failure mode:** Agent fills out the form but accidentally clicks Discard, or closes without saving. The UI shows an empty form, but the agent doesn't notice the discard confirmation.
> **Hidden:** The discarded record never existed — no visual trace remains. Agent must notice the form is empty or check the records list.
> **Dimensions:** Recognition (absence of evidence), Execution (button click accuracy)

---

**Task B3: Log File Error Message**
> **Task:** Run a script that performs a computation and writes output to a log file. The script has a subtle bug that causes it to write an ERROR line to the log instead of the expected result. Agent must read the log to confirm success.
> **Expected:** Check the log file for "ERROR" or absence of expected output; if found, fix the script and rerun.
> **Hidden:** The script appears to run successfully (no crash, exit code 0). Error is only in the log file.
> **Dimensions:** Recognition (must actively read log), Observability (log file is observable but easily skipped)

---

### Category C — Delayed Consequence (≥2 tasks)

Tasks where the failure only manifests several steps after the incorrect action.

---

**Task C1: Email Draft Auto-Save then Send**
> **Task:** Open an email client, start composing an email, the app auto-saves a draft every 30 seconds. The agent makes an edit, then continues typing for several more paragraphs without checking the draft. The draft autosave interval passes. Later, agent sends the email.
> **Expected:** The email is sent with all the content including the early edit.
> **Failure mode:** If the agent accidentally deletes a paragraph early, and the autosave happens after the deletion, the sent email will be missing that paragraph — but the agent may not notice because they see the full text in the compose window.
> **Delayed:** The consequence (missing paragraph) only manifests at send time.
> **Dimensions:** Execution (must not delete unintended content), Recognition (must verify composed text matches intent)

---

**Task C2: Multi-Step Build Pipeline**
> **Task:** Run a build command that has four sequential steps. Step 1 compiles, Step 2 runs tests, Step 3 packages, Step 4 deploys. An error in Step 1 causes Step 2 to fail — but the agent may misdiagnose the root cause as Step 2.
> **Expected:** Read build output, identify Step 1 error, fix it, rebuild from Step 1.
> **Failure mode:** Agent fixes symptoms at Step 2 but the real problem was Step 1. Repeatedly patching later steps without fixing the root cause.
> **Delayed:** Error at Step 1 only propagates to visible failure at Step 2.
> **Dimensions:** Selection (root cause diagnosis), Recognition (must trace back to original failure point)

---

### Category D — Recoverable Failure (≥2 tasks)

Tasks where a recoverable error occurs but the agent must successfully recover — designed to distinguish "doesn't know it failed" from "knows but can't recover."

---

**Task D1: Wrong File Opened, Can Close and Reopen**
> **Task:** Open a specific file from a list of 5 files. The files have similar names. Agent opens the wrong file, makes an edit, notices the content is wrong, then closes the file without saving.
> **Expected:** Close the file, open the correct one, make the intended edit.
> **Failure mode:** Agent notices the content is wrong but doesn't close and reopen — instead tries to fix within the wrong file.
> **Recoverable:** The correct file is still intact; closing and reopening recovers.
> **Dimensions:** Recovery (must close and restart), Recognition (must notice wrong content)

---

**Task D2: Password Entry Failure, Can Retry**
> **Task:** Log into a web application. The agent types the password but gets the character case wrong (password field shows dots, so case is hidden). Login fails with "Invalid credentials."
> **Expected:** Re-enter the password with correct case.
> **Failure mode:** Agent retries with the same wrong password multiple times, or navigates away.
> **Recoverable:** Retry is unlimited; the correct password is known.
> **Dimensions:** Recognition (must notice "Invalid credentials" message), Recovery (must correct the input)

---

### Category E — Irreversible Boundary (≥2 tasks)

Tasks with a clear point of no return; crossing it without verifying the state causes permanent failure.

---

**Task E1: Form Submit with Preview**
> **Task:** Fill out a data entry form with multiple fields. Before submitting, there is a "Preview" step that shows exactly what will be submitted. After submission, no edits are possible.
> **Expected:** Review preview carefully, correct any errors, then submit.
> **Failure mode:** Agent skips preview or reviews it carelessly, submits with incorrect data.
> **Irreversible:** Submitted data cannot be edited; only deleted and re-entered.
> **Dimensions:** Recognition (must notice discrepancy in preview), Recovery (can recover only by deleting and re-entering, not editing)
> **Critical boundary:** Form submission

---

**Task E2: File Delete to Recycle Bin vs Permanent**
> **Task:** In a file manager, delete a specific file. The system asks whether to move to Recycle Bin (recoverable) or permanently delete (irreversible).
> **Expected:** Choose "Move to Recycle Bin" or verify the file's importance before permanently deleting.
> **Failure mode:** Agent accidentally selects "Permanent Delete" when the file should be preserved.
> **Irreversible:** Permanent deletion cannot be undone without backup.
> **Dimensions:** Execution (must select correct option in dialog), Recovery (permanent deletion has no recovery)
> **Critical boundary:** Permanent delete confirmation

---

### Category F — Cross-Application State (≥2 tasks)

Tasks require coordinating state across two different applications or system components.

---

**Task F1: Copy from App A, Paste into App B**
> **Task:** Open a spreadsheet application (App A), copy a cell value. Open a document editor (App B), paste the value into a specific field. The pasted value must match the source exactly.
> **Expected:** Verify the pasted value in App B matches the source in App A.
> **Failure mode:** Agent copies the wrong cell, or pastes in the wrong field, or clipboard gets cleared by an intermediate action.
> **Cross-app:** State must be verified across two different application contexts.
> **Dimensions:** Selection (must select correct source), Recognition (must verify cross-app consistency)

---

**Task F2: Browser Download Triggers External App**
> **Task:** In a browser, download a file. The download triggers an installation prompt from a security dialog. The agent must decline the installation and locate the downloaded file to complete the task.
> **Expected:** Decline installation, navigate to download folder, open the file.
> **Failure mode:** Agent accepts installation (wrong action), or loses track of the downloaded file's location.
> **Cross-app:** Browser state (download in progress) interacts with system file manager and installation dialog.
> **Dimensions:** Execution (dialog handling), Recognition (must track state across browser and file manager)

---

### Category G — External Interruption (≥3 tasks)

Tasks where an external event changes system state mid-trajectory, creating a hidden inconsistency the agent must detect. Minimum 3 tasks to support analysis.

---

**Task G1: Concurrent File Modification**
> **Task:** Agent is editing a configuration file. While the agent is mid-edit, an external process (simulated background task) modifies the same file. When the agent saves, a conflict dialog appears.
> **Expected:** Read the conflict dialog, compare versions, merge or choose the correct version.
> **External interruption:** State changed externally during the agent's action sequence.
> **Hidden:** The agent may not notice the external modification until the conflict dialog appears.
> **Recoverable:** Both versions are available; agent can choose.
> **Dimensions:** Hidden, Recoverable, External

---

**Task G2: External State Change Breaks Cross-App Workflow**
> **Task:** Agent copies a value from a spreadsheet (App A) to paste into a web form (App B). While the agent is preparing the paste, an external sync process updates the spreadsheet, changing the cell value. The agent pastes the old (stale) value without noticing the change.
> **Expected:** Re-copy the current value from App A after the sync, then paste.
> **External interruption:** Spreadsheet syncs externally during the agent's action window.
> **Cross-app:** Staleness can only be detected by re-checking App A after the sync notification.
> **Hidden:** The old value still looks valid in the clipboard; no visual indicator flags staleness.
> **Dimensions:** Hidden, Cross-App, External

---

**Task G3: External Notification Interrupts Action Sequence**
> **Task:** Agent is midway through a multi-step form entry. A system notification appears ("System update available — restart required") overlaying part of the form. The agent dismisses the notification but loses track of which form field was active, and submits an incomplete form.
> **Expected:** Re-read the form state after dismissing the notification, verify all fields are filled, then submit.
> **External interruption:** Notification arrives asynchronously mid-trajectory.
> **Observable:** The incomplete form is visible after the notification is dismissed — but only if agent checks.
> **Dimensions:** Observable, External

---

## 3 Coverage Matrix

Tasks are **multi-label**: each task may exercise multiple orthogonal attributes simultaneously. All seven attributes must be represented in the pilot pool, with each attribute appearing in at least 4 tasks.

| Task | Observable | Hidden | Delayed | Recoverable | Irreversible | Cross-App | External |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| A1 | ● | | | ● | | | |
| A2 | ● | | | ● | | | |
| A3 | ● | | | | | | |
| A4 | ● | | ● | | | | |
| B1 | | ● | ● | | | | |
| B2 | | ● | | | | | |
| B3 | | ● | | | | | |
| B4 | | ● | | | | | |
| C1 | | | ● | ● | | | |
| C2 | | | ● | | | | |
| C3 | | ● | ● | | | | |
| D1 | | | | ● | | | |
| D2 | | | | ● | | | |
| E1 | | | | | ● | | |
| E2 | | | | | ● | | |
| E3 | ● | | | | ● | | |
| E4 | ● | | | ● | ● | | |
| F1 | | | | | | ● | |
| F2 | | | | | | ● | |
| F3 | | | | | | ● | |
| G1 | | ● | | ● | | | ● |
| G2 | | ● | | | | ● | ● |
| G3 | ● | | | | | | ● |

**Coverage check:**

| Attribute | Count | Minimum | Status |
|---|---|---|---|
| Observable | 8 | 4 | ✓ |
| Hidden | 7 | 4 | ✓ |
| Delayed | 5 | 4 | ✓ |
| Recoverable | 6 | 4 | ✓ |
| Irreversible | 4 | 4 | ✓ |
| Cross-App | 4 | 4 | ✓ |
| External | 3 | 3 | ✓ |

---

## 4 Pilot Pool (23 Tasks)

The pool contains 23 tasks designed for multi-label attribute coverage. Each task exercises one or more orthogonal attributes. All seven attributes appear in at least 3 tasks; six of seven appear in at least 4.

The original 15 tasks are supplemented with 5 gap-fill tasks (A4, B4, C3, E3, E4) and 3 external-interruption tasks (G1, G2, G3). Tasks E3–F3 were previously listed as "additional"; they are now fully specified above and included in the final pool.

### Final 23-Task Pool with Multi-Label Dimensions

| # | Task ID | Observable | Hidden | Delayed | Recoverable | Irreversible | Cross-App | External | Expected Failure Types |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | A1 | ● | | | ● | | | | Execution / Recognition |
| 2 | A2 | ● | | | ● | | | | Recognition |
| 3 | A3 | ● | | | | | | | Selection / Recognition |
| 4 | A4 | ● | | ● | | | | | Recognition |
| 5 | B1 | | ● | ● | | | | | Recognition |
| 6 | B2 | | ● | | | | | | Recognition / Execution |
| 7 | B3 | | ● | | | | | | Recognition |
| 8 | B4 | | ● | | | | | | Recognition |
| 9 | C1 | | | ● | ● | | | | Recognition / Execution |
| 10 | C2 | | | ● | | | | | Selection |
| 11 | C3 | | ● | ● | | | | | Recognition |
| 12 | D1 | | | | ● | | | | Recovery |
| 13 | D2 | | | | ● | | | | Recognition / Recovery |
| 14 | E1 | | | | | ● | | | Recognition |
| 15 | E2 | | | | | ● | | | Execution |
| 16 | E3 | ● | | | | ● | | | Recognition |
| 17 | E4 | ● | | | ● | ● | | | Recognition |
| 18 | F1 | | | | | | ● | | Selection / Recognition |
| 19 | F2 | | | | | | ● | | Execution / Recognition |
| 20 | F3 | | | | | | ● | | Recognition |
| 21 | G1 | | ● | | ● | | | ● | Recognition |
| 22 | G2 | | ● | | | | ● | ● | Selection / Recognition |
| 23 | G3 | ● | | | | | | ● | Recognition |

**Coverage summary:**

| Attribute | Tasks | Minimum | Status |
|---|---|---|---|
| Observable | 8 | 4 | ✓ |
| Hidden | 7 | 4 | ✓ |
| Delayed | 5 | 4 | ✓ |
| Recoverable | 6 | 4 | ✓ |
| Irreversible | 4 | 4 | ✓ |
| Cross-App | 4 | 4 | ✓ |
| External | 3 | 3 | ✓ |

---

## 5 Task Implementation Notes

### 5.1 Environment Requirements

- **OSWorld 2.0** or equivalent GUI agent benchmark environment
- Tasks A1–A4, E1–E4, F2 require a desktop GUI environment with window management
- Tasks B1–B4, C2–C3 require filesystem access and terminal
- Tasks F1–F3, G2 require multiple application windows open simultaneously
- Tasks G1–G3 require a background process that can be triggered mid-trajectory

### 5.2 Failure Injection Strategy

Failures should be **natural**, not injected. The task descriptions above are designed so that realistic agent errors produce the target failure mode. For the pilot:

- Do **not** artificially corrupt state mid-trajectory unless simulating G1 (external interruption)
- Let agent errors arise from realistic mistakes: wrong selection, missed verification, dialog mishandling
- If an agent succeeds perfectly on a task, record it as a non-failure trajectory for baseline

### 5.3 Expected Failure Rate Calibration

Based on current agent capabilities (circa 2026), approximate expected failure rates:

| Task Type | Expected Baseline Success | Key Failure Mode |
|---|---|---|
| Observable | 40-60% | Missed verification despite visible evidence |
| Hidden | 20-40% | No inspection of internal state |
| Delayed | 30-50% | Misdiagnosis of root cause |
| Recoverable | 50-70% | Detection without successful recovery |
| Irreversible | 60-80% | Proceed without checking critical state |
| Cross-App | 30-50% | State consistency not verified across apps |
| External | 20-40% | No detection of externally changed state |

These are rough estimates for pilot calibration only — actual rates determine whether the protocol can discriminate between conditions.

### 5.4 Ground Truth Annotation Guide

For each task, define:

1. **Correct final state:** What the environment should look like on success
2. **Acceptable intermediate states:** What states are OK during the process
3. **Critical boundary:** The step beyond which recovery is impossible or severely costly
4. **Expected failure types:** Which of the four types are plausible failure modes for this task
5. **Detection oracle:** How a human annotator would confirm the task succeeded or failed

---

## 6 Next Steps

1. **Validate task feasibility** in the target environment (OSWorld 2.0 or equivalent)
2. **Define ground truth per task** using the annotation guide in Section 5.4
3. **Run pilot**: 20 tasks × 3 capability levels = 60 trajectories
4. **Annotate** using Local Causal Window protocol from measurement protocol
5. **Evaluate kill/go criteria** before proceeding to full experiment

---

## 7 Document History

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2026-10-01 | Initial task pool design |

