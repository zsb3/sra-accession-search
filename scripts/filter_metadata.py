#!/usr/bin/env python3
"""Filter SRA metadata based on coverage and quality criteria.

This script processes the JSON output from search_sra.py and filters
accessions based on estimated coverage, instrument type, and other
quality metrics.

Usage:
    python filter_metadata.py \
        --input data/salmonella_metadata.json \
        --output results/salmonella_filtered.csv \
        --min-coverage 50 \
        --max-coverage 250
"""

import json
import argparse
import pandas as pd
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from schemas import SRASearchResult
from tqdm import tqdm

try:
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    from botocore.exceptions import ClientError, NoCredentialsError

    BOTO3_AVAILABLE = True
except ImportError:  # pragma: no cover
    BOTO3_AVAILABLE = False

# Genome sizes (in bases) for coverage calculation
GENOME_SIZES: dict[str, int] = {
    "Salmonella": 4_800_000,
    "Escherichia": 5_000_000,
    "Listeria": 3_000_000,
    "Campylobacter": 1_700_000,
    "Staphylococcus": 2_800_000,
    "Streptococcus": 2_000_000,
}

# S3 configuration
SRA_S3_BUCKET = "sra-pub-run-odp"
SRA_S3_PREFIX = "sra"


def construct_s3_path(accession: str) -> str:
    """Construct S3 path for an SRA accession.

    Args:
        accession: SRA run accession (e.g., SRR36650731)

    Returns:
        Full S3 URI (e.g., s3://sra-pub-run-odp/sra/SRR36650731/SRR36650731)
    """
    if not accession or not accession.startswith("SRR"):
        return ""

    # Extract the numeric prefix (e.g., SRR36650731 -> SRR366507)
    # S3 structure: s3://sra-pub-run-odp/sra/SRR######/SRR#######
    return f"s3://{SRA_S3_BUCKET}/{SRA_S3_PREFIX}/{accession}/{accession}"


def verify_s3_path(s3_path: str) -> bool:
    """Verify that an S3 path exists.

    Args:
        s3_path: Full S3 URI (e.g., s3://sra-pub-run-odp/sra/SRR36650731/SRR36650731)

    Returns:
        True if path exists and is accessible, False otherwise
    """
    if not BOTO3_AVAILABLE:
        print("Warning: boto3 not available, skipping S3 verification")
        return True  # Assume path exists if can't verify

    if not s3_path or not s3_path.startswith("s3://"):
        return False

    # Parse S3 URI
    parts = s3_path.replace("s3://", "").split("/", 1)
    if len(parts) != 2:
        return False

    bucket = parts[0]
    key = parts[1]

    try:
        s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
        # List objects with prefix to check if directory exists
        response = s3.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
        return "Contents" in response
    except (ClientError, NoCredentialsError):
        # If we can't access S3, log but don't fail
        return False
    except Exception:
        # Unknown error - assume exists to be conservative
        return True


def calculate_coverage(bases: int, organism_genus: str) -> int | None:
    """Calculate estimated coverage from total bases and genome size."""
    genome_size = GENOME_SIZES.get(organism_genus, None)
    if genome_size is None:
        return None
    return round(bases / genome_size)


