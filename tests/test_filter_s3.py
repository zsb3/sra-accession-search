"""Unit tests for S3 functionality in filter_metadata.py"""

import json
import os
import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from filter_metadata import construct_s3_path, verify_s3_path, filter_metadata  # noqa: E402


# Helper function to mock tqdm.pandas
def mock_tqdm_pandas(*args, **kwargs):
    """Mock tqdm.pandas to make progress_apply use regular apply"""
    pd.Series.progress_apply = pd.Series.apply
    pd.DataFrame.progress_apply = pd.DataFrame.apply


# =============================================================================
# S3 PATH CONSTRUCTION TESTS
# =============================================================================


class TestS3PathConstruction:
    """Test S3 path construction"""

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


# =============================================================================
# S3 PATH VERIFICATION TESTS
# =============================================================================


class TestS3PathVerification:
    """Test S3 path verification"""

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


# =============================================================================
# S3 INTEGRATION TESTS
# =============================================================================


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

    def test_filter_metadata_boto3_not_available(self):
        """Test filter_metadata when boto3 is not available"""
        test_data = pd.DataFrame(
            {
                "Accession": ["SRR36650731"],
                "BioProject": ["PRJNA123"],
                "Title": ["Test 1"],
                "CreateDate": ["2025/12/31"],
                "UpdateDate": ["2025/12/31"],
                "Runs": ["<Run/>"],
                "bases": [480_000_000],
                "Organism": ["Salmonella enterica"],
                "Genus": ["Salmonella"],
                "Estimated_Coverage": [100],
            }
        )

        # Mock BOTO3_AVAILABLE as False to simulate boto3 not installed
        import scripts.filter_metadata as fm_module

        original_boto3_available = fm_module.BOTO3_AVAILABLE

        try:
            fm_module.BOTO3_AVAILABLE = False

            import io
            import sys

            captured_output = io.StringIO()
            sys.stdout = captured_output

            result = fm_module.filter_metadata(
                test_data,
                min_coverage=50,
                max_coverage=150,
                verify_s3=True,  # Request verification but boto3 not available
            )

            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()

            # Should still return data with S3 paths
            assert len(result) == 1
            assert "s3_path" in result.columns

            # Should print warnings
            assert "Warning: boto3 not installed" in output
            assert "Skipping S3 verification" in output

        finally:
            # Restore original value
            fm_module.BOTO3_AVAILABLE = original_boto3_available

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
            
            # Mock tqdm.pandas to make progress_apply just use apply
            with patch("scripts.filter_metadata.tqdm.pandas", side_effect=mock_tqdm_pandas):
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
                    with patch("scripts.filter_metadata.tqdm.pandas", side_effect=mock_tqdm_pandas):
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
