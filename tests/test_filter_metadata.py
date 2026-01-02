"""Unit tests for filter_metadata.py"""

import json
import os
import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pandas as pd
import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from filter_metadata import (  # noqa: E402
    calculate_coverage,
    extract_summary_data,
    parse_json_metadata,
    filter_metadata,
    construct_s3_path,
    verify_s3_path,
)


class TestCalculateCoverage:
    """Test coverage calculation"""

    def test_listeria_coverage(self):
        """Test coverage calculation for Listeria"""
        # Listeria genome: 3 Mb = 3,000,000 bases
        # 300,000,000 bases / 3,000,000 = 100x coverage
        coverage = calculate_coverage(300_000_000, "Listeria")
        assert coverage == 100

    def test_campylobacter_coverage(self):
        """Test coverage calculation for Campylobacter"""
        # Campylobacter genome: 1.7 Mb
        # 170,000,000 bases / 1,700,000 = 100x
        coverage = calculate_coverage(170_000_000, "Campylobacter")
        assert coverage == 100

    def test_salmonella_coverage(self):
        """Test coverage calculation for Salmonella"""
        # Salmonella genome: 4.8 Mb
        # 480,000,000 bases / 4,800,000 = 100x
        coverage = calculate_coverage(480_000_000, "Salmonella")
        assert coverage == 100

    def test_escherichia_coverage(self):
        """Test coverage calculation for E. coli"""
        # E. coli genome: 5 Mb
        coverage = calculate_coverage(250_000_000, "Escherichia")
        assert coverage == 50

    def test_staphylococcus_coverage(self):
        """Test coverage calculation for Staphylococcus"""
        # Staphylococcus genome: 2.8 Mb
        coverage = calculate_coverage(280_000_000, "Staphylococcus")
        assert coverage == 100

    def test_streptococcus_coverage(self):
        """Test coverage calculation for Streptococcus"""
        # Streptococcus genome: 2 Mb
        coverage = calculate_coverage(200_000_000, "Streptococcus")
        assert coverage == 100

    def test_unknown_organism(self):
        """Test coverage returns None for unknown organism"""
        coverage = calculate_coverage(100_000_000, "Unknown")
        assert coverage is None

    def test_coverage_rounding(self):
        """Test that coverage is rounded to nearest integer"""
        # 313,617,513 / 3,000,000 = 104.539... should round to 105
        coverage = calculate_coverage(313_617_513, "Listeria")
        assert coverage == 105
        assert isinstance(coverage, int)

    def test_low_coverage(self):
        """Test low coverage calculation"""
        # 30 Mb / 3 Mb = 10x
        coverage = calculate_coverage(30_000_000, "Listeria")
        assert coverage == 10

    def test_high_coverage(self):
        """Test high coverage calculation"""
        # 1.5 Gb / 3 Mb = 500x
        coverage = calculate_coverage(1_500_000_000, "Listeria")
        assert coverage == 500


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


class TestParseCSVMetadata:
    """Test CSV metadata parsing"""

    def test_parse_csv_with_scientificname(self):
        """Test parsing CSV with ScientificName column"""
        from filter_metadata import parse_csv_metadata

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
        from filter_metadata import parse_csv_metadata

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


