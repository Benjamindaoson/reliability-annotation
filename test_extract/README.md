# Paper 1: Do Agents Know When They Fail?

**A Causal Decomposition of Long-Horizon Agent Reliability**

## Project Overview

This repository contains the experimental pipeline for analyzing agent failure patterns in long-horizon computer tasks using OSWorld trajectories.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Download OSWorld trajectories
python scripts/download_data.py

# Inspect dataset
python scripts/inspect_dataset.py --path data/raw/

# Run full analysis pipeline
python scripts/analyze_trajectories.py --path data/raw/ --output results/

# Generate experimental reports
python scripts/generate_report.py

# Generate paper figures
python scripts/generate_paper_figures.py
```

## Project Structure

```
Reliability-Bottleneck-Shift/
├── data/
│   ├── annotations/           # Human annotation files
│   ├── external/              # Downloaded datasets
│   │   └── osworld_verified/  # OSWorld verified trajectories
│   ├── processed/              # Normalized/converted data
│   └── raw/                   # Raw trajectory data
├── src/
│   └── trajectory_analyzer/   # Core analysis library
│       ├── analysis/          # Statistical analysis
│       ├── data_loader/        # Dataset loading
│       ├── export/            # Annotation export
│       └── trajectory/         # Schema and normalization
├── scripts/                   # CLI entry points
│   ├── analyze_rq1.py         # RQ1: Failure distribution
│   ├── analyze_rq2.py         # RQ2: Detection analysis
│   ├── analyze_self_attribution.py
│   ├── analyze_oracle_intervention.py
│   ├── convert_osworld.py     # Format converter
│   ├── evaluate_localization.py
│   ├── export_annotations.py
│   ├── generate_failure_dataset.py
│   ├── generate_paper_figures.py
│   ├── generate_report.py
│   ├── inspect_dataset.py
│   └── download_data.py
├── annotation_tool/           # Streamlit annotation interface
├── paper_figures/             # Generated figures
├── results/                  # Analysis outputs
└── tests/                   # Unit tests (63 passing)
```

## Research Questions

### RQ1: Where do agents fail?
- Failure type distribution (selection, execution, recognition, recovery)
- Failure position in trajectory
- Detection rate by failure type

### RQ2: Do agents know when they fail?
- C0-C3 elicitation protocol
- Detection gap analysis
- Bottleneck decomposition (G_trigger, G_representation, G_observability)

### RQ3: Oracle intervention effects
- Selection/Execution/Recognition/Recovery intervention
- Success rate improvements

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `inspect_dataset.py` | Inspect dataset schema and statistics |
| `analyze_trajectories.py` | Full trajectory analysis with candidate detection |
| `export_annotations.py` | Export trajectories for human annotation |
| `evaluate_localization.py` | Evaluate candidate detection against human labels |
| `generate_failure_dataset.py` | Create failure decomposition dataset |
| `analyze_rq1.py` | RQ1 failure distribution analysis |
| `analyze_rq2.py` | RQ2 detection gap analysis |
| `convert_osworld.py` | Convert OSWorld format to unified schema |
| `generate_paper_figures.py` | Generate all paper figures |
| `generate_report.py` | Generate experimental report |

## Annotation Tool

Launch the Streamlit annotation interface:

```bash
streamlit run annotation_tool/app.py
```

Annotators can view trajectories and label:
- First consequential failure step
- Failure type (selection/execution/recognition/recovery)
- Confidence level
- Notes

## Current Status

### Implemented
- ✅ Dataset loading (JSON, JSONL, ZIP, GZIP, directories)
- ✅ Trajectory normalization
- ✅ Schema inspection
- ✅ Candidate failure detection
- ✅ Annotation export
- ✅ Streamlit annotation tool
- ✅ RQ1 analysis
- ✅ RQ2 analysis (offline heuristics)
- ✅ Oracle intervention analysis
- ✅ Self-attribution analysis
- ✅ Paper figure generation
- ✅ Experimental report generation
- ✅ 63 unit tests passing

### Data Available
- ✅ OSWorld verified trajectories (claude-4-sonnet-15steps) downloaded
- ⏳ Additional model trajectories (need more downloads)
- ⏳ Human-agent comparison data

### Pending
- ⏳ Full-scale human annotation
- ⏳ Actual RQ2 elicitation experiments (requires API access)
- ⏳ Oracle intervention experiments
- ⏳ Localization evaluation (requires annotations)

## Limitations

1. **Sample Size**: Current analysis based on sample data
2. **Offline Analysis**: RQ2 results are heuristic-based, not actual model queries
3. **Simulated Effects**: Oracle and self-attribution results are simulated frameworks
4. **No Actual Experiments**: Full validation requires running trajectories with interventions

## Research Integrity

This infrastructure:
- ❌ Does NOT fabricate results
- ❌ Does NOT claim RLHF causes behavior
- ❌ Does NOT assume reasoning = internal belief
- ✅ Distinguishes observed vs inferred
- ✅ Reports limitations clearly