def extract_summary_data(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract relevant fields from SRA summaries."""
    import re

    records = []

    for summary in summaries:
        # Handle different summary structures
        if isinstance(summary, dict):
            # Parse Runs XML field to extract accession and bases
            runs_xml = summary.get("Runs", "")
            accession = ""
            bases = 0

            if runs_xml:
                # Extract accession (e.g., SRR36637329)
                acc_match = re.search(r'acc="([^"]+)"', runs_xml)
                if acc_match:
                    accession = acc_match.group(1)

                # Extract total bases
                bases_match = re.search(r'total_bases="([^"]+)"', runs_xml)
                if bases_match:
                    try:
                        bases = int(bases_match.group(1))
                    except ValueError:
                        bases = 0

            # Extract title and bioproject from ExpXml
            title = ""
            bioproject = ""
            exp_xml = summary.get("ExpXml", "")
            if exp_xml:
                title_match = re.search(r"<Title>([^<]+)</Title>", exp_xml)
                if title_match:
                    title = title_match.group(1)

                # Extract BioProject ID
                bioproject_match = re.search(r"<Bioproject>([^<]+)</Bioproject>", exp_xml)
                if bioproject_match:
                    bioproject = bioproject_match.group(1)

            # Build record
            record = {
                "Accession": accession,
                "BioProject": bioproject,
                "Title": title,
                "CreateDate": summary.get("CreateDate", ""),
                "UpdateDate": summary.get("UpdateDate", ""),
                "Runs": runs_xml,
                "bases": bases,
            }

            records.append(record)

    return records


def parse_json_metadata(json_file: str | Path) -> pd.DataFrame:
    """Parse JSON metadata file from search_sra.py output.

    Validates JSON structure using Pydantic schema before processing.
    """
    # Load and validate JSON structure
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        validated_result = SRASearchResult.from_dict(data)
        organism = validated_result.organism
        summaries = [s.model_dump() for s in validated_result.summaries]
    except ValidationError as e:
        print(f"Error: Invalid JSON structure in {json_file}")
        print(f"Validation errors: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to parse JSON: {e}")
        sys.exit(1)

    # Extract genus from organism name
    genus = organism.split()[0] if organism else None

    records = extract_summary_data(summaries)
    df = pd.DataFrame(records)

    if not df.empty:
        df["Organism"] = organism
        df["Genus"] = genus

    return df


def parse_csv_metadata(csv_file: str | Path) -> pd.DataFrame:
    """Parse CSV metadata (RunInfo format from SRA)."""
    df = pd.read_csv(csv_file)

    # Extract genus from ScientificName or Organism field
    if "ScientificName" in df.columns:
        df["Genus"] = df["ScientificName"].str.split().str[0]
    elif "Organism" in df.columns:
        df["Genus"] = df["Organism"].str.split().str[0]

    return df


def filter_metadata(
    df: pd.DataFrame,
    min_coverage: float = 50,
    max_coverage: float = 250,
    preferred_instruments: list[str] | None = None,
    verify_s3: bool = True,
) -> pd.DataFrame:
    """Filter metadata based on quality criteria.

    Args:
        df: DataFrame with SRA metadata
        min_coverage: Minimum coverage threshold
        max_coverage: Maximum coverage threshold
        preferred_instruments: List of preferred instrument models
        verify_s3: Whether to verify S3 availability (default: True)

    Returns:
        Filtered DataFrame with s3_path column added
    """

    if df.empty:
        return df

    # Calculate coverage if bases column exists
    if "bases" in df.columns and "Genus" in df.columns:
        df["Estimated_Coverage"] = df.apply(
            lambda row: calculate_coverage(row["bases"], row["Genus"]), axis=1
        )

        # Filter by coverage
        df = df[
            (df["Estimated_Coverage"] >= min_coverage) & (df["Estimated_Coverage"] <= max_coverage)
        ]

    # Filter for paired-end layout if column exists
    if "LibraryLayout" in df.columns:
        df = df[df["LibraryLayout"] == "PAIRED"]

    # Filter for Illumina platform if column exists
    if "Platform" in df.columns:
        df = df[df["Platform"] == "ILLUMINA"]

    # Filter by instrument model if specified
    if preferred_instruments and "Model" in df.columns:
        df = df[df["Model"].isin(preferred_instruments)]

    # Add S3 paths
    if "Accession" in df.columns:
        print("Constructing S3 paths...")
        df = df.copy()  # Avoid SettingWithCopyWarning
        df["s3_path"] = df["Accession"].apply(construct_s3_path)

        # Verify S3 availability if requested
        if verify_s3:
            if not BOTO3_AVAILABLE:
                print("Warning: boto3 not installed. Install with: pip install boto3")
                print("Skipping S3 verification. Use --no-verify-s3 to suppress this warning.")
            else:
                print(f"Verifying S3 availability for {len(df)} records...")
                print("(This may take a few minutes. Use --no-verify-s3 to skip.)")

                # Check S3 availability with progress bar
                tqdm.pandas(desc="Verifying S3 paths")
                df["s3_available"] = df["s3_path"].progress_apply(verify_s3_path)

                initial_count = len(df)
                df = df[df["s3_available"]].copy()
                filtered_count = initial_count - len(df)

                if filtered_count > 0:
                    print(f"Filtered out {filtered_count} records without S3 availability")

                # Remove the temporary s3_available column if DataFrame is not empty
                if not df.empty and "s3_available" in df.columns:
                    df = df.drop(columns=["s3_available"])

    # Sort by coverage (if available) or date
    if "Estimated_Coverage" in df.columns:
        df = df.sort_values("Estimated_Coverage", ascending=False)
    elif "ReleaseDate" in df.columns:
        df = df.sort_values("ReleaseDate", ascending=False)

    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter SRA metadata based on coverage and quality criteria",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Input JSON or CSV file with SRA metadata")
    parser.add_argument("--output", required=True, help="Output CSV file for filtered results")
    parser.add_argument(
        "--min-coverage", type=float, default=50, help="Minimum coverage threshold (default: 50)"
    )
    parser.add_argument(
        "--max-coverage", type=float, default=250, help="Maximum coverage threshold (default: 250)"
    )
    parser.add_argument(
        "--instruments", nargs="+", help="Preferred instrument models (e.g., NextSeq NovaSeq MiSeq)"
    )
    parser.add_argument(
        "--verify-s3",
        dest="verify_s3",
        action="store_true",
        default=True,
        help="Verify S3 availability for each accession (default: enabled)",
    )
    parser.add_argument(
        "--no-verify-s3",
        dest="verify_s3",
        action="store_false",
        help="Skip S3 verification (faster but may include unavailable accessions)",
    )

    args = parser.parse_args()

    # Check input file exists
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Parse metadata based on file type
    print(f"Reading metadata from {args.input}...")
    if input_file.suffix == ".json":
        df = parse_json_metadata(args.input)
    elif input_file.suffix == ".csv":
        df = parse_csv_metadata(args.input)
    else:
        print(f"Error: Unsupported file type: {input_file.suffix}")
        print("Supported types: .json, .csv")
        sys.exit(1)

    if df.empty:
        print("Warning: No records found in input file")
        sys.exit(0)

    print(f"Found {len(df)} total records")

    # Filter metadata
    print(f"Filtering for coverage range: {args.min_coverage}x - {args.max_coverage}x")
    filtered_df = filter_metadata(
        df,
        min_coverage=args.min_coverage,
        max_coverage=args.max_coverage,
        preferred_instruments=args.instruments,
        verify_s3=args.verify_s3,
    )

    print(f"After filtering: {len(filtered_df)} records")

    if filtered_df.empty:
        print("Warning: No records passed filtering criteria")
        sys.exit(0)

    # Create output directory if needed
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Export filtered results
    filtered_df.to_csv(args.output, index=False)
    print(f"\nSuccess! Saved {len(filtered_df)} filtered records to {args.output}")

    # Print summary statistics if coverage available
    if "Estimated_Coverage" in filtered_df.columns:
        print("\nCoverage Statistics:")
        print(f"  Mean: {int(round(filtered_df['Estimated_Coverage'].mean()))}x")
        print(f"  Median: {int(round(filtered_df['Estimated_Coverage'].median()))}x")
        print(f"  Min: {int(filtered_df['Estimated_Coverage'].min())}x")
        print(f"  Max: {int(filtered_df['Estimated_Coverage'].max())}x")


if __name__ == "__main__":
    main()