class TestFilterMetadata:
    """Test metadata filtering"""

    def test_filter_by_coverage_range(self):
        """Test filtering by coverage range"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002", "SRR003", "SRR004"],
                "bases": [150_000_000, 300_000_000, 450_000_000, 750_000_000],
                "Genus": ["Listeria", "Listeria", "Listeria", "Listeria"],
            }
        )

        filtered = filter_metadata(df, min_coverage=50, max_coverage=250, verify_s3=False)

        # Should keep 50x (150M/3M), 100x (300M/3M), 150x (450M/3M), and 250x (750M/3M)
        # All are within 50-250 range
        assert len(filtered) == 4
        assert "Estimated_Coverage" in filtered.columns

    def test_filter_removes_low_coverage(self):
        """Test low coverage samples are filtered out"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002"],
                "bases": [60_000_000, 300_000_000],  # 20x and 100x for Listeria
                "Genus": ["Listeria", "Listeria"],
            }
        )

        filtered = filter_metadata(df, min_coverage=50, max_coverage=250, verify_s3=False)

        assert len(filtered) == 1
        assert filtered.iloc[0]["Accession"] == "SRR002"

    def test_filter_removes_high_coverage(self):
        """Test high coverage samples are filtered out"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002"],
                "bases": [300_000_000, 900_000_000],  # 100x and 300x for Listeria
                "Genus": ["Listeria", "Listeria"],
            }
        )

        filtered = filter_metadata(df, min_coverage=50, max_coverage=250, verify_s3=False)

        assert len(filtered) == 1
        assert filtered.iloc[0]["Accession"] == "SRR001"

    def test_filter_empty_dataframe(self):
        """Test filtering empty dataframe"""
        df = pd.DataFrame()

        filtered = filter_metadata(df, min_coverage=50, max_coverage=250, verify_s3=False)

        assert filtered.empty

    def test_filter_different_organisms(self):
        """Test filtering with different organisms (different genome sizes)"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002"],
                "bases": [170_000_000, 250_000_000],  # Both 100x for their respective organisms
                "Genus": ["Campylobacter", "Escherichia"],
            }
        )

        filtered = filter_metadata(df, min_coverage=50, max_coverage=150, verify_s3=False)

        # Both should pass (100x coverage each)
        assert len(filtered) == 2

    def test_filter_by_library_layout(self):
        """Test filtering by LibraryLayout column"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002", "SRR003"],
                "bases": [300_000_000, 300_000_000, 300_000_000],
                "Genus": ["Listeria", "Listeria", "Listeria"],
                "LibraryLayout": ["PAIRED", "SINGLE", "PAIRED"],
            }
        )

        filtered = filter_metadata(df, verify_s3=False)

        # Should only keep PAIRED layouts
        assert len(filtered) == 2
        assert all(filtered["LibraryLayout"] == "PAIRED")

    def test_filter_by_platform(self):
        """Test filtering by Platform column"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002", "SRR003"],
                "bases": [300_000_000, 300_000_000, 300_000_000],
                "Genus": ["Listeria", "Listeria", "Listeria"],
                "Platform": ["ILLUMINA", "PACBIO_SMRT", "ILLUMINA"],
            }
        )

        filtered = filter_metadata(df, verify_s3=False)

        # Should only keep ILLUMINA platform
        assert len(filtered) == 2
        assert all(filtered["Platform"] == "ILLUMINA")

    def test_filter_by_preferred_instruments(self):
        """Test filtering by preferred instrument models"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002", "SRR003"],
                "bases": [300_000_000, 300_000_000, 300_000_000],
                "Genus": ["Listeria", "Listeria", "Listeria"],
                "Model": ["Illumina MiSeq", "Illumina HiSeq 2500", "Illumina NovaSeq 6000"],
            }
        )

        filtered = filter_metadata(
            df, preferred_instruments=["Illumina MiSeq", "Illumina NovaSeq 6000"], verify_s3=False
        )

        # Should only keep MiSeq and NovaSeq
        assert len(filtered) == 2
        assert "SRR002" not in filtered["Accession"].values

    def test_sort_by_estimated_coverage(self):
        """Test sorting by Estimated_Coverage when available"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002", "SRR003"],
                "bases": [150_000_000, 450_000_000, 300_000_000],
                "Genus": ["Listeria", "Listeria", "Listeria"],
            }
        )

        filtered = filter_metadata(df, verify_s3=False)

        # Should be sorted by coverage (highest first)
        assert filtered.iloc[0]["Accession"] == "SRR002"  # 150x
        assert filtered.iloc[1]["Accession"] == "SRR003"  # 100x
        assert filtered.iloc[2]["Accession"] == "SRR001"  # 50x

    def test_sort_by_release_date_when_no_coverage(self):
        """Test sorting by ReleaseDate when Estimated_Coverage not in dataframe"""
        df = pd.DataFrame(
            {
                "Accession": ["SRR001", "SRR002", "SRR003"],
                "ReleaseDate": ["2023-01-15", "2023-12-01", "2023-06-30"],
            }
        )

        filtered = filter_metadata(df, verify_s3=False)

        # Should be sorted by date (most recent first)
        assert filtered.iloc[0]["Accession"] == "SRR002"  # 2023-12-01
        assert filtered.iloc[1]["Accession"] == "SRR003"  # 2023-06-30
        assert filtered.iloc[2]["Accession"] == "SRR001"  # 2023-01-15

    def test_coverage_calculated_correctly(self):
        """Test that coverage is calculated and added to dataframe"""
        df = pd.DataFrame({"Accession": ["SRR001"], "bases": [300_000_000], "Genus": ["Listeria"]})

        filtered = filter_metadata(df, min_coverage=50, max_coverage=250, verify_s3=False)

        assert "Estimated_Coverage" in filtered.columns
        assert filtered["Estimated_Coverage"].iloc[0] == 100


