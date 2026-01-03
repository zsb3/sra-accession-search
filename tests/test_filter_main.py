"""Unit tests for main CLI function in filter_metadata.py"""

import json
import os
import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from filter_metadata import main  # noqa: E402


# =============================================================================
# MAIN FUNCTION / CLI TESTS
# =============================================================================


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


# =============================================================================
# MODULE EXECUTION TEST
# =============================================================================


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
