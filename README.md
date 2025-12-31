# SRA Accession Search

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

```bash
# Copy the example config
cp config.example.sh config.sh

# Edit config.sh with your email and API key
# Use any text editor (nano, vim, etc.)
nano config.sh
```

**Important:** Never commit `config.sh` to git! It's already in `.gitignore`.

### 4. Source Credentials

Before running searches, load your credentials:

```bash
source config.sh
```

## Usage

### Basic Search

```bash
python scripts/search_sra.py \
  --email "$NCBI_EMAIL" \
  --api-key "$NCBI_API_KEY" \
  --organism "Salmonella enterica" \
  --output data/salmonella_metadata.json
```

### Search All Target Organisms

```bash
# Make sure credentials are loaded
source config.sh

# Salmonella
python scripts/search_sra.py \
  --email "$NCBI_EMAIL" \
  --api-key "$NCBI_API_KEY" \
  --organism "Salmonella enterica" \
  --output data/salmonella_metadata.json

# E. coli
python scripts/search_sra.py \
  --email "$NCBI_EMAIL" \
  --api-key "$NCBI_API_KEY" \
  --organism "Escherichia coli" \
  --output data/ecoli_metadata.json

# Listeria
python scripts/search_sra.py \
  --email "$NCBI_EMAIL" \
  --api-key "$NCBI_API_KEY" \
  --organism "Listeria monocytogenes" \
  --output data/listeria_metadata.json

# Campylobacter
python scripts/search_sra.py \
  --email "$NCBI_EMAIL" \
  --api-key "$NCBI_API_KEY" \
  --organism "Campylobacter jejuni" \
  --output data/campylobacter_metadata.json

# Staphylococcus
python scripts/search_sra.py \
  --email "$NCBI_EMAIL" \
  --api-key "$NCBI_API_KEY" \
  --organism "Staphylococcus aureus" \
  --output data/staphylococcus_metadata.json

# Streptococcus
python scripts/search_sra.py \
  --email "$NCBI_EMAIL" \
  --api-key "$NCBI_API_KEY" \
  --organism "Streptococcus pneumoniae" \
  --output data/streptococcus_metadata.json
```

### Command-Line Options

**Required:**
- `--email`: Your email address (required by NCBI, no registration needed)
- `--api-key`: Your NCBI API key
- `--organism`: Species name (e.g., "Salmonella enterica")
- `--output`: Output JSON file path

**Optional:**
- `--date-range`: Publication date range (default: `2020:2025`)
- `--max-results`: Maximum records to retrieve (default: `5000`)

### Example with Optional Parameters

```bash
python scripts/search_sra.py \
  --email "$NCBI_EMAIL" \
  --api-key "$NCBI_API_KEY" \
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

## Project Structure

```
sra-accession-search/
├── .git/                      # Git repository
├── .gitignore                 # Ignored files (credentials, data)
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── config.example.sh          # Template for credentials
├── scripts/
│   └── search_sra.py          # Main search script
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

## License

This project is for research and educational purposes.

## Contact

For issues or questions, refer to the NCBI E-utilities documentation:
https://www.ncbi.nlm.nih.gov/books/NBK25500/
