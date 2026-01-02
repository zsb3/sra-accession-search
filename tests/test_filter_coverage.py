"""Unit tests for coverage calculation functionality in filter_metadata.py"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from filter_metadata import calculate_coverage  # noqa: E402


# =============================================================================
# COVERAGE CALCULATION TESTS
# =============================================================================


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
