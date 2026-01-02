"""Unit tests for Pydantic schemas"""

import pytest
from pydantic import ValidationError

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from schemas import SRASummary, SRASearchResult, FilteredRecord  # noqa: E402


class TestSRASummary:
    """Test SRASummary model validation"""

    def test_valid_summary(self):
        """Test creating a valid SRA summary"""
        summary = SRASummary(
            Runs='<Run acc="SRR12345" total_bases="300000000"/>',
            ExpXml="<Summary><Title>Test WGS</Title></Summary>",
            CreateDate="2024/01/15",
            UpdateDate="2024/01/15",
        )
        assert summary.Runs == '<Run acc="SRR12345" total_bases="300000000"/>'
        assert summary.CreateDate == "2024/01/15"

    def test_summary_allows_extra_fields(self):
        """Test that extra NCBI fields are allowed"""
        summary = SRASummary(
            Runs='<Run acc="SRR12345" total_bases="300000000"/>',
            ExpXml="<Summary><Title>Test</Title></Summary>",
            CreateDate="2024/01/15",
            UpdateDate="2024/01/15",
            ExtraField="some_value",  # Extra field from NCBI
        )
        assert summary.model_extra["ExtraField"] == "some_value"

    def test_invalid_date_format(self):
        """Test that invalid date format raises error"""
        with pytest.raises(ValidationError) as exc_info:
            SRASummary(
                Runs='<Run acc="SRR12345"/>',
                ExpXml="<Summary></Summary>",
                CreateDate="2024-01-15",  # Wrong format (should be YYYY/MM/DD)
                UpdateDate="2024/01/15",
            )
        assert "Date must be in YYYY/MM/DD format" in str(exc_info.value)

    def test_missing_required_field(self):
        """Test that missing required fields raise error"""
        with pytest.raises(ValidationError):
            SRASummary(
                Runs='<Run acc="SRR12345"/>',
                ExpXml="<Summary></Summary>",
                CreateDate="2024/01/15",
                # Missing UpdateDate
            )

    def test_empty_date_allowed(self):
        """Test that empty date strings are allowed"""
        summary = SRASummary(Runs="", ExpXml="", CreateDate="", UpdateDate="")  # Empty allowed
        assert summary.CreateDate == ""


class TestSRASearchResult:
    """Test SRASearchResult model validation"""

    def test_valid_search_result(self):
        """Test creating a valid search result"""
        summaries = [
            SRASummary(
                Runs='<Run acc="SRR12345" total_bases="300000000"/>',
                ExpXml="<Summary><Title>Test</Title></Summary>",
                CreateDate="2024/01/15",
                UpdateDate="2024/01/15",
            )
        ]

        result = SRASearchResult(
            organism="Listeria monocytogenes",
            query='"Listeria"[Organism]',
            total_count=100,
            retrieved_count=1,
            summaries=summaries,
        )

        assert result.organism == "Listeria monocytogenes"
        assert result.total_count == 100
        assert result.retrieved_count == 1
        assert len(result.summaries) == 1

    def test_empty_organism_raises_error(self):
        """Test that empty organism raises error"""
        with pytest.raises(ValidationError) as exc_info:
            SRASearchResult(
                organism="",  # Empty not allowed
                query="test",
                total_count=0,
                retrieved_count=0,
                summaries=[],
            )
        assert "at least 1 character" in str(exc_info.value).lower()

    def test_negative_count_raises_error(self):
        """Test that negative counts raise error"""
        with pytest.raises(ValidationError):
            SRASearchResult(
                organism="Test",
                query="test",
                total_count=-1,  # Negative not allowed
                retrieved_count=0,
                summaries=[],
            )

    def test_retrieved_exceeds_total_raises_error(self):
        """Test that retrieved_count > total_count raises error"""
        with pytest.raises(ValidationError) as exc_info:
            SRASearchResult(
                organism="Test",
                query="test",
                total_count=100,
                retrieved_count=150,  # Can't exceed total
                summaries=[],
            )
        assert "cannot exceed total_count" in str(exc_info.value)

    def test_summaries_count_mismatch_raises_error(self):
        """Test that len(summaries) != retrieved_count raises error"""
        summaries = [
            SRASummary(
                Runs='<Run acc="SRR12345"/>',
                ExpXml="<Summary></Summary>",
                CreateDate="2024/01/15",
                UpdateDate="2024/01/15",
            )
        ]

        with pytest.raises(ValidationError) as exc_info:
            SRASearchResult(
                organism="Test",
                query="test",
                total_count=100,
                retrieved_count=5,  # Says 5 but only 1 summary
                summaries=summaries,
            )
        assert "must match retrieved_count" in str(exc_info.value)

    def test_empty_summaries_with_zero_count(self):
        """Test that empty summaries works with zero retrieved_count"""
        result = SRASearchResult(
            organism="Test",
            query="test",
            total_count=0,
            retrieved_count=0,
            summaries=[],  # Empty is OK if count is 0
        )
        assert len(result.summaries) == 0

    def test_to_dict(self):
        """Test converting to dictionary"""
        result = SRASearchResult(
            organism="Test", query="test", total_count=0, retrieved_count=0, summaries=[]
        )
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["organism"] == "Test"
        assert data["summaries"] == []

    def test_from_dict(self):
        """Test creating from dictionary"""
        data = {
            "organism": "Listeria monocytogenes",
            "query": '"Listeria"[Organism]',
            "total_count": 100,
            "retrieved_count": 1,
            "summaries": [
                {
                    "Runs": '<Run acc="SRR12345"/>',
                    "ExpXml": "<Summary></Summary>",
                    "CreateDate": "2024/01/15",
                    "UpdateDate": "2024/01/15",
                }
            ],
        }

        result = SRASearchResult.from_dict(data)
        assert result.organism == "Listeria monocytogenes"
        assert result.total_count == 100
        assert len(result.summaries) == 1
        assert isinstance(result.summaries[0], SRASummary)

    def test_from_dict_with_invalid_data(self):
        """Test that from_dict raises error for invalid data"""
        data = {
            "organism": "Test",
            "query": "test",
            "total_count": "not_a_number",  # Invalid type
            "retrieved_count": 0,
            "summaries": [],
        }

        with pytest.raises(ValidationError):
            SRASearchResult.from_dict(data)