class TestMainFunction:
    """Test the main CLI function"""

    @patch("filter_metadata.pd.DataFrame.to_csv")
    def test_main_with_json_input(self, mock_to_csv):
        """Test main function with JSON input"""
        fixture_path = Path(__file__).parent / "fixtures" / "mock_search_output.json"

        with patch(
            "sys.argv",
            [
                "filter_metadata.py",
                "--input",
                str(fixture_path),
                "--output",
                "test_output.csv",
                "--min-coverage",
                "50",
                "--max-coverage",
                "250",
            ],
        ):
            from filter_metadata import main

            main()

        # Verify to_csv was called
        mock_to_csv.assert_called_once()

    @patch("filter_metadata.pd.DataFrame.to_csv")
    def test_main_with_csv_input(self, mock_to_csv):
        """Test main function with CSV input"""

        # Create a temporary CSV file with test data
        csv_data = """Run,ScientificName,Bases
SRR001,Listeria monocytogenes,300000000
SRR002,Listeria monocytogenes,450000000"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_data)
            csv_file = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "filter_metadata.py",
                    "--input",
                    csv_file,
                    "--output",
                    "test_output.csv",
                    "--min-coverage",
                    "50",
                    "--max-coverage",
                    "250",
                ],
            ):
                from filter_metadata import main

                main()

            # Verify to_csv was called
            mock_to_csv.assert_called_once()
        finally:
            if os.path.exists(csv_file):
                os.unlink(csv_file)

    def test_main_unsupported_file_type(self):
        """Test main function exits with unsupported file type"""
        # Create a temporary .txt file to trigger the error
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            txt_file = f.name

        try:
            with patch(
                "sys.argv", ["filter_metadata.py", "--input", txt_file, "--output", "output.csv"]
            ):
                from filter_metadata import main

                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
        finally:
            # Clean up
            if os.path.exists(txt_file):
                os.unlink(txt_file)

    def test_main_file_not_found(self):
        """Test main function exits when input file doesn't exist"""
        with patch(
            "sys.argv",
            ["filter_metadata.py", "--input", "/nonexistent/file.json", "--output", "output.csv"],
        ):
            from filter_metadata import main

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("filter_metadata.pd.DataFrame.to_csv")
    @patch("filter_metadata.Path.exists")
    def test_main_empty_results(self, mock_exists, mock_to_csv):
        """Test main function with no matching results"""
        mock_exists.return_value = True  # Pretend file exists

        # Create mock data with coverage outside range
        mock_data = {
            "organism": "Listeria monocytogenes",
            "query": "test",
            "total_count": 1,
            "retrieved_count": 1,
            "summaries": [
                {
                    "Runs": '<Run acc="SRR123" total_bases="30000000"/>',  # 10x, below min
                    "ExpXml": "<Summary><Title>Test</Title></Summary>",
                    "CreateDate": "2025/12/31",
                    "UpdateDate": "2025/12/31",
                }
            ],
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            with patch(
                "sys.argv",
                [
                    "filter_metadata.py",
                    "--input",
                    "test.json",
                    "--output",
                    "output.csv",
                    "--min-coverage",
                    "50",
                    "--max-coverage",
                    "250",
                    "--no-verify-s3",
                ],
            ):
                from filter_metadata import main

                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

    def test_main_empty_json_file(self):
        """Test main function with empty JSON file (no summaries)"""

        # Create mock data with empty summaries list
        mock_data = {
            "organism": "Listeria monocytogenes",
            "query": "test",
            "total_count": 0,
            "retrieved_count": 0,
            "summaries": [],
        }

        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mock_data, f)
            json_file = f.name

        try:
            with patch(
                "sys.argv", ["filter_metadata.py", "--input", json_file, "--output", "output.csv"]
            ):
                from filter_metadata import main

                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
        finally:
            # Clean up
            if os.path.exists(json_file):
                os.unlink(json_file)

    def test_main_invalid_json_schema(self):
        """Test main function with invalid JSON schema"""
        # Create file with invalid schema (missing required fields)
        invalid_data = {
            "organism": "Test",
            # Missing query, total_count, retrieved_count, summaries
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            json_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_file = f.name

        try:
            with patch(
                "sys.argv", ["filter_metadata.py", "--input", json_file, "--output", csv_file]
            ):
                with pytest.raises(SystemExit) as exc_info:
                    runpy.run_module("scripts.filter_metadata", run_name="__main__")
                assert exc_info.value.code == 1
        finally:
            for f in [json_file, csv_file]:
                if os.path.exists(f):
                    os.unlink(f)

    def test_main_mismatched_counts_in_json(self):
        """Test main function with mismatched retrieved_count and summaries length"""
        invalid_data = {
            "organism": "Test",
            "query": "test query",
            "total_count": 100,
            "retrieved_count": 5,  # Says 5 but only 1 summary
            "summaries": [
                {
                    "Runs": '<Run acc="SRR123" total_bases="100000"/>',
                    "ExpXml": "<Summary><Title>Test</Title></Summary>",
                    "CreateDate": "2024/01/01",
                    "UpdateDate": "2024/01/01",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            json_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_file = f.name

        try:
            with patch(
                "sys.argv", ["filter_metadata.py", "--input", json_file, "--output", csv_file]
            ):
                with pytest.raises(SystemExit) as exc_info:
                    runpy.run_module("scripts.filter_metadata", run_name="__main__")
                assert exc_info.value.code == 1
        finally:
            for f in [json_file, csv_file]:
                if os.path.exists(f):
                    os.unlink(f)

    def test_main_json_parsing_error(self):
        """Test main function with JSON that can't be parsed"""
        # Create file with invalid JSON (not even valid JSON syntax)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json content")  # Invalid JSON
            json_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_file = f.name

        try:
            with patch(
                "sys.argv", ["filter_metadata.py", "--input", json_file, "--output", csv_file]
            ):
                with pytest.raises(SystemExit) as exc_info:
                    runpy.run_module("scripts.filter_metadata", run_name="__main__")
                assert exc_info.value.code == 1
        finally:
            for f in [json_file, csv_file]:
                if os.path.exists(f):
                    os.unlink(f)


def test_module_execution():
    """Test that the module can be executed as __main__"""
    # This ensures the if __name__ == "__main__": line is covered

    # Create a temporary JSON file with test data
    mock_data = {
        "organism": "Listeria monocytogenes",
        "query": "test",
        "total_count": 1,
        "retrieved_count": 1,
        "summaries": [
            {
                "Runs": '<Run acc="SRR123" total_bases="300000000"/>',
                "ExpXml": "<Summary><Title>Test</Title></Summary>",
                "CreateDate": "2025/12/31",
                "UpdateDate": "2025/12/31",
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as infile:
        json.dump(mock_data, infile)
        input_file = infile.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as outfile:
        output_file = outfile.name

    try:
        with patch(
            "sys.argv", ["filter_metadata.py", "--input", input_file, "--output", output_file]
        ):
            # Use runpy to execute the module as __main__
            # This will trigger the if __name__ == "__main__": block
            runpy.run_module("scripts.filter_metadata", run_name="__main__")
    except SystemExit:
        # Expected to exit successfully
        pass
    finally:
        for f in [input_file, output_file]:
            if os.path.exists(f):
                os.unlink(f)


class TestS3Functionality:
    """Test S3 path construction and verification"""

    def test_construct_s3_path_valid(self):
        """Test S3 path construction for valid accession"""
        path = construct_s3_path("SRR36650731")
        assert path == "s3://sra-pub-run-odp/sra/SRR36650731/SRR36650731"

    def test_construct_s3_path_different_accession(self):
        """Test S3 path construction with different accession number"""
        path = construct_s3_path("SRR12345678")
        assert path == "s3://sra-pub-run-odp/sra/SRR12345678/SRR12345678"

    def test_construct_s3_path_empty(self):
        """Test S3 path construction with empty accession"""
        path = construct_s3_path("")
        assert path == ""

    def test_construct_s3_path_none(self):
        """Test S3 path construction with None accession"""
        path = construct_s3_path(None)
        assert path == ""

    def test_construct_s3_path_invalid_prefix(self):
        """Test S3 path construction with non-SRR prefix"""
        path = construct_s3_path("ERR12345678")
        assert path == ""

    def test_verify_s3_path_valid_format(self):
        """Test S3 path verification with valid path format"""
        # Mock boto3 to avoid actual S3 calls
        with patch("filter_metadata.BOTO3_AVAILABLE", True):
            with patch("filter_metadata.boto3") as mock_boto3:
                mock_s3 = mock_boto3.client.return_value
                mock_s3.list_objects_v2.return_value = {"Contents": [{"Key": "test"}]}

                result = verify_s3_path("s3://sra-pub-run-odp/sra/SRR36650731/SRR36650731")
                assert result is True

                # Verify it used unsigned config
                mock_boto3.client.assert_called_once()
                call_args = mock_boto3.client.call_args
                assert call_args[0][0] == "s3"

    def test_verify_s3_path_not_found(self):
        """Test S3 path verification when path doesn't exist"""
        with patch("filter_metadata.BOTO3_AVAILABLE", True):
            with patch("filter_metadata.boto3") as mock_boto3:
                mock_s3 = mock_boto3.client.return_value
                mock_s3.list_objects_v2.return_value = {}  # No Contents key

                result = verify_s3_path("s3://sra-pub-run-odp/sra/SRR99999999/SRR99999999")
                assert result is False

    def test_verify_s3_path_client_error(self):
        """Test S3 path verification with client error"""
        with patch("filter_metadata.BOTO3_AVAILABLE", True):
            with patch("filter_metadata.boto3") as mock_boto3:
                from botocore.exceptions import ClientError

                mock_s3 = mock_boto3.client.return_value
                mock_s3.list_objects_v2.side_effect = ClientError(
                    {"Error": {"Code": "NoSuchBucket"}}, "ListObjectsV2"
                )

                result = verify_s3_path("s3://invalid-bucket/key")
                assert result is False

    def test_verify_s3_path_no_credentials_error(self):
        """Test S3 path verification with no credentials error"""
        with patch("filter_metadata.BOTO3_AVAILABLE", True):
            with patch("filter_metadata.boto3") as mock_boto3:
                from botocore.exceptions import NoCredentialsError

                mock_s3 = mock_boto3.client.return_value
                mock_s3.list_objects_v2.side_effect = NoCredentialsError()

                result = verify_s3_path("s3://sra-pub-run-odp/sra/SRR123/SRR123")
                assert result is False

    def test_verify_s3_path_unexpected_error(self):
        """Test S3 path verification with unexpected error returns True"""
        with patch("filter_metadata.BOTO3_AVAILABLE", True):
            with patch("filter_metadata.boto3") as mock_boto3:
                mock_s3 = mock_boto3.client.return_value
                mock_s3.list_objects_v2.side_effect = Exception("Unexpected error")

                # Should return True to be conservative
                result = verify_s3_path("s3://sra-pub-run-odp/sra/SRR123/SRR123")
                assert result is True

    def test_verify_s3_path_boto3_not_available(self):
        """Test S3 path verification when boto3 is not available"""
        with patch("filter_metadata.BOTO3_AVAILABLE", False):
            with patch("builtins.print") as mock_print:
                result = verify_s3_path("s3://sra-pub-run-odp/sra/SRR123/SRR123")
                assert result is True
                mock_print.assert_called_once_with(
                    "Warning: boto3 not available, skipping S3 verification"
                )

    def test_verify_s3_path_empty(self):
        """Test S3 path verification with empty path"""
        result = verify_s3_path("")
        assert result is False

    def test_verify_s3_path_invalid_format(self):
        """Test S3 path verification with invalid S3 URI format"""
        result = verify_s3_path("http://example.com/file")
        assert result is False

    def test_verify_s3_path_no_key(self):
        """Test S3 path verification with bucket but no key"""
        result = verify_s3_path("s3://bucket-only")
        assert result is False


class TestS3Integration:
    """Test S3 integration in filter_metadata workflow"""

    def test_filter_metadata_adds_s3_paths(self):
        """Test that filter_metadata adds S3 paths to output"""
        # Create test data with valid SRR accessions
        test_data = pd.DataFrame(
            {
                "Accession": ["SRR36650731", "SRR36650732"],
                "BioProject": ["PRJNA123", "PRJNA123"],
                "Title": ["Test 1", "Test 2"],
                "CreateDate": ["2025/12/31", "2025/12/31"],
                "UpdateDate": ["2025/12/31", "2025/12/31"],
                "Runs": ["<Run/>", "<Run/>"],
                "bases": [480_000_000, 480_000_000],
                "Organism": ["Salmonella enterica", "Salmonella enterica"],
                "Genus": ["Salmonella", "Salmonella"],
                "Estimated_Coverage": [100, 100],
            }
        )

        result = filter_metadata(
            test_data,
            min_coverage=50,
            max_coverage=150,
            preferred_instruments=None,
            verify_s3=False,
        )

        # Check S3 paths were added
        assert "s3_path" in result.columns
        assert result["s3_path"].iloc[0] == "s3://sra-pub-run-odp/sra/SRR36650731/SRR36650731"
        assert result["s3_path"].iloc[1] == "s3://sra-pub-run-odp/sra/SRR36650732/SRR36650732"

    def test_filter_metadata_with_s3_verification(self):
        """Test that filter_metadata with S3 verification filters correctly"""
        test_data = pd.DataFrame(
            {
                "Accession": ["SRR36650731", "SRR99999999"],
                "BioProject": ["PRJNA123", "PRJNA123"],
                "Title": ["Test 1", "Test 2"],
                "CreateDate": ["2025/12/31", "2025/12/31"],
                "UpdateDate": ["2025/12/31", "2025/12/31"],
                "Runs": ["<Run/>", "<Run/>"],
                "bases": [480_000_000, 480_000_000],
                "Organism": ["Salmonella enterica", "Salmonella enterica"],
                "Genus": ["Salmonella", "Salmonella"],
                "Estimated_Coverage": [100, 100],
            }
        )

        # Import here to patch it correctly
        from filter_metadata import filter_metadata as fm

        with patch("scripts.filter_metadata.verify_s3_path") as mock_verify:
            # First accession exists, second doesn't
            mock_verify.side_effect = lambda path: "SRR36650731" in path

            result = fm(
                test_data,
                min_coverage=50,
                max_coverage=150,
                preferred_instruments=None,
                verify_s3=True,
            )

            # Should only have one record
            assert len(result) == 1
            assert result["Accession"].iloc[0] == "SRR36650731"

    def test_main_with_s3_verification_flag(self):
        """Test main function with --verify-s3 flag"""
        mock_data = {
            "organism": "Salmonella enterica",
            "query": "test",
            "total_count": 1,
            "retrieved_count": 1,
            "summaries": [
                {
                    "Runs": '<Run acc="SRR36650731" total_bases="480000000"/>',
                    "ExpXml": "<Summary><Title>Test</Title></Summary>",
                    "CreateDate": "2025/12/31",
                    "UpdateDate": "2025/12/31",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as infile:
            json.dump(mock_data, infile)
            input_file = infile.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as outfile:
            output_file = outfile.name

        try:
            with patch(
                "sys.argv",
                [
                    "filter_metadata.py",
                    "--input",
                    input_file,
                    "--output",
                    output_file,
                    "--verify-s3",
                ],
            ):
                with patch("filter_metadata.verify_s3_path", return_value=True):
                    runpy.run_module("scripts.filter_metadata", run_name="__main__")

            # Verify output file was created and has S3 path
            df = pd.read_csv(output_file)
            assert "s3_path" in df.columns
            assert df["s3_path"].iloc[0] == "s3://sra-pub-run-odp/sra/SRR36650731/SRR36650731"
        finally:
            for f in [input_file, output_file]:
                if os.path.exists(f):
                    os.unlink(f)

    def test_main_with_no_verify_s3_flag(self):
        """Test main function with --no-verify-s3 flag"""
        mock_data = {
            "organism": "Salmonella enterica",
            "query": "test",
            "total_count": 1,
            "retrieved_count": 1,
            "summaries": [
                {
                    "Runs": '<Run acc="SRR36650731" total_bases="480000000"/>',
                    "ExpXml": "<Summary><Title>Test</Title></Summary>",
                    "CreateDate": "2025/12/31",
                    "UpdateDate": "2025/12/31",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as infile:
            json.dump(mock_data, infile)
            input_file = infile.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as outfile:
            output_file = outfile.name

        try:
            with patch(
                "sys.argv",
                [
                    "filter_metadata.py",
                    "--input",
                    input_file,
                    "--output",
                    output_file,
                    "--no-verify-s3",
                ],
            ):
                runpy.run_module("scripts.filter_metadata", run_name="__main__")

            # Verify output file was created with S3 paths
            df = pd.read_csv(output_file)
            assert "s3_path" in df.columns
        finally:
            for f in [input_file, output_file]:
                if os.path.exists(f):
                    os.unlink(f)
