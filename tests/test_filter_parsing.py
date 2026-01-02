"""Unit tests for metadata parsing functionality in filter_metadata.py"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

import pandas as pd

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from filter_metadata import (  # noqa: E402
    extract_summary_data,
    parse_json_metadata,
    parse_csv_metadata,
)


# =============================================================================
# SUMMARY DATA EXTRACTION TESTS
# =============================================================================


class TestExtractSummaryData:
    """Test summary data extraction"""

    def test_extract_basic_fields(self):
        """Test extraction of basic fields from summary"""
        summaries = [
            {
                "Runs": '<Run acc="SRR12345" total_bases="100000000"/>',
                "ExpXml": (
                    "<Summary><Title>Test Sample</Title></Summary>"
                    "<Bioproject>PRJNA123456</Bioproject>"
                ),
                "CreateDate": "2025/12/31",
                "UpdateDate": "2025/12/31",
            }
        ]

        records = extract_summary_data(summaries)

        assert len(records) == 1
        assert records[0]["Accession"] == "SRR12345"
        assert records[0]["BioProject"] == "PRJNA123456"
        assert records[0]["Title"] == "Test Sample"
        assert records[0]["bases"] == 100000000
        assert records[0]["CreateDate"] == "2025/12/31"

    def test_extract_accession_from_runs(self):
        """Test accession extraction from Runs XML"""
        summaries = [
            {
                "Runs": '<Run acc="SRR36637329" total_spots="647085" total_bases="313617513"/>',
                "ExpXml": "",
                "CreateDate": "",
                "UpdateDate": "",
            }
        ]

        records = extract_summary_data(summaries)
        assert records[0]["Accession"] == "SRR36637329"

    def test_extract_bases_from_runs(self):
        """Test total_bases extraction from Runs XML"""
        summaries = [
            {
                "Runs": '<Run acc="SRR123" total_bases="500000000"/>',
                "ExpXml": "",
                "CreateDate": "",
                "UpdateDate": "",
            }
        ]

        records = extract_summary_data(summaries)
        assert records[0]["bases"] == 500000000

    def test_extract_title_from_expxml(self):
        """Test title extraction from ExpXml"""
        summaries = [
            {
                "Runs": "",
                "ExpXml": "<Summary><Title>Illumina WGS of Salmonella enterica</Title></Summary>",
                "CreateDate": "",
                "UpdateDate": "",
            }
        ]

        records = extract_summary_data(summaries)
        assert records[0]["Title"] == "Illumina WGS of Salmonella enterica"

    def test_extract_multiple_summaries(self):
        """Test extracting multiple summaries"""
        summaries = [
            {
                "Runs": '<Run acc="SRR001" total_bases="100000000"/>',
                "ExpXml": "<Summary><Title>Sample 1</Title></Summary>",
                "CreateDate": "2025/01/01",
                "UpdateDate": "2025/01/01",
            },
            {
                "Runs": '<Run acc="SRR002" total_bases="200000000"/>',
                "ExpXml": "<Summary><Title>Sample 2</Title></Summary>",
                "CreateDate": "2025/01/02",
                "UpdateDate": "2025/01/02",
            },
        ]

        records = extract_summary_data(summaries)
        assert len(records) == 2
        assert records[0]["Accession"] == "SRR001"
        assert records[1]["Accession"] == "SRR002"

    def test_extract_missing_fields(self):
        """Test extraction handles missing fields gracefully"""
        summaries = [{"Runs": "", "ExpXml": "", "CreateDate": "", "UpdateDate": ""}]

        records = extract_summary_data(summaries)
        assert records[0]["Accession"] == ""
        assert records[0]["BioProject"] == ""
        assert records[0]["bases"] == 0
        assert records[0]["Title"] == ""

    def test_extract_invalid_bases(self):
        """Test extraction handles invalid bases value"""
        summaries = [
            {
                "Runs": '<Run acc="SRR123" total_bases="invalid"/>',
                "ExpXml": "",
                "CreateDate": "",
                "UpdateDate": "",
            }
        ]

        records = extract_summary_data(summaries)
        assert records[0]["bases"] == 0


# =============================================================================
# JSON METADATA PARSING TESTS
# =============================================================================


class TestParseJsonMetadata:
    """Test JSON metadata parsing"""

    def test_parse_json_with_fixture(self):
        """Test parsing JSON file with fixture data"""
        fixture_path = Path(__file__).parent / "fixtures" / "mock_search_output.json"

        df = parse_json_metadata(str(fixture_path))

        assert len(df) == 2
        assert "Organism" in df.columns
        assert "Genus" in df.columns
        assert df["Organism"].iloc[0] == "Listeria monocytogenes"
        assert df["Genus"].iloc[0] == "Listeria"

    def test_parse_json_genus_extraction(self):
        """Test genus is correctly extracted from organism name"""
        # Create temporary mock data
        mock_data = {
            "organism": "Campylobacter jejuni",
            "query": "test",
            "total_count": 1,
            "retrieved_count": 1,
            "summaries": [
                {
                    "Runs": '<Run acc="SRR123" total_bases="100000000"/>',
                    "ExpXml": "<Summary><Title>Test</Title></Summary>",
                    "CreateDate": "2025/12/31",
                    "UpdateDate": "2025/12/31",
                }
            ],
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            df = parse_json_metadata("dummy.json")
            assert df["Genus"].iloc[0] == "Campylobacter"


# =============================================================================
# CSV METADATA PARSING TESTS
# =============================================================================


class TestParseCSVMetadata:
    """Test CSV metadata parsing"""

    def test_parse_csv_with_scientificname(self):
        """Test parsing CSV with ScientificName column"""
        csv_data = """Run,ScientificName,Bases
SRR001,Listeria monocytogenes,300000000
SRR002,Salmonella enterica,480000000"""

        with patch("builtins.open", mock_open(read_data=csv_data)):
            with patch("pandas.read_csv") as mock_read_csv:
                mock_df = pd.DataFrame(
                    {
                        "Run": ["SRR001", "SRR002"],
                        "ScientificName": ["Listeria monocytogenes", "Salmonella enterica"],
                        "Bases": [300000000, 480000000],
                    }
                )
                mock_read_csv.return_value = mock_df

                df = parse_csv_metadata("test.csv")

                assert "Genus" in df.columns
                assert df["Genus"].iloc[0] == "Listeria"
                assert df["Genus"].iloc[1] == "Salmonella"

    def test_parse_csv_with_organism(self):
        """Test parsing CSV with Organism column"""
        csv_data = """Run,Organism,Bases
SRR001,Escherichia coli,250000000"""

        with patch("builtins.open", mock_open(read_data=csv_data)):
            with patch("pandas.read_csv") as mock_read_csv:
                mock_df = pd.DataFrame(
                    {"Run": ["SRR001"], "Organism": ["Escherichia coli"], "Bases": [250000000]}
                )
                mock_read_csv.return_value = mock_df

                df = parse_csv_metadata("test.csv")

                assert "Genus" in df.columns
                assert df["Genus"].iloc[0] == "Escherichia"
