# Reproducibility

## Code Availability

All code is in this repository:
- `scripts/` - Analysis scripts
- `annotation_tool/` - Streamlit annotation interface
- `src/` - Core library

## Data Availability

- OSWorld trajectories: HuggingFace `xlangai/ubuntu_osworld_verified_trajs`
- Human annotations: `data/human_annotations/annotations.jsonl`

## Running the Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Download data
python scripts/download_data.py

# Run annotation
streamlit run annotation_tool/app.py

# Analyze results
python scripts/phase32_regenerate_rq1.py
```

## Seed and Randomness

- Trajectory selection: Deterministic (score-based priority)
- Synthetic annotations: Random seed fixed for reproducibility
- Real experiments: Random seed documented per run

## Computational Requirements

- Annotation: Manual (no compute)
- RQ1 analysis: < 1 minute
- RQ2 API: Depends on API rate limits
- Oracle experiments: Significant GPU time

---

*Documented: 2026-10-02*
