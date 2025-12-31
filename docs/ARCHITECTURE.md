# Architecture Documentation

## System Overview

The SRA Accession Search project consists of two main command-line tools that work in sequence to find and filter bacterial WGS data from NCBI's Sequence Read Archive.

```
User Request
     ↓
┌────────────────────────────────────────────┐
│  Step 1: Search SRA (search_sra.py)       │
│  - Build query for organism                │
│  - Call NCBI E-utilities API               │
│  - Fetch metadata summaries                │
│  - Save to JSON                            │
└────────────────┬───────────────────────────┘
                 │
                 ↓ JSON metadata file
                 │
┌────────────────────────────────────────────┐
│  Step 2: Filter Results (filter_metadata) │
│  - Parse JSON/CSV input                    │
│  - Calculate coverage estimates            │
│  - Apply filters (coverage, platform, etc) │
│  - Sort by coverage/date                   │
│  - Save to CSV                             │
└────────────────┬───────────────────────────┘
                 │
                 ↓ Filtered CSV results
                 │
            User Analysis
```

## Component Details

### 1. Search Module (`scripts/search_sra.py`)

**Purpose**: Query NCBI SRA for organism-specific WGS data

**Key Functions**:
```python
build_query(organism, date_range) -> str
    Constructs NCBI search query with filters:
    - Organism name
    - Illumina platform
    - Paired-end layout
    - WGS strategy
    - Publication date range

search_sra(query, retmax) -> dict
    Executes esearch, returns:
    - Count: Total matching records
    - WebEnv: Web environment token
    - QueryKey: Query session key

fetch_summaries(webenv, query_key, retmax) -> list[dict]
    Retrieves summaries via esummary in batches
    - Batch size: 500 records
    - Rate limiting: Sleeps 0.4s between batches
    - Returns: Runs, ExpXml, dates for each record

main()
    CLI orchestration:
    1. Parse arguments
    2. Set NCBI credentials
    3. Build query
    4. Search SRA
    5. Fetch summaries
    6. Save JSON output
```

**Data Flow**:
```
CLI Args → build_query() → NCBI esearch API
                              ↓
                    WebEnv + QueryKey
                              ↓
                    NCBI esummary API (batched)
                              ↓
                    Raw summaries (XML in JSON)
                              ↓
                    JSON file output
```

**External Dependencies**:
- `Bio.Entrez.esearch()` - Search SRA database
- `Bio.Entrez.esummary()` - Fetch detailed summaries
- Rate limits: 3 req/s (no key) or 10 req/s (with key)

### 2. Filter Module (`scripts/filter_metadata.py`)

**Purpose**: Filter and rank SRA results by coverage and quality

**Key Functions**:
```python
calculate_coverage(bases, genus) -> int
    Coverage = bases / (genome_size_mb * 1_000_000)
    - Looks up genome size from GENOME_SIZES dict
    - Defaults to 5.0 Mb for unknown organisms
    - Returns rounded integer

extract_summary_data(summaries) -> list[dict]
    Parses SRA summaries from JSON:
    - Extracts accession from Runs XML
    - Extracts bases from Runs XML
    - Extracts title from ExpXml
    - Extracts dates
    
parse_json_metadata(filepath) -> pd.DataFrame
    - Reads search_sra.py JSON output
    - Calls extract_summary_data()
    - Extracts genus from organism name
    - Returns DataFrame

parse_csv_metadata(filepath) -> pd.DataFrame
    - Reads CSV with ScientificName or Organism column
    - Extracts genus
    - Returns DataFrame

filter_metadata(df, min_cov, max_cov, instruments) -> pd.DataFrame
    Applies filters:
    1. Calculate coverage (adds Estimated_Coverage column)
    2. Filter by coverage range
    3. Filter for PAIRED layout (if column exists)
    4. Filter for ILLUMINA platform (if column exists)
    5. Filter by instrument models (if specified)
    6. Sort by coverage (desc) or release date (desc)

main()
    CLI orchestration:
    1. Parse arguments
    2. Read input file (JSON or CSV)
    3. Filter data
    4. Display statistics
    5. Save CSV output
```

**Data Flow**:
```
JSON/CSV Input → parse_*_metadata() → DataFrame
                                         ↓
                            Add genus column
                                         ↓
                            filter_metadata()
                                         ↓
                    Calculate coverage → Filter → Sort
                                         ↓
                            Display stats
                                         ↓
                            CSV output
```

**Filtering Logic**:
```
Input DataFrame
    ↓
Calculate Coverage (using GENOME_SIZES)
    ↓
Filter: min_coverage <= coverage <= max_coverage
    ↓
Filter: LibraryLayout == 'PAIRED' (if column exists)
    ↓
Filter: Platform == 'ILLUMINA' (if column exists)
    ↓
Filter: Model in preferred_instruments (if specified)
    ↓
Sort: By Estimated_Coverage DESC or ReleaseDate DESC
    ↓
Output DataFrame
```

## Data Structures

### GENOME_SIZES Dictionary
```python
GENOME_SIZES = {
    "Salmonella": 4.8,    # Mb
    "Escherichia": 5.0,
    "Listeria": 3.0,
    # ... etc
}
```
**Purpose**: Source of truth for genome size lookups  
**Key**: Genus name (first word of scientific name)  
**Value**: Genome size in megabases (Mb)  
**Source**: NCBI genome assemblies, literature

### JSON Output Format (search_sra.py)
```json
{
  "organism": "Listeria monocytogenes",
  "query": "\"Listeria monocytogenes\"[Organism] AND ...",
  "total_count": 1500,
  "retrieved_count": 1500,
  "summaries": [
    {
      "Runs": "<Run acc=\"SRR123\" total_bases=\"300000000\"/>",
      "ExpXml": "<Summary><Title>WGS of L. mono</Title></Summary>",
      "CreateDate": "2024/01/15",
      "UpdateDate": "2024/01/15"
    }
  ]
}
```

