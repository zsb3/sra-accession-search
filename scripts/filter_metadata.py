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

# Genome sizes (in bases) for coverage calculation
GENOME_SIZES = {
    'Salmonella': 4_800_000,
    'Escherichia': 5_000_000,
    'Listeria': 3_000_000,
    'Campylobacter': 1_700_000,
    'Staphylococcus': 2_800_000,
    'Streptococcus': 2_000_000
}

def calculate_coverage(bases, organism_genus):
    """Calculate estimated coverage from total bases and genome size."""
    genome_size = GENOME_SIZES.get(organism_genus, None)
    if genome_size is None:
        return None
    return round(bases / genome_size)

def extract_summary_data(summaries):
    """Extract relevant fields from SRA summaries."""
    import re
    records = []
    
    for summary in summaries:
        # Handle different summary structures
        if isinstance(summary, dict):
            # Parse Runs XML field to extract accession and bases
            runs_xml = summary.get('Runs', '')
            accession = ''
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
            
            # Extract title from ExpXml
            title = ''
            exp_xml = summary.get('ExpXml', '')
            if exp_xml:
                title_match = re.search(r'<Title>([^<]+)</Title>', exp_xml)
                if title_match:
                    title = title_match.group(1)
            
            # Build record
            record = {
                'Accession': accession,
                'Title': title,
                'CreateDate': summary.get('CreateDate', ''),
                'UpdateDate': summary.get('UpdateDate', ''),
                'Runs': runs_xml,
                'bases': bases
            }
            
            records.append(record)
    
    return records

def parse_json_metadata(json_file):
    """Parse JSON metadata file from search_sra.py output."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    organism = data.get('organism', '')
    summaries = data.get('summaries', [])
    
    # Extract genus from organism name
    genus = organism.split()[0] if organism else None
    
    records = extract_summary_data(summaries)
    df = pd.DataFrame(records)
    
    if not df.empty:
        df['Organism'] = organism
        df['Genus'] = genus
    
    return df

def parse_csv_metadata(csv_file):
    """Parse CSV metadata (RunInfo format from SRA)."""
    df = pd.read_csv(csv_file)
    
    # Extract genus from ScientificName or Organism field
    if 'ScientificName' in df.columns:
        df['Genus'] = df['ScientificName'].str.split().str[0]
    elif 'Organism' in df.columns:
        df['Genus'] = df['Organism'].str.split().str[0]
    
    return df

def filter_metadata(df, min_coverage=50, max_coverage=250, 
                   preferred_instruments=None):
    """Filter metadata based on quality criteria."""
    
    if df.empty:
        return df
    
    # Calculate coverage if bases column exists
    if 'bases' in df.columns and 'Genus' in df.columns:
        df['Estimated_Coverage'] = df.apply(
            lambda row: calculate_coverage(row['bases'], row['Genus']), 
            axis=1
        )
        
        # Filter by coverage
        df = df[
            (df['Estimated_Coverage'] >= min_coverage) & 
            (df['Estimated_Coverage'] <= max_coverage)
        ]
    
    # Filter for paired-end layout if column exists
    if 'LibraryLayout' in df.columns:
        df = df[df['LibraryLayout'] == 'PAIRED']
    
    # Filter for Illumina platform if column exists
    if 'Platform' in df.columns:
        df = df[df['Platform'] == 'ILLUMINA']
    
    # Filter by instrument model if specified
    if preferred_instruments and 'Model' in df.columns:
        df = df[df['Model'].isin(preferred_instruments)]
    
    # Sort by coverage (if available) or date
    if 'Estimated_Coverage' in df.columns:
        df = df.sort_values('Estimated_Coverage', ascending=False)
    elif 'ReleaseDate' in df.columns:
        df = df.sort_values('ReleaseDate', ascending=False)
    
    return df

def main():
    parser = argparse.ArgumentParser(
        description='Filter SRA metadata based on coverage and quality criteria',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input JSON or CSV file with SRA metadata'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output CSV file for filtered results'
    )
    parser.add_argument(
        '--min-coverage',
        type=float,
        default=50,
        help='Minimum coverage threshold (default: 50)'
    )
    parser.add_argument(
        '--max-coverage',
        type=float,
        default=250,
        help='Maximum coverage threshold (default: 250)'
    )
    parser.add_argument(
        '--instruments',
        nargs='+',
        help='Preferred instrument models (e.g., NextSeq NovaSeq MiSeq)'
    )
    
    args = parser.parse_args()
    
    # Check input file exists
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Parse metadata based on file type
    print(f"Reading metadata from {args.input}...")
    if input_file.suffix == '.json':
        df = parse_json_metadata(args.input)
    elif input_file.suffix == '.csv':
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
        preferred_instruments=args.instruments
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
    if 'Estimated_Coverage' in filtered_df.columns:
        print("\nCoverage Statistics:")
        print(f"  Mean: {int(round(filtered_df['Estimated_Coverage'].mean()))}x")
        print(f"  Median: {int(round(filtered_df['Estimated_Coverage'].median()))}x")
        print(f"  Min: {int(filtered_df['Estimated_Coverage'].min())}x")
        print(f"  Max: {int(filtered_df['Estimated_Coverage'].max())}x")

if __name__ == "__main__":
    main()
