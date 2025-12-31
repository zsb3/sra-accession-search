# SRA Accession Search

[![Tests](https://github.com/zsb3/sra-accession-search/actions/workflows/test.yml/badge.svg)](https://github.com/zsb3/sra-accession-search/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)](https://github.com/zsb3/sra-accession-search)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Public%20Domain-lightgrey)](LICENSE)

Search NCBI SRA for bacterial paired-end Illumina WGS data suitable for genome assembly pipelines.

## Overview

This tool searches the NCBI Sequence Read Archive (SRA) for high-quality bacterial whole genome sequencing data with the following criteria:
- Paired-end Illumina sequencing
- Whole genome sequencing (WGS) strategy
- 50-250x coverage range (estimated)
- Recent data (2020-2025 by default)

## Target Organisms

The project focuses on six bacterial genera of public health importance:
- *Salmonella* (esp. *S. enterica*)
- *Escherichia coli*
- *Listeria* (esp. *L. monocytogenes*)
- *Campylobacter* (esp. *C. jejuni*)
- *Staphylococcus* (esp. *S. aureus*)
- *Streptococcus* (esp. *S. pneumoniae*)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get NCBI API Key

1. Create a free NCBI account at https://www.ncbi.nlm.nih.gov/account/
2. Go to Settings → API Key Management
3. Click "Create an API Key"
4. Copy your API key

### 3. Configure Credentials

### 3. Configure NCBI Credentials

**Email (Required):**
NCBI requires an email address for all API requests.

**API Key (Optional but Recommended):**
An API key increases rate limits from 3 to 10 requests/second, significantly speeding up large searches.

**Option A: Environment Variables (Recommended)**

Add to your `~/.bashrc` or `~/.bash_profile`:

```bash
export NCBI_EMAIL="your.email@example.com"
export NCBI_API_KEY="your_api_key_here"  # Optional but recommended
```

Get a free API key at: https://www.ncbi.nlm.nih.gov/account/settings/

Then reload your shell:

```bash
source ~/.bashrc
```

**Option B: Config File (Alternative)**

```bash
# Copy the example config
cp config.example.sh config.sh

# Edit config.sh with your email and API key
nano config.sh

# Source it before running scripts
source config.sh
```

**Important:** Never commit credentials to git! Both `config.sh` and your API key are already in `.gitignore`.

## Usage

### Basic Search

With environment variables configured (recommended):

```bash
python scripts/search_sra.py \
  --organism "Salmonella enterica" \
  --output data/salmonella_metadata.json
```

Or override with command-line arguments:

```bash
python scripts/search_sra.py \
  --email "your.email@example.com" \
  --api-key "your_api_key" \
  --organism "Salmonella enterica" \
  --output data/salmonella_metadata.json
```

### Search All Target Organisms

```bash
# Salmonella
python scripts/search_sra.py \
  --organism "Salmonella enterica" \
  --output data/salmonella_metadata.json

# E. coli
python scripts/search_sra.py \
  --organism "Escherichia coli" \
  --output data/ecoli_metadata.json

# Listeria
python scripts/search_sra.py \
  --organism "Listeria monocytogenes" \
  --output data/listeria_metadata.json

# Campylobacter
python scripts/search_sra.py \
  --organism "Campylobacter jejuni" \
  --output data/campylobacter_metadata.json

# Staphylococcus
python scripts/search_sra.py \
  --organism "Staphylococcus aureus" \
  --output data/staphylococcus_metadata.json

# Streptococcus
python scripts/search_sra.py \
  --organism "Streptococcus pneumoniae" \
  --output data/streptococcus_metadata.json
```

### Command-Line Options

**Required:**
- `--organism`: Species name (e.g., "Salmonella enterica")
- `--output`: Output JSON file path

**Optional:**
- `--email`: Your email address (default: from `NCBI_EMAIL` env var)
- `--api-key`: Your NCBI API key (default: from `NCBI_API_KEY` env var)
- `--date-range`: Publication date range (default: `2020:2025`)
- `--max-results`: Maximum records to retrieve (default: `5000`)

### Example with Optional Parameters

```bash
python scripts/search_sra.py \
  --organism "Salmonella enterica" \
  --output data/salmonella_recent.json \
  --date-range "2023:2025" \
  --max-results 1000
```

## Output

The script creates JSON files in the `data/` directory containing:
- Search metadata (organism, query, counts)
- SRA run summaries for all matching records

These files can then be filtered based on coverage, quality metrics, and other criteria.

## Filtering Results

After searching SRA, you'll likely want to filter the results based on coverage and quality metrics.

### Using the Filter Script

```bash
# Filter Salmonella results for 80-150x coverage
python scripts/filter_metadata.py \
  --input data/salmonella_metadata.json \
  --output results/salmonella_filtered.csv \
  --min-coverage 80 \
  --max-coverage 150

# Filter with preferred instruments
python scripts/filter_metadata.py \
  --input data/ecoli_metadata.json \
  --output results/ecoli_filtered.csv \
  --min-coverage 50 \
  --max-coverage 250 \
  --instruments NextSeq NovaSeq MiSeq
```

### Filter Options

- `--input`: Input JSON (from search_sra.py) or CSV file
- `--output`: Output CSV file for filtered results
- `--min-coverage`: Minimum coverage (default: 50x)
- `--max-coverage`: Maximum coverage (default: 250x)
- `--instruments`: Preferred sequencing instruments (optional)

The filter script will:
- Calculate estimated coverage based on genome size
- Filter for paired-end Illumina data
- Filter by coverage range
- Optionally filter by instrument model
- Sort by coverage (highest first)
- Provide coverage statistics

## Project Structure

```
sra-accession-search/
├── .git/                      # Git repository
├── .gitignore                 # Ignored files (credentials, data)
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── config.example.sh          # Template for credentials
├── scripts/
│   ├── search_sra.py          # Search NCBI SRA database
│   └── filter_metadata.py     # Filter results by coverage/quality
├── data/                      # Raw metadata (gitignored)
│   └── .gitkeep
└── results/                   # Filtered results (gitignored)
    └── .gitkeep
```

## Notes

- Each search may take several minutes depending on the number of results
- With an API key, searches are ~3x faster (10 requests/sec vs 3 requests/sec)
- Data files are excluded from git to avoid repository bloat
- The `project_background.md` file (if present) contains detailed methodology and is gitignored

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=scripts --cov-report=term

# Run specific test file
pytest tests/test_search_sra.py -v

# Run with coverage report in HTML
pytest tests/ --cov=scripts --cov-report=html
# Open htmlcov/index.html in browser
```

### CI/CD

The project uses GitHub Actions for continuous integration:

**Test Workflow** (`.github/workflows/test.yml`):
- Runs on every push and pull request
- Tests across Python 3.10, 3.11, and 3.12
- Enforces 85% minimum code coverage
- Includes optional integration tests (requires NCBI secrets)
- Uploads coverage reports and artifacts

**Release Workflow** (`.github/workflows/release.yml`):
- Triggers on version tags (e.g., `v1.0.0`)
- Runs full test suite
- Creates GitHub releases automatically

### Code Quality

```bash
# Check code formatting
black --check scripts/ tests/

# Format code
black scripts/ tests/

# Lint code
flake8 scripts/ tests/
```

## Troubleshooting

**"No results found":**
- Check organism name spelling
- Try broader date range
- Verify organism has SRA data available

**Rate limiting errors:**
- Ensure API key is set correctly
- Check you're not running multiple instances simultaneously

**Import errors:**
- Verify all dependencies are installed: `pip install -r requirements.txt`

**GitHub Actions workflow push rejected:**
- If you see "refusing to allow a Personal Access Token to create or update workflow", you need a token with `workflow` scope
- Alternative: Create the workflow files directly on GitHub's web interface

## License

This project is for research and educational purposes.

## Contact

For issues or questions, refer to the NCBI E-utilities documentation:
https://www.ncbi.nlm.nih.gov/books/NBK25500/