### CSV Output Format (filter_metadata.py)
```csv
Accession,bases,Genus,Estimated_Coverage,Title,CreateDate,UpdateDate
SRR123,300000000,Listeria,100,WGS of L. mono,2024/01/15,2024/01/15
```

## Testing Architecture

### Test Organization
```
tests/
├── test_search_sra.py       # 18 tests
│   ├── TestBuildQuery
│   ├── TestSearchSRA
│   ├── TestFetchSummaries
│   ├── TestMainFunction
│   └── TestGetRunInfo
├── test_filter_metadata.py  # 37 tests
│   ├── TestCalculateCoverage
│   ├── TestExtractSummaryData
│   ├── TestParseJsonMetadata
│   ├── TestParseCSVMetadata
│   ├── TestFilterMetadata
│   └── TestMainFunction
└── fixtures/
    ├── mock_search_output.json
    ├── mock_summaries.json
    └── mock_search_response.json
```

### Mocking Strategy

**NCBI API Mocking**:
```python
# Mock Bio.Entrez responses with BytesIO
xml_response = b'<?xml version="1.0"?>...'
mock_esearch.return_value = io.BytesIO(xml_response)

# Mock Entrez.read() returns
mock_read.return_value = {'Count': '100', 'WebEnv': 'test'}
```

**File Operation Mocking**:
```python
# Use tempfile for actual file operations
with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
    json.dump(data, f)
    # Test with real file
# Auto-cleanup on exit
```

**Coverage Enforcement**:
- Pytest with pytest-cov
- 100% coverage required
- Enforced in CI/CD pipeline
- Reports: HTML, XML, terminal

## Configuration Files

### pyproject.toml
```toml
[tool.pytest.ini_options]
addopts = ["--cov=scripts", "--cov-fail-under=100"]

[tool.black]
line-length = 100
```

### .flake8
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503  # Black compatibility
```

### .cursorrules
Project-specific coding standards for AI assistants

### .ai/
- `context.json` - Machine-readable project metadata
- `prompts.md` - Task templates for common operations

## CI/CD Pipeline

### GitHub Actions Workflows

**test.yml** (Main CI):
```yaml
Triggers: push, pull_request
Matrix: Python 3.10, 3.11, 3.12
Steps:
  1. Checkout code
  2. Setup Python
  3. Install dependencies
  4. Run pytest with coverage
  5. Run black --check
  6. Run flake8
  7. Upload coverage artifacts
  8. (Optional) Integration tests with NCBI secrets
```

**release.yml** (Release Automation):
```yaml
Triggers: Tags matching v*.*.*
Steps:
  1. Run full test suite
  2. Create GitHub release
  3. Upload artifacts
```

## Error Handling

### search_sra.py
- **No email**: Exit with error message
- **No API key**: Warning about rate limits
- **No results**: Exit gracefully with message
- **API errors**: Propagate to user with details

### filter_metadata.py
- **Unsupported file type**: Exit with error, list supported types
- **File not found**: Exit with file path error
- **Empty results**: Exit gracefully with warning
- **Missing columns**: Continue with available data, skip filters

## Performance Considerations

### Batch Processing
- **SRA summaries**: Fetched in 500-record batches
- **Rate limiting**: 0.4s sleep between batches
- **Memory**: Processes entire dataset in memory (acceptable for 5000 records)

### Optimization Points
- **Coverage calculation**: Vectorized pandas operations
- **Filtering**: Sequential pandas boolean indexing
- **Sorting**: Single pandas sort operation

### Scalability
- **Current limits**: ~5000 records (default max)
- **Bottleneck**: NCBI API rate limits
- **Future**: Could add streaming for >10K records

## Security

### Credentials
- **Storage**: Environment variables (~/.bashrc)
- **Never committed**: Listed in .gitignore patterns
- **CI/CD**: GitHub Secrets (optional)

### API Keys
- **Personal repos**: Workflow-scoped token
- **Org repos**: Standard token (no workflow scope)
- **Configuration**: Conditional git config by directory

## Extension Points

### Adding New Organisms
1. Add to GENOME_SIZES with source comment
2. Add test case
3. Verify coverage maintained

### Adding New Filters
1. Add parameter to filter_metadata()
2. Add CLI argument
3. Add test coverage
4. Update documentation

### New Data Sources
Could extend to other NCBI databases:
- GenBank
- Assembly
- BioProject
Same pattern: search → fetch → filter

## Dependencies Graph

```
search_sra.py
    ├── biopython (Bio.Entrez)
    ├── argparse (stdlib)
    ├── json (stdlib)
    ├── time (stdlib)
    └── os (stdlib)

filter_metadata.py
    ├── pandas
    ├── argparse (stdlib)
    ├── json (stdlib)
    ├── sys (stdlib)
    └── pathlib (stdlib)

tests/
    ├── pytest
    ├── pytest-cov
    ├── pytest-mock
    ├── unittest.mock
    ├── io (stdlib)
    ├── tempfile (stdlib)
    └── runpy (stdlib)
```

## Design Patterns

### CLI Pattern
- argparse for argument parsing
- Environment variable fallbacks
- Informative error messages
- Progress indicators

### Data Processing Pipeline
- Read → Transform → Filter → Sort → Write
- Functional approach with pure functions
- Pandas for data manipulation

### Testing Pattern
- Arrange-Act-Assert
- Fixtures for test data
- Mocking for external dependencies
- Temporary files for file operations