class TestFilteredRecord:
    """Test FilteredRecord model validation"""

    def test_valid_filtered_record(self):
        """Test creating a valid filtered record"""
        record = FilteredRecord(
            Accession="SRR12345",
            BioProject="PRJNA123456",
            bases=300_000_000,
            Genus="Listeria",
            Estimated_Coverage=100,
            Title="WGS of Listeria",
            CreateDate="2024/01/15",
            UpdateDate="2024/01/15",
        )

        assert record.Accession == "SRR12345"
        assert record.BioProject == "PRJNA123456"
        assert record.bases == 300_000_000
        assert record.Estimated_Coverage == 100

    def test_minimal_record(self):
        """Test creating record with only required fields"""
        record = FilteredRecord(Accession="SRR12345", bases=100000)

        assert record.Accession == "SRR12345"
        assert record.bases == 100000
        assert record.BioProject == ""
        assert record.Genus is None
        assert record.Estimated_Coverage is None
        assert record.Title == ""

    def test_negative_bases_raises_error(self):
        """Test that negative bases raises error"""
        with pytest.raises(ValidationError):
            FilteredRecord(Accession="SRR12345", bases=-1000)

    def test_negative_coverage_raises_error(self):
        """Test that negative coverage raises error"""
        with pytest.raises(ValidationError):
            FilteredRecord(Accession="SRR12345", bases=100000, Estimated_Coverage=-10)

    def test_allows_extra_fields(self):
        """Test that extra fields like Platform are allowed"""
        record = FilteredRecord(
            Accession="SRR12345",
            bases=100000,
            Platform="ILLUMINA",  # Extra field
            LibraryLayout="PAIRED",  # Extra field
        )

        assert record.model_extra["Platform"] == "ILLUMINA"
        assert record.model_extra["LibraryLayout"] == "PAIRED"

    def test_none_coverage_for_unknown_organism(self):
        """Test that None coverage is allowed (unknown organism)"""
        record = FilteredRecord(
            Accession="SRR12345",
            bases=100000,
            Genus="Unknown",
            Estimated_Coverage=None,  # None allowed
        )

        assert record.Estimated_Coverage is None


class TestSchemaIntegration:
    """Test schemas working together"""

    def test_full_search_result_workflow(self):
        """Test creating a complete search result and converting to dict"""
        summaries = [
            SRASummary(
                Runs='<Run acc="SRR12345" total_bases="300000000"/>',
                ExpXml="<Summary><Title>Listeria WGS</Title></Summary>",
                CreateDate="2024/01/15",
                UpdateDate="2024/01/15",
            ),
            SRASummary(
                Runs='<Run acc="SRR67890" total_bases="500000000"/>',
                ExpXml="<Summary><Title>Salmonella WGS</Title></Summary>",
                CreateDate="2024/02/20",
                UpdateDate="2024/02/20",
            ),
        ]

        result = SRASearchResult(
            organism="Listeria monocytogenes",
            query='"Listeria"[Organism] AND "wgs"[Strategy]',
            total_count=1500,
            retrieved_count=2,
            summaries=summaries,
        )

        # Convert to dict and back
        data = result.to_dict()
        result2 = SRASearchResult.from_dict(data)

        assert result2.organism == result.organism
        assert result2.total_count == result.total_count
        assert len(result2.summaries) == len(result.summaries)

    def test_realistic_data_from_fixtures(self):
        """Test with realistic data matching test fixtures"""
        data = {
            "organism": "Listeria monocytogenes",
            "query": '"Listeria monocytogenes"[Organism] AND "wgs"[Strategy]',
            "total_count": 100,
            "retrieved_count": 3,
            "summaries": [
                {
                    "Runs": '<Run acc="SRR12345" total_bases="300000000"/>',
                    "ExpXml": "<Summary><Title>Listeria WGS</Title></Summary>",
                    "CreateDate": "2024/01/15",
                    "UpdateDate": "2024/01/15",
                },
                {
                    "Runs": '<Run acc="SRR67890" total_bases="720000000"/>',
                    "ExpXml": "<Summary><Title>Salmonella WGS</Title></Summary>",
                    "CreateDate": "2024/02/20",
                    "UpdateDate": "2024/02/20",
                },
                {
                    "Runs": '<Run acc="SRR11111" total_bases="85000000"/>',
                    "ExpXml": "<Summary><Title>Campylobacter WGS</Title></Summary>",
                    "CreateDate": "2024/03/10",
                    "UpdateDate": "2024/03/10",
                },
            ],
        }

        result = SRASearchResult.from_dict(data)
        assert result.organism == "Listeria monocytogenes"
        assert result.total_count == 100
        assert result.retrieved_count == 3
        assert len(result.summaries) == 3
        assert all(isinstance(s, SRASummary) for s in result.summaries)
