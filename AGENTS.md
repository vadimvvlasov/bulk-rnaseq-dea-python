# AGENTS.md

## Quick Commands

```bash
uv sync                    # Install dependencies
uv run python scripts/fetch_data.py              # Fetch synthetic data (default)
uv run python scripts/fetch_data.py --source csv --counts-file X --metadata-file Y  # Custom CSV
uv run jupyter notebook rnaseq_deseq2.ipynb      # Run analysis notebook
```

## Project Structure

- `rnaseq_deseq2.ipynb` — main analysis notebook (not Python scripts)
- `scripts/fetch_data.py` — data fetching pipeline
- `data/` — counts.csv + metadata.csv (generated)
- `figures/` — visualizations (generated)
- `results/` — DEA results (generated)

## Key Details

- **Package manager**: `uv` (not pip/poetry)
- **Python**: >= 3.11
- **Analysis library**: PyDESeq2
- **Data format**: counts = samples × genes (rows=samples, cols=genes)
- **Metadata**: must have `condition` column for comparison groups

## Data Sources

| Source | Usage | Notes |
|--------|-------|-------|
| synthetic | `--source synthetic` | Default; loads built-in PyDESeq2 example |
| custom CSV | `--source csv --counts-file X --metadata-file Y` | Your own data |
| recount3 | `--source recount3` | Falls back to synthetic; requires R for real data |

## Output Files

- `data/counts.csv` — raw count matrix
- `data/metadata.csv` — sample metadata
- `figures/*.png` — MA, volcano, PCA, p-value plots
- `results/deseq2_results.csv` — all genes with stats
- `results/significant_degs.csv` — padj < 0.05 only
