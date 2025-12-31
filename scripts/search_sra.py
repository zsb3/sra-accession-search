#!/usr/bin/env python3
"""Search NCBI SRA for bacterial paired-end Illumina WGS data.

Usage:
    python search_sra.py \
        --email your.email@example.com \
        --api-key YOUR_NCBI_API_KEY \
        --organism "Salmonella enterica" \
        --output salmonella_metadata.json
"""

from Bio import Entrez
import argparse
import json
import os
import sys
import time


def search_sra(query, retmax=5000):
    """Search SRA database and return list of UIDs"""
    handle = Entrez.esearch(db="sra", term=query, retmax=retmax, usehistory="y")
    results = Entrez.read(handle)
    handle.close()
    return results


def fetch_summaries(webenv, query_key, retstart=0, retmax=500):
    """Fetch summaries for search results"""
    handle = Entrez.esummary(
        db="sra", query_key=query_key, WebEnv=webenv, retstart=retstart, retmax=retmax
    )
    results = Entrez.read(handle)
    handle.close()
    return results


def get_runinfo(accessions):
    """Get RunInfo CSV for accessions"""
    import requests

    acc_list = ",".join(accessions) if isinstance(accessions, list) else accessions
    base_url = "https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi"
    url = f"{base_url}?save=efetch&db=sra&rettype=runinfo&term={acc_list}"

    response = requests.get(url)
    return response.text


def build_query(organism, date_range="2020:2025"):
    """Build SRA search query for paired-end Illumina WGS data"""
    parts = [
        f'"{organism}"[Organism]',
        '"illumina"[Platform]',
        '"paired"[Layout]',
        '"wgs"[Strategy]',
        f"{date_range}[Publication Date]",
    ]
    query = " AND ".join(parts)
    return query


def main():
    parser = argparse.ArgumentParser(
        description="Search NCBI SRA for bacterial paired-end Illumina WGS data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("NCBI_EMAIL"),
        help="Your email address (default: from NCBI_EMAIL env var)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("NCBI_API_KEY"),
        help="NCBI API key (default: from NCBI_API_KEY env var)",
    )
    parser.add_argument(
        "--organism",
        required=True,
        help='Organism name (e.g., "Salmonella enterica", "Escherichia coli")',
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file for results (e.g., salmonella_metadata.json)",
    )
    parser.add_argument(
        "--date-range", default="2020:2025", help="Publication date range (default: 2020:2025)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5000,
        help="Maximum number of results to retrieve (default: 5000)",
    )

    args = parser.parse_args()

    # Validate email is available
    if not args.email:
        print("Error: Email is required. Set NCBI_EMAIL env var or use --email")
        sys.exit(1)

    # Configure Entrez with email
    Entrez.email = args.email

    # Configure API key if available
    if args.api_key:
        Entrez.api_key = args.api_key
    else:
        print("Warning: No API key provided. Rate limited to 3 requests/second.")
        print("Get a free API key at: https://www.ncbi.nlm.nih.gov/account/settings/")
        print("Set NCBI_API_KEY env var or use --api-key to increase to 10 req/sec\n")

    # Build and execute query
    query = build_query(args.organism, args.date_range)

    print(f"Organism: {args.organism}")
    print(f"Query: {query}")
    print("Searching SRA...")

    search_results = search_sra(query, retmax=args.max_results)

    count = int(search_results["Count"])
    webenv = search_results["WebEnv"]
    query_key = search_results["QueryKey"]

    print(f"Found {count} records")

    if count == 0:
        print("No results found. Try adjusting your search criteria.")
        sys.exit(0)

    # Fetch summaries in batches
    all_summaries = []
    batch_size = 500
    total_to_fetch = min(count, args.max_results)

    # Rate limiting: 10 req/sec with API key, 3 req/sec without
    sleep_time = 0.11 if args.api_key else 0.34

    for start in range(0, total_to_fetch, batch_size):
        end = min(start + batch_size, total_to_fetch)
        records_to_fetch = end - start  # Fetch only the number we need
        print(f"Fetching records {start+1} to {end}...")
        summaries = fetch_summaries(webenv, query_key, retstart=start, retmax=records_to_fetch)
        all_summaries.extend(summaries)
        time.sleep(sleep_time)  # Rate limiting: 10 req/sec with API key

    # Save results
    output_data = {
        "organism": args.organism,
        "query": query,
        "total_count": count,
        "retrieved_count": len(all_summaries),
        "summaries": all_summaries,
    }

    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSuccess! Saved {len(all_summaries)} summaries to {args.output}")
    print(f"Total matching records: {count}")


if __name__ == "__main__":
    main()
