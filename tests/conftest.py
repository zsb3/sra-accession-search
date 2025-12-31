"""Shared pytest fixtures for SRA Accession Search tests.

This module provides reusable test fixtures that represent common test data
structures used across multiple test modules. Fixtures are session-scoped where
possible to improve test performance.

Fixture Categories:
- Mock SRA summaries: Simulated NCBI API responses
- Mock metadata: Sample data for filtering tests
- File paths: Temporary file locations
"""

import json

import pandas as pd
import pytest


@pytest.fixture(scope="session")
def mock_sra_summary_listeria():
    """Mock SRA summary for a Listeria sample with good coverage.

    Represents a typical NCBI SRA summary response for a paired-end
    Illumina WGS run of Listeria monocytogenes.

    Returns:
        dict: SRA summary with Runs XML, ExpXml, and dates

    Example usage:
        def test_parse_summary(mock_sra_summary_listeria):
            data = extract_summary_data([mock_sra_summary_listeria])
            assert data[0]["accession"] == "SRR12345"
    """
    return {
        "Runs": '<Run acc="SRR12345" total_bases="300000000"/>',
        "ExpXml": ("<Summary><Title>WGS of Listeria monocytogenes</Title></Summary>"),
        "CreateDate": "2024/01/15",
        "UpdateDate": "2024/01/15",
    }


@pytest.fixture(scope="session")
def mock_sra_summary_salmonella():
    """Mock SRA summary for a Salmonella sample with high coverage.

    Returns:
        dict: SRA summary representing 150x coverage Salmonella run

    Coverage calculation:
        720,000,000 bases / 4.8 Mb = 150x
    """
    return {
        "Runs": '<Run acc="SRR67890" total_bases="720000000"/>',
        "ExpXml": "<Summary><Title>Salmonella enterica WGS</Title></Summary>",
        "CreateDate": "2024/02/20",
        "UpdateDate": "2024/02/20",
    }


@pytest.fixture(scope="session")
def mock_sra_summaries_batch():
    """Mock batch of SRA summaries with varying coverage levels.

    Useful for testing filtering logic across multiple samples with
    different organisms and coverage ranges.

    Returns:
        list[dict]: Three SRA summaries (Listeria, Salmonella, Campylobacter)
            - Listeria: 100x coverage
            - Salmonella: 150x coverage
            - Campylobacter: 50x coverage

    Example usage:
        def test_filter_by_coverage(mock_sra_summaries_batch):
            df = parse_json_metadata(mock_sra_summaries_batch)
            filtered = filter_metadata(df, min_coverage=75, max_coverage=200)
            assert len(filtered) == 2  # Salmonella and Listeria only
    """
    return [
        {
            "Runs": '<Run acc="SRR12345" total_bases="300000000"/>',
            "ExpXml": ("<Summary><Title>Listeria monocytogenes WGS</Title></Summary>"),
            "CreateDate": "2024/01/15",
            "UpdateDate": "2024/01/15",
        },
        {
            "Runs": '<Run acc="SRR67890" total_bases="720000000"/>',
            "ExpXml": "<Summary><Title>Salmonella enterica WGS</Title></Summary>",
            "CreateDate": "2024/02/20",
            "UpdateDate": "2024/02/20",
        },
        {
            "Runs": '<Run acc="SRR11111" total_bases="85000000"/>',
            "ExpXml": "<Summary><Title>Campylobacter jejuni WGS</Title></Summary>",
            "CreateDate": "2024/03/10",
            "UpdateDate": "2024/03/10",
        },
    ]


@pytest.fixture
def mock_filtered_dataframe():
    """Mock DataFrame with calculated coverage and metadata columns.

    Represents the output of parse_json_metadata() before filtering.
    Includes all standard columns: Accession, bases, Genus, Title, dates.

    Returns:
        pd.DataFrame: Sample data with 3 rows (Listeria, Salmonella, Campylobacter)

    Note:
        Function-scoped because tests may modify the DataFrame.

    Example usage:
        def test_coverage_filter(mock_filtered_dataframe):
            df = mock_filtered_dataframe
            high_cov = df[df["Estimated_Coverage"] >= 100]
            assert len(high_cov) == 2
    """
    return pd.DataFrame(
        {
            "Accession": ["SRR12345", "SRR67890", "SRR11111"],
            "bases": [300_000_000, 720_000_000, 85_000_000],
            "Genus": ["Listeria", "Salmonella", "Campylobacter"],
            "Estimated_Coverage": [100, 150, 50],
            "Title": [
                "Listeria monocytogenes WGS",
                "Salmonella enterica WGS",
                "Campylobacter jejuni WGS",
            ],
            "CreateDate": ["2024/01/15", "2024/02/20", "2024/03/10"],
            "UpdateDate": ["2024/01/15", "2024/02/20", "2024/03/10"],
        }
    )


@pytest.fixture
def mock_metadata_with_platform():
    """Mock DataFrame including Platform and LibraryLayout columns.

    Used for testing filter logic that checks sequencing platform
    and library type (PAIRED vs SINGLE).

    Returns:
        pd.DataFrame: Sample data with Platform and LibraryLayout columns

    Contains:
        - Mix of ILLUMINA and PACBIO platforms
        - Mix of PAIRED and SINGLE layouts
        - Varying coverage levels

    Example usage:
        def test_platform_filter(mock_metadata_with_platform):
            df = mock_metadata_with_platform
            illumina = df[df["Platform"] == "ILLUMINA"]
            assert len(illumina) == 2
    """
    return pd.DataFrame(
        {
            "Accession": ["SRR12345", "SRR67890", "SRR11111"],
            "bases": [300_000_000, 720_000_000, 85_000_000],
            "Genus": ["Listeria", "Salmonella", "Campylobacter"],
            "Estimated_Coverage": [100, 150, 50],
            "Title": ["Sample 1", "Sample 2", "Sample 3"],
            "Platform": ["ILLUMINA", "ILLUMINA", "PACBIO"],
            "LibraryLayout": ["PAIRED", "PAIRED", "SINGLE"],
            "CreateDate": ["2024/01/15", "2024/02/20", "2024/03/10"],
        }
    )


