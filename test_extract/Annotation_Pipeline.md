# Annotation Pipeline Overview

## Architecture

```
OSWorld Trajectories
        |
        v
[scripts/export_annotation_batches.py]
        |
        v
annotation_batches_calibration/batch_*.json
        |
        v
+--> Claude (manual) --> data/annotations/raw/claude/*.jsonl
+--> GPT/Codex (manual) --> data/annotations/raw/gpt/*.jsonl
+--> Gemini (manual) --> data/annotations/raw/gemini/*.jsonl
        |
        v
[scripts/import_annotations.py]
        |
        v
data/annotations/raw/{claude,gpt,gemini}/*.jsonl
        |
        v
[scripts/analyze_agreement.py]
        |
        v
results/annotation_agreement/agreement_report.json
        |
        +--- kappa > 0.7 ---> Expand to full 500+ trajectories
        |
        +--- kappa < 0.5 ---> Revise prompt/taxonomy
        |
        v
[scripts/generate_consensus.py]
        |
        +--> data/annotations/processed/consensus_labels.jsonl
        |
        +--> data/annotations/review/disagreement_queue.jsonl
```

## Calibration Protocol (v2)

### Gate Criteria

| Metric | Threshold | Action if Failed |
|--------|-----------|------------------|
| Label Agreement | ≥ 0.8 | Revise taxonomy |
| Onset-Step Agreement (±1 step) | ≥ 0.8 | Accept boundary cases |
| Systematic Category Confusion | None | Investigate ontology overlap |

### Agreement Metrics

1. **Exact Label Agreement** - All 3 annotators same label
2. **Pairwise Cohen's κ** - Pairwise failure type agreement
3. **Fleiss' κ** - Multi-rater agreement
4. **Onset-Step MAE** - Mean absolute error in first failure step
5. **Causal Chain Agreement** - Root cause reasoning consistency

### Disagreement Classification

| Class | Description | Action |
|-------|-------------|--------|
| **Class 1** | Same causal interpretation, different label name | Resolve naming |
| **Class 2** | Same failure type, different onset step | Accept (boundary) |
| **Class 3** | Completely different causal chains | Revise ontology |

### Adjudication Protocol

For all disagreement cases:
1. Identify: prompt ambiguity vs evidence insufficient vs ontology overlap vs annotator error
2. Class 3 cases only → modify schema
3. Document all decisions in calibration report

## File Structure

```
Reliability-Bottleneck-Shift/
├── src/annotation/
│   └── schema.py                 # Unified annotation schema
├── scripts/
│   ├── export_annotation_batches.py   # Export trajectories for annotation
│   ├── import_annotations.py         # Import LLM annotations
│   ├── analyze_agreement.py          # Calculate agreement metrics
│   └── generate_consensus.py         # Generate consensus labels
├── templates/
│   └── failure_annotation_prompt.md   # Annotation prompt for LLM/Human
├── annotation_batches/
│   └── batch_*.json                  # Export batches
├── data/annotations/
│   ├── raw/
│   │   ├── claude/                   # Claude annotations
│   │   ├── gpt/                      # GPT annotations
│   │   ├── gemini/                   # Gemini annotations
│   │   └── human/                    # Human annotations
│   ├── processed/
│   │   └── consensus_labels.jsonl    # Consensus labels
│   └── review/
│       └── disagreement_queue.jsonl  # Cases needing review
├── results/annotation_agreement/
│   └── agreement_report.json
└── tests/
    └── test_annotation_schema.py
```

## Quick Start

### 1. Export Trajectory Batch

```bash
python scripts/export_annotation_batches.py --num_batches 10 --batch_size 10
```

This creates `annotation_batches/batch_001.json`, `batch_002.json`, etc.

### 2. Annotate with LLM

1. Open `annotation_batches/batch_001.json`
2. Copy content to Claude/GPT/Gemini with the prompt from `templates/failure_annotation_prompt.md`
3. Export JSON results

### 3. Import Annotations

```bash
python scripts/import_annotations.py \
    --file claude_batch001.jsonl \
    --source claude \
    --annotator_id claude-3-5-sonnet \
    --model claude-3-5-sonnet-20241022
```

### 4. Analyze Agreement

```bash
python scripts/analyze_agreement.py
```

### 5. Generate Calibration Report

```bash
python scripts/generate_calibration_report.py
```

This generates:
- Calibration table (trajectory × annotator)
- Disagreement classification (Class 1/2/3)
- Gate pass/fail status

### 5. Generate Consensus

```bash
python scripts/generate_consensus.py
```

## Workflow

### Phase 1: Calibration (100 trajectories)
1. Export first 100 trajectories
2. Annotate with Claude, GPT, Gemini
3. Analyze agreement
4. If κ > 0.7, proceed to Phase 2

### Phase 2: Full Annotation (500+ trajectories)
1. Export remaining trajectories
2. Annotate with multiple models
3. Generate consensus
4. Review disagreements
5. Run RQ1/RQ2 analysis

## Data Provenance

Every annotation includes:
- `trajectory_hash`: SHA256 of trajectory content
- `annotator_type`: HUMAN, LLM, or HEURISTIC
- `annotator_model`: Model identifier
- `prompt_version`: Prompt version used
- `timestamp`: When annotation was created

## Quality Metrics

Key metrics to track:
- Fleiss κ for failure type (target: > 0.7)
- Exact match rate for first failure step
- Agreement rate by failure type
- Confidence calibration

## Status

- [x] Schema defined (v3 with onset justification fields)
- [x] Batch exporter implemented
- [x] Importer implemented (supports v1/v2/v3 formats)
- [x] Agreement analysis implemented
- [x] Consensus generator implemented
- [x] Calibration report generator implemented (with diagnostic metrics)
- [x] Tests passing
- [x] Calibration batches generated (100 trajectories in annotation_batches_calibration/)
- [ ] **Prompt v3 finalized** - ready for real annotation
- [ ] Batch 001 real calibration annotation (10 trajectories x 3 annotators)
- [ ] Gate evaluation (kappa >= 0.8, onset +-1 >= 0.8)
- [ ] Expansion decision (30-50 more if gate passed)
