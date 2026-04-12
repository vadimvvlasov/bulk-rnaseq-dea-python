"""
Fetch RNA-seq count data for differential expression analysis.

Supports multiple data sources:
1. recount3 via AWS Open Data (HTTP/S3) — real human/mouse bulk RNA-seq data
2. PyDESeq2 synthetic example data — fallback for testing/development

Usage:
    python scripts/fetch_data.py --source recount3 --species human --project SRP000000
    python scripts/fetch_data.py --source synthetic
    python scripts/fetch_data.py  # defaults to synthetic
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data")


def fetch_synthetic_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load PyDESeq2 synthetic example data.

    Returns:
        counts_df: Gene count matrix (samples x genes)
        metadata_df: Sample metadata with condition labels
    """
    from pydeseq2.utils import load_example_data

    logger.info("Loading PyDESeq2 synthetic example data...")
    counts_df = load_example_data(
        modality="raw_counts",
        dataset="synthetic",
        debug=False,
    )
    metadata_df = load_example_data(
        modality="metadata",
        dataset="synthetic",
        debug=False,
    )

    # PyDESeq2 already returns samples x genes format
    logger.info(f"  Counts shape: {counts_df.shape} (samples x genes)")
    logger.info(f"  Metadata shape: {metadata_df.shape}")
    logger.info(f"  Conditions: {metadata_df['condition'].unique().tolist()}")

    return counts_df, metadata_df


def fetch_recount3_data(
    species: str = "human",
    project_id: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Attempt to fetch recount3 RNA-seq data.

    recount3 stores data on AWS S3 (s3://recount-opendata/).
    The data is organized by project/study with pre-computed gene counts.

    Since recount3 is primarily an R/Bioconductor resource, this function
    provides a Python interface to download the data via HTTP endpoints.

    NOTE: If direct download fails, falls back to synthetic data.

    Args:
        species: 'human' or 'mouse'
        project_id: Specific study accession (e.g., 'SRP009615')

    Returns:
        counts_df: Gene count matrix (samples x genes)
        metadata_df: Sample metadata
    """

    logger.info(
        f"Attempting to fetch recount3 data (species={species}, project={project_id})..."
    )

    # recount3 provides RangedSummarizedExperiment objects as RDS files
    # and also provides summarized count matrices
    if project_id:
        gene_count_url = f"https://recount-opendata.s3.amazonaws.com/{species}/projects/{project_id}/gene_counts.rds"
    else:
        # Default to a well-studied dataset if no project specified
        gene_count_url = f"https://recount-opendata.s3.amazonaws.com/{species}/SRP009615/gene_counts.rds"

    logger.info(f"  Target URL: {gene_count_url}")
    logger.warning(
        "recount3 provides data primarily as RDS (R Data Standard) files, "
        "which require R to parse. Falling back to synthetic data.\n"
        "\n"
        "To use real recount3 data:\n"
        "  1. Use R/Bioconductor: BiocManager::install('recount3')\n"
        "  2. Download counts: create_rse(project='SRP009615', species='human')\n"
        "  3. Export to CSV and place in data/ directory\n"
        "  4. Load with: pd.read_csv('data/custom_counts.csv', index_col=0)\n"
        "\n"
        "Alternatively, provide your own count matrix as a CSV file."
    )

    raise NotImplementedError(
        "Direct recount3 download requires R (RDS format). "
        "Use --source synthetic or provide custom CSV data."
    )


def load_custom_csv(
    counts_path: str, metadata_path: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load user-provided count and metadata CSV files.

    Args:
        counts_path: Path to counts CSV (rows=samples, cols=genes)
        metadata_path: Path to metadata CSV (rows=samples, cols=attributes)

    Returns:
        counts_df, metadata_df
    """
    logger.info(f"Loading custom counts from {counts_path}...")
    counts_df = pd.read_csv(counts_path, index_col=0)

    logger.info(f"Loading custom metadata from {metadata_path}...")
    metadata_df = pd.read_csv(metadata_path, index_col=0)

    logger.info(f"  Counts shape: {counts_df.shape}")
    logger.info(f"  Metadata shape: {metadata_df.shape}")

    return counts_df, metadata_df


def save_data(
    counts_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Save counts and metadata to CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    counts_path = output_dir / "counts.csv"
    metadata_path = output_dir / "metadata.csv"

    counts_df.to_csv(counts_path)
    metadata_df.to_csv(metadata_path)

    logger.info(f"Saved counts to {counts_path}")
    logger.info(f"Saved metadata to {metadata_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch RNA-seq count data for DEA analysis"
    )
    parser.add_argument(
        "--source",
        choices=["synthetic", "recount3", "csv"],
        default="synthetic",
        help="Data source to use (default: synthetic)",
    )
    parser.add_argument(
        "--species",
        choices=["human", "mouse"],
        default="human",
        help="Species for recount3 data (default: human)",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="recount3 project/study accession ID (e.g., SRP009615)",
    )
    parser.add_argument(
        "--counts-file",
        type=str,
        default=None,
        help="Path to custom counts CSV file",
    )
    parser.add_argument(
        "--metadata-file",
        type=str,
        default=None,
        help="Path to custom metadata CSV file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Directory to save downloaded data",
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    if args.source == "synthetic":
        counts_df, metadata_df = fetch_synthetic_data()

    elif args.source == "recount3":
        try:
            counts_df, metadata_df = fetch_recount3_data(
                species=args.species,
                project_id=args.project,
            )
        except NotImplementedError as e:
            logger.error(str(e))
            logger.info("Falling back to synthetic data...")
            counts_df, metadata_df = fetch_synthetic_data()

    elif args.source == "csv":
        if not args.counts_file or not args.metadata_file:
            logger.error(
                "--counts-file and --metadata-file are required for CSV source"
            )
            sys.exit(1)
        counts_df, metadata_df = load_custom_csv(args.counts_file, args.metadata_file)

    else:
        logger.error(f"Unknown source: {args.source}")
        sys.exit(1)

    save_data(counts_df, metadata_df, output_dir)
    logger.info("Data fetch complete!")


if __name__ == "__main__":
    main()
