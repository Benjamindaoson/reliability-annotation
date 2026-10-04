# Calibration Protocol - Real Data (v3)

## 当前状态

- Prompt v3 已更新（加入 onset definition 和 justification 字段）
- Report Generator 已更新（加入 ±2 diagnostic metrics）
- Gate 保持不变

---

## Gate Criteria (Primary)

| Metric | Threshold |
|--------|-----------|
| Label Agreement Rate | ≥ 0.8 |
| Onset-Step Agreement (±1) | ≥ 0.8 |

## Diagnostic Metrics

| Metric | Purpose |
|--------|---------|
| Onset-Step Agreement (±2) | Sensitivity analysis |
| Avg Step MAE | Onset precision |
| Class 1/2/3 distribution | Disagreement root cause |

---

## 真实 Calibration 流程

### Step 1: 用 Prompt v3 标注 Batch 001

**Prompt 文件：** `templates/failure_annotation_prompt.md`

**关键变化：**
1. 新增 onset step operational definition
2. 强制回答 `why_qualifies` 和 `why_preceding_not`
3. Causal analysis first, then label

**标注输出格式：**
```json
{
  "trajectory_id": "...",
  "annotator_id": "claude-3-5-sonnet",
  "annotator_model": "claude-3-5-sonnet-20241022",
  "annotator_type": "LLM",
  "timestamp": "2026-10-03T...",
  "trajectory_hash": "...",

  "causal_analysis": {
    "first_failure_step": 2,
    "what_happened": "...",
    "why_consequential": "...",
    "why_this_step": "...",
    "why_qualifies": "Why does step N qualify as onset?",
    "why_preceding_not": "Why does step N-1 NOT qualify?"
  },

  "label": {
    "type": "SELECTION",
    "confidence": 0.85,
    "reasoning": "..."
  },

  "agent_awareness": {...},
  "evidence_steps": [...],
  "evidence_text": "..."
}
```

### Step 2: Import 标注

```bash
# 标注后生成 JSONL 文件，然后：
python scripts/import_annotations.py --file YOUR_ANNOTATIONS.jsonl --source claude --annotator_id MODEL_NAME
```

### Step 3: 生成 Report

```bash
python scripts/generate_calibration_report.py
```

### Step 4: 解读结果

**Gate Pass:**
- Label Agreement ≥ 80%
- Onset-Step ±1 ≥ 80%
- → 继续扩展到 30-50 条

**Gate Fail:**
- 分析 disagreement class 分布
- Class 3 为主 → 修改 ontology
- Class 2 为主 → 这是正常的 onset boundary uncertainty
- Class 1 为主 → 统一命名

---

## Batch 001 数据

10 条轨迹：`annotation_batches_calibration/batch_001.json`

| # | Trajectory ID | Task | Steps |
|---|---------------|------|-------|
| 1 | libreoffice_writer/3ef2b35... | libreoffice_writer | 4 |
| 2 | libreoffice_writer/72b810ef... | libreoffice_writer | 10 |
| 3 | libreoffice_calc/30e3e107... | libreoffice_calc | 15 |
| 4 | libreoffice_writer/f178a4a9... | libreoffice_writer | 15 |
| 5 | multi_apps/869de13e... | multi_apps | 15 |
| 6 | multi_apps/aceb0368... | multi_apps | 15 |
| 7 | thunderbird/9bc3cc16... | thunderbird | 15 |
| 8 | gimp/5ca86c6f... | gimp | 15 |
| 9 | vlc/9195653c... | vlc | 15 |
| 10 | libreoffice_calc/7efeb4b1... | libreoffice_calc | 15 |

---

## 决策树

```
Real Calibration Report Generated
              |
              v
        Gate Pass?
         /        \
       Yes         No
        |           |
        v           v
   Expand to     Analyze Class Distribution
   30-50 more        |
                    /   |   \
                 C1     C2    C3
                  |      |      |
                 Naming  Accept  Revise
                 Issue   Boundary Ontology
```

---

## 注意事项

1. **独立盲标** - 三个模型不能互相看到结果
2. **真实数据** - 不要用模拟 bias
3. **保留 justification** - `why_qualifies` 和 `why_preceding_not` 字段是诊断关键
4. **不调 Gate** - 无论诊断指标如何，Gate 阈值不变
