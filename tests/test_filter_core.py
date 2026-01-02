"""Unit tests for core filtering logic in filter_metadata.py"""

import sys
from pathlib import Path

import pandas as pd

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from filter_metadata import filter_metadata  # noqa: E402


# =============================================================================
# CORE FILTERING LOGIC TESTS
# =============================================================================


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
