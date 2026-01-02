"""Pydantic models for SRA metadata validation.

This module provides type-safe schemas for validating JSON data structures
used throughout the SRA Accession Search project. These models ensure
data integrity and provide automatic validation with helpful error messages.

Models:
    SRASummary: Individual SRA run summary from NCBI API
    SRASearchResult: Complete output from search_sra.py
    FilteredRecord: Individual filtered record with coverage
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class SRASummary(BaseModel):
    """NCBI SRA summary for a single sequencing run.

    This model represents the data structure returned by NCBI's Entrez.esummary()
    API for SRA records. Fields contain XML-formatted strings that need further
    parsing to extract specific values.

    Attributes:
        Runs: XML string containing run accession and sequencing statistics
              Example: '<Run acc="SRR12345" total_bases="300000000"/>'
        ExpXml: XML string containing experiment metadata and title
                Example: '<Summary><Title>WGS of organism</Title></Summary>'
        CreateDate: Date when SRA record was created (format: YYYY/MM/DD)
        UpdateDate: Date when SRA record was last updated (format: YYYY/MM/DD)

    Example:
        >>> summary = SRASummary(
        ...     Runs='<Run acc="SRR12345" total_bases="300000000"/>',
        ...     ExpXml='<Summary><Title>Test</Title></Summary>',
        ...     CreateDate="2024/01/15",
        ...     UpdateDate="2024/01/15"
        ... )
        >>> summary.Runs
        '<Run acc="SRR12345" total_bases="300000000"/>'
    """

    Runs: str = Field(..., description="XML string with run accession and stats")
    ExpXml: str = Field(..., description="XML string with experiment metadata")
    CreateDate: str = Field(..., description="Creation date (YYYY/MM/DD)")
    UpdateDate: str = Field(..., description="Last update date (YYYY/MM/DD)")

    # Allow extra fields that NCBI might return
    model_config = {"extra": "allow"}

    @field_validator("CreateDate", "UpdateDate")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date string is in YYYY/MM/DD format.

        Args:
            v: Date string to validate

        Returns:
            Original date string if valid

        Raises:
            ValueError: If date format is invalid
        """
        if not v:
            return v
        try:
            # Try to parse as YYYY/MM/DD
            datetime.strptime(v, "%Y/%m/%d")
        except ValueError:
            raise ValueError(f"Date must be in YYYY/MM/DD format, got: {v}")
        return v


class SRASearchResult(BaseModel):
    """Complete output from search_sra.py script.

    This model represents the JSON file structure written by search_sra.py,
    containing metadata about the search query and all retrieved SRA summaries.

    Attributes:
        organism: Scientific name of organism searched (e.g., "Salmonella enterica")
        query: Complete NCBI search query string used
        total_count: Total number of records matching the query in SRA
        retrieved_count: Number of summaries actually retrieved (≤ total_count)
        summaries: List of SRA summary records from NCBI API

    Example:
        >>> result = SRASearchResult(
        ...     organism="Listeria monocytogenes",
        ...     query='"Listeria"[Organism] AND "wgs"[Strategy]',
        ...     total_count=1500,
        ...     retrieved_count=1000,
        ...     summaries=[...]
        ... )
        >>> result.organism
        'Listeria monocytogenes'
    """

    organism: str = Field(..., min_length=1, description="Organism scientific name")
    query: str = Field(..., min_length=1, description="NCBI search query")
    total_count: int = Field(..., ge=0, description="Total matching records in SRA")
    retrieved_count: int = Field(..., ge=0, description="Number of summaries retrieved")
    summaries: list[SRASummary] = Field(
        default_factory=list, description="List of SRA summary records"
    )

    @model_validator(mode="after")
    def validate_counts(self) -> "SRASearchResult":
        """Validate that retrieved_count doesn't exceed total_count.

        Returns:
            Self if valid

        Raises:
            ValueError: If retrieved_count > total_count
        """
        if self.retrieved_count > self.total_count:
            raise ValueError(
                f"retrieved_count ({self.retrieved_count}) cannot exceed "
                f"total_count ({self.total_count})"
            )
        return self

    @model_validator(mode="after")
    def validate_summaries_count(self) -> "SRASearchResult":
        """Validate that number of summaries matches retrieved_count.

        Returns:
            Self if valid

        Raises:
            ValueError: If len(summaries) != retrieved_count
        """
        if len(self.summaries) != self.retrieved_count:
            raise ValueError(
                f"Number of summaries ({len(self.summaries)}) must match "
                f"retrieved_count ({self.retrieved_count})"
            )
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for json.dump()
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SRASearchResult":
        """Create instance from dictionary.

        Args:
            data: Dictionary with search result data

        Returns:
            Validated SRASearchResult instance

        Raises:
            ValidationError: If data doesn't match schema
        """
        return cls.model_validate(data)


class FilteredRecord(BaseModel):
    """Individual filtered record with calculated coverage.

    This model represents a single row from the filtered metadata output,
    typically used after parse_json_metadata() and filter_metadata() processing.

    Attributes:
        Accession: SRA run accession (e.g., "SRR12345")
        BioProject: NCBI BioProject ID (e.g., "PRJNA230403")
        bases: Total sequencing bases (integer)
        Genus: Organism genus name extracted from scientific name
        Estimated_Coverage: Calculated sequencing coverage (bases / genome_size)
        Title: Experiment title from NCBI metadata
        CreateDate: When SRA record was created
        UpdateDate: When SRA record was last updated
        Organism: Full organism scientific name (optional)
        Runs: Raw Runs XML string (optional)

    Example:
        >>> record = FilteredRecord(
        ...     Accession="SRR12345",
        ...     BioProject="PRJNA123456",
        ...     bases=300000000,
        ...     Genus="Listeria",
        ...     Estimated_Coverage=100,
        ...     Title="WGS of Listeria",
        ...     CreateDate="2024/01/15",
        ...     UpdateDate="2024/01/15"
        ... )
        >>> record.Accession
        'SRR12345'
    """

    Accession: str = Field(..., min_length=1, description="SRA run accession")
    BioProject: str = Field(default="", description="NCBI BioProject ID")
    bases: int = Field(..., ge=0, description="Total sequencing bases")
    Genus: str | None = Field(None, description="Organism genus name")
    Estimated_Coverage: int | None = Field(None, ge=0, description="Estimated coverage (x)")
    Title: str = Field(default="", description="Experiment title")
    CreateDate: str = Field(default="", description="Creation date")
    UpdateDate: str = Field(default="", description="Update date")
    Organism: str | None = Field(None, description="Full organism name")
    Runs: str | None = Field(None, description="Raw Runs XML")

    # Allow extra fields (like Platform, LibraryLayout, etc.)
    model_config = {"extra": "allow"}


# Convenience type aliases
SRASearchResults = list[SRASearchResult]
FilteredRecords = list[FilteredRecord]