@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file with mock SRA search output.

    This fixture creates a real temporary file with JSON data, useful for
    testing file I/O operations without mocking.

    Args:
        tmp_path: pytest built-in fixture providing temporary directory

    Returns:
        Path: Path to temporary JSON file

    File structure matches search_sra.py output:
        {
            "organism": "...",
            "query": "...",
            "total_count": int,
            "retrieved_count": int,
            "summaries": [...]
        }

    Example usage:
        def test_read_json(temp_json_file):
            with open(temp_json_file) as f:
                data = json.load(f)
            assert data["organism"] == "Listeria monocytogenes"

    Note:
        File is automatically cleaned up after test completes (tmp_path fixture).
    """
    data = {
        "organism": "Listeria monocytogenes",
        "query": '"Listeria monocytogenes"[Organism] AND "wgs"[Strategy]',
        "total_count": 100,
        "retrieved_count": 3,
        "summaries": [
            {
                "Runs": '<Run acc="SRR12345" total_bases="300000000"/>',
                "ExpXml": ("<Summary><Title>Listeria WGS</Title></Summary>"),
                "CreateDate": "2024/01/15",
                "UpdateDate": "2024/01/15",
            },
        ],
    }

    json_file = tmp_path / "test_sra_output.json"
    json_file.write_text(json.dumps(data, indent=2))
    return json_file


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file with mock metadata.

    Returns:
        Path: Path to temporary CSV file with columns matching NCBI RunInfo API

    Columns:
        - Accession
        - ScientificName (full species name, used to extract genus)
        - bases
        - LibraryLayout
        - Platform
        - ReleaseDate

    Example usage:
        def test_read_csv(temp_csv_file):
            df = pd.read_csv(temp_csv_file)
            assert len(df) == 2
            assert "ScientificName" in df.columns
    """
    df = pd.DataFrame(
        {
            "Accession": ["SRR12345", "SRR67890"],
            "ScientificName": ["Listeria monocytogenes", "Salmonella enterica"],
            "bases": [300_000_000, 720_000_000],
            "LibraryLayout": ["PAIRED", "PAIRED"],
            "Platform": ["ILLUMINA", "ILLUMINA"],
            "ReleaseDate": ["2024-01-15", "2024-02-20"],
        }
    )

    csv_file = tmp_path / "test_metadata.csv"
    df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture(scope="session")
def sample_ncbi_esearch_response():
    """Mock XML response from NCBI Entrez.esearch().

    Returns:
        bytes: XML response as bytes (Bio.Entrez returns BytesIO)

    Response includes:
        - Count: Total number of results
        - RetMax: Maximum results returned
        - QueryKey: Session key for fetching summaries
        - WebEnv: Web environment token

    Example usage:
        @patch("scripts.search_sra.Entrez.esearch")
        def test_search(mock_esearch, sample_ncbi_esearch_response):
            mock_esearch.return_value = io.BytesIO(sample_ncbi_esearch_response)
            result = search_sra("test query", retmax=100)
            assert "WebEnv" in result
    """
    return b"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE eSearchResult PUBLIC "-//NLM//DTD esearch 20060628//EN"
 "https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20060628/esearch.dtd">
<eSearchResult>
    <Count>150</Count>
    <RetMax>100</RetMax>
    <RetStart>0</RetStart>
    <QueryKey>1</QueryKey>
    <WebEnv>MCID_test123</WebEnv>
    <IdList>
        <Id>12345</Id>
        <Id>67890</Id>
    </IdList>
</eSearchResult>
"""


@pytest.fixture(scope="session")
def sample_ncbi_esummary_response():
    """Mock XML response from NCBI Entrez.esummary().

    Returns:
        bytes: XML response with SRA run summaries

    Response includes multiple <DocSum> elements with:
        - Runs: Run accession and total_bases
        - ExpXml: Experiment title and metadata
        - CreateDate/UpdateDate: Timestamps

    Example usage:
        @patch("scripts.search_sra.Entrez.esummary")
        def test_fetch(mock_esummary, sample_ncbi_esummary_response):
            mock_esummary.return_value = io.BytesIO(sample_ncbi_esummary_response)
            summaries = fetch_summaries("test_webenv", "1", retmax=100)
            assert len(summaries) > 0
    """
    return b"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE eSummaryResult PUBLIC "-//NLM//DTD esummary 20060628//EN"
 "https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20060628/esummary.dtd">
<eSummaryResult>
    <DocSum>
        <Id>12345</Id>
        <Item Name="Runs" Type="String">
            &lt;Run acc="SRR12345" total_bases="300000000"/&gt;
        </Item>
        <Item Name="ExpXml" Type="String">
            &lt;Summary&gt;&lt;Title&gt;Listeria WGS&lt;/Title&gt;&lt;/Summary&gt;
        </Item>
        <Item Name="CreateDate" Type="String">2024/01/15</Item>
        <Item Name="UpdateDate" Type="String">2024/01/15</Item>
    </DocSum>
</eSummaryResult>
"""


# Scope explanation:
# - session: Fixtures that return immutable data (dicts, strings, bytes)
#            Reused across all tests for performance
# - function: Fixtures that return mutable data (DataFrames, file paths)
#             Created fresh for each test to avoid cross-contamination
