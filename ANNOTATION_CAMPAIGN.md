# Human Annotation Campaign - Quick Start

## 目标
```
50条真实人工标注 → RQ1真实结果 → 决定论文方向
```

## 当前状态
- 基础设施：✅ 完成
- 人工标注：⏳ 0/200
- RQ1分析：⏳ 等待标注

---

## 第一步：启动标注工具

### 方式 A: Streamlit Web界面（推荐新手）

```bash
streamlit run annotation_tool/app.py
```

浏览器打开 http://localhost:8501

### 方式 B: 命令行批处理工具（推荐有经验者）

```bash
python scripts/batch_annotation_tool.py --batch annotation_batches/batch_001.json
```

---

## 标注流程

### 每个轨迹需要标注：

1. **First Failure Step** (第一步)
   - 第一个导致后果的失败步骤
   - 或选择 "No Failure"

2. **Failure Type** (失败类型)
   - SELECTION: 选错了动作
   - EXECUTION: 动作意图正确但执行失败
   - RECOGNITION: 结果错了但没注意到
   - RECOVERY: 检测到了但恢复失败

3. **Detection** (检测)
   - Agent是否明确承认了失败？
   - 需要引用证据

4. **Recovery** (恢复)
   - 是否尝试恢复？
   - 恢复成功了吗？

5. **Confidence** (置信度)
   - HIGH / MEDIUM / LOW

---

## 标注技巧

### SELECTION vs EXECUTION
- **SELECTION**: 动作本身错了（比如点击错误的按钮）
- **EXECUTION**: 动作对了但做错了（比如坐标错误）

### RECOGNITION是关键
- Agent是否明确说了"失败了"、"没有成功"？
- 还是继续假设一切正常？

### 检测证据要求
- 必须引用轨迹中的实际文本
- 不能推断隐藏信念
- 只能使用明确的证据

---

## 实时进度

```bash
python scripts/annotation_progress_tracker.py
```

查看：
- 已标注数量
- 失败类型分布
- 检测率 (UFR)

---

## 质量控制

### 每10条标注后运行：
```bash
python scripts/phase30_annotation_qc.py
```

检查：
- 缺失字段
- 无效标签
- 不可能的时间戳
- 检测在失败之前

---

## 达到50条后

```bash
python scripts/run_human_analysis.py
```

这将自动：
1. 生成RQ1真实结果
2. 检查Thesis Gate
3. 选择RQ2候选案例

---

## 文件结构

```
data/human_annotations/
└── annotations.jsonl    # 所有标注保存在这里

annotation_batches/
├── batch_001.json       # 优先标注批次1
├── batch_002.json       # 批次2
└── annotation_queue.json

results/
├── annotation_progress.json
├── annotation_progress.md
└── RQ1_human_first50/   # 分析结果
```

---

## 重要规则

❌ **不要做：**
- 创建synthetic annotations
- 用LLM推断标签
- 生成假结果
- 修改研究定义

✅ **只做：**
- 真实人工标注
- 观察到的证据
- 如实报告

---

## Thesis Gate

论文方向取决于：

**条件 1:** UFR > 0
- 存在未被检测到的失败

**条件 2:** Selection ≈ 40%
- 选择失败占主导

**如果两者都为真 → 继续Paper 1**
**如果为假 → 调整方向**

---

## 常见问题

**Q: 标注错了怎么办？**
A: 编辑 `data/human_annotations/annotations.jsonl`

**Q: 两个失败类型都像怎么办？**
A: 选择最早发生的那个

**Q: 没有明确的检测证据？**
A: 选择 "NO" 并在notes中说明

**Q: 轨迹太复杂？**
A: 选择 "UNCLEAR" 并跳过

---

## 联系方式

标注过程中遇到问题，请参考：
- `annotation_tool/README.md`
- `paper/paper_status.md`
