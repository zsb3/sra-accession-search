# SRA Accession Search

[![Tests](https://github.com/zsb3/sra-accession-search/actions/workflows/test.yml/badge.svg)](https://github.com/zsb3/sra-accession-search/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/zsb3/sra-accession-search)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Public%20Domain-lightgrey)](LICENSE)

Search NCBI SRA for bacterial paired-end Illumina WGS data suitable for genome assembly pipelines.

## Overview

This tool searches the NCBI Sequence Read Archive (SRA) for high-quality bacterial whole genome sequencing data with the following criteria:
- Paired-end Illumina sequencing
- Whole genome sequencing (WGS) strategy
- 50-250x coverage range (estimated)
- Recent data (2020-2025 by default)

## For AI Agents 🤖

**Quick Context:**
- 2 main scripts: `search_sra.py` (fetch data) → `filter_metadata.py` (filter by coverage)
- Test everything: `pytest tests/` (100% coverage required)
- Format/lint: `black scripts/ tests/ && flake8 scripts/ tests/`
- See [`.cursorrules`](.cursorrules) for detailed coding standards and patterns
- Common tasks documented in [`.ai/prompts.md`](.ai/prompts.md)

**Key Files:**
- `scripts/filter_metadata.py::GENOME_SIZES` - organism genome size lookup
- `tests/fixtures/` - mock API responses for testing
- `.github/workflows/` - CI/CD configuration

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

### Quick Commands (Makefile)

The project includes a Makefile for common development tasks:

```bash
# Show all available commands
make help

# Install dependencies
make install          # Production dependencies only
make install-dev      # All dependencies + pre-commit hooks

# Testing
make test             # Run tests with coverage
make coverage         # Run tests and open HTML coverage report

# Code quality
make format           # Format code with black
make format-check     # Check formatting without modifying
make lint             # Run flake8 linter
make type-check       # Run mypy type checker
make check            # Run ALL quality checks (format, lint, type-check, test)

# Cleanup
make clean            # Remove cache files and build artifacts

# Run scripts
make run-search ARGS="--organism 'Listeria' --output data.json"
make run-filter ARGS="--input data.json --output results.csv"
```

### Running Tests

```bash
# Using make (recommended)
make test

# Or directly with pytest
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
- Enforces 100% code coverage
- Code quality checks with black, flake8, and mypy
- Includes optional integration tests (requires NCBI secrets)
- Uploads coverage reports and artifacts

**Release Workflow** (`.github/workflows/release.yml`):
- Triggers on version tags (e.g., `v1.0.0`)
- Runs full test suite
- Creates GitHub releases automatically

### Code Quality

The project uses **black** for code formatting, **flake8** for linting, and **mypy** for type checking.

```bash
# Using make (recommended)
make check            # Run all quality checks

# Or individually
make format-check     # Check code formatting
make format           # Format code
make lint             # Lint code
make type-check       # Type check with mypy
```

**Manual commands:**
```bash
# Check code formatting
black --check scripts/ tests/

# Format code
black scripts/ tests/

# Lint code
flake8 scripts/ tests/

# Type check
mypy scripts/
```

**Configuration:**
- Black: 100 character line length (configured in `pyproject.toml`)
- Flake8: Rules in `.flake8` file
- Mypy: Configuration in `pyproject.toml`
- Pre-commit hooks available in `.pre-commit-config.yaml`

**Setup pre-commit hooks** (optional):
```bash
make install-dev
# Or manually:
pip install pre-commit
pre-commit install
# Now black and flake8 will run automatically on git commit
```

## Troubleshooting

### Search Issues

**"No results found":**
- **Check organism name spelling** - Use scientific name (e.g., "Listeria monocytogenes")
- **Try broader date range** - Default is 2020:2025, try 2015:2025
- **Verify SRA data exists** - Search NCBI SRA web interface first
- **Check query construction** - Run with `-v` for verbose output to see actual query

**Too many results / timeout:**
- Use `--max-results` to limit (default: 5000)
- Narrow date range
- Be more specific with organism subspecies

### API Issues

**Rate limiting errors (HTTP 429):**
- **Add API key** - Without it, you're limited to 3 requests/second
- **Don't run parallel searches** - NCBI rate limits per IP
- **Wait and retry** - Rate limits reset after a few minutes

**Connection errors:**
- Check internet connection
- NCBI services occasionally have outages - check https://www.ncbi.nlm.nih.gov/
- Try again in a few minutes

### Coverage Calculation Issues

**Coverage seems wrong:**
- **Check genome size** - Verify `GENOME_SIZES` dict has correct value for your organism
- **Genus mismatch** - Uses first word of organism name as genus
- **Unknown organism** - Defaults to 5 Mb, add specific size to `GENOME_SIZES`

**No records after filtering:**
- Coverage range too narrow - try wider range (e.g., 30-300x)
- Bases data missing from SRA - some records lack this metadata
- Check input file has `bases` column (CSV) or `Runs` field (JSON)

### Testing Issues

**Tests failing:**
```bash
# Run with verbose output
pytest tests/ -v

# Run specific test
pytest tests/test_search_sra.py::TestBuildQuery::test_basic_query -v

# Check coverage
pytest tests/ --cov=scripts --cov-report=term-missing
```

**Import errors in tests:**
- Ensure you're in project root directory
- Check virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Code Quality Issues

**Black formatting fails:**
```bash
# See what would change
black --check --diff scripts/ tests/

# Apply changes
black scripts/ tests/
```

**Flake8 errors:**
- Check `.flake8` config for rules
- Common: E501 (line too long), F401 (unused import)
- Fix automatically where possible, or add `# noqa: <code>` with justification

### Git/GitHub Issues

**Workflow push rejected:**
- If you see "refusing to allow a Personal Access Token to create or update workflow"
- Need a token with `workflow` scope for `.github/workflows/` changes
- See conditional git config in `~/.gitconfig` for token management

**CI tests fail but pass locally:**
- Different Python version - CI tests 3.10, 3.11, 3.12
- Missing dependency in `requirements.txt`
- Check GitHub Actions logs for specific error

### Environment Issues

**NCBI credentials not found:**
```bash
# Check environment variables
echo $NCBI_EMAIL
echo $NCBI_API_KEY

# Check ~/.bashrc
grep NCBI ~/.bashrc

# Reload environment
source ~/.bashrc
```

**Wrong Python version:**
```bash
# Check version
python --version  # Should be 3.10+

# Use specific version
python3.11 -m pip install -r requirements.txt
python3.11 scripts/search_sra.py ...
```

### Getting Help

**Still stuck?**
1. Check `.cursorrules` for project-specific patterns
2. Look at existing tests for examples
3. Review git history: `git log --oneline`
4. Search issues on GitHub (if public repo)

**For NCBI API questions:**
- E-utilities documentation: https://www.ncbi.nlm.nih.gov/books/NBK25500/
- SRA help: https://www.ncbi.nlm.nih.gov/sra/docs/

## License

This project is for research and educational purposes.

## Contact

For issues or questions, refer to the NCBI E-utilities documentation:
https://www.ncbi.nlm.nih.gov/books/NBK25500/
