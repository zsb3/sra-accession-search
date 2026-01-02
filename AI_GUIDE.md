# AI Agent Navigation Guide

**For: GitHub Copilot, Claude, GPT-4, and other AI coding assistants**

This guide helps AI agents efficiently navigate and modify the codebase.

## 📁 Repository Structure

```
sra-accession-search/
├── scripts/              # Production code (3 modules, all <400 lines)
│   ├── search_sra.py         # Search NCBI SRA database (~180 lines)
│   ├── filter_metadata.py    # Filter results by coverage/S3 (~390 lines)
│   └── schemas.py            # Pydantic data models (~220 lines)
│
├── tests/                # Test suite (organized by feature, all <400 lines)
│   ├── conftest.py           # Shared fixtures (~340 lines)
│   ├── test_search_sra.py    # SRA search tests (~375 lines)
│   ├── test_schemas.py       # Schema validation tests (~345 lines)
│   ├── test_filter_coverage.py   # Coverage calculation tests
│   ├── test_filter_s3.py         # S3 functionality tests
│   └── test_filter_core.py       # Core filtering logic tests
│
├── .ai/                  # AI-specific resources
│   ├── context.json          # Project context for AI
│   └── prompts.md            # Common prompts/tasks
│
├── .cursorrules          # Coding standards and patterns
├── AI_GUIDE.md           # This file
├── README.md             # User documentation
└── requirements.txt      # Dependencies
```

## 🎯 Quick Navigation

### Finding Code

| What You Need | Command | File Location |
|--------------|---------|---------------|
| Search/filter logic | `grep_search "def filter_metadata"` | `scripts/filter_metadata.py` |
| Coverage calculation | `grep_search "def calculate_coverage"` | `scripts/filter_metadata.py` |
| S3 path functions | `grep_search "def construct_s3_path"` | `scripts/filter_metadata.py` |
| SRA query building | `grep_search "def build_query"` | `scripts/search_sra.py` |
| Data models | `semantic_search "pydantic models"` | `scripts/schemas.py` |
| Test fixtures | `read_file conftest.py` | `tests/conftest.py` |

### Key Functions by File

**`scripts/search_sra.py`** (~180 lines)
- `build_query()` - Construct NCBI search query
- `search_sra()` - Execute SRA search
- `fetch_summaries()` - Get detailed metadata
- `main()` - CLI entry point

**`scripts/filter_metadata.py`** (~390 lines)
- `calculate_coverage()` - Estimate sequencing coverage
- `construct_s3_path()` - Build S3 URI from SRR accession
- `verify_s3_path()` - Check S3 path exists
- `filter_metadata()` - Main filtering function
- `main()` - CLI entry point

**`scripts/schemas.py`** (~220 lines)
- `SRASearchResult` - Validated search results
- `RunInfo` - Sequencing run metadata

## 🔍 Search Strategies

### 1. Finding Specific Functionality

```bash
# ✅ BEST: Use grep for exact names
grep_search "def verify_s3_path"

# ✅ GOOD: Use semantic search for concepts
semantic_search "S3 bucket verification"

# ❌ BAD: Reading entire files blindly
read_file filter_metadata.py 1 390  # Too much at once
```

### 2. Understanding Test Coverage

```bash
# Find tests for a specific function
grep_search "test_calculate_coverage"

# Find all S3-related tests
grep_search "class.*S3" isRegexp=true

# Check what a test file covers
read_file tests/test_filter_s3.py 1 50  # Just the header
```

### 3. Locating Constants/Configuration

```bash
# Find genome size definitions
grep_search "GENOME_SIZES"

# Find S3 bucket configuration
grep_search "sra-pub-run-odp"

# Find CLI argument definitions
grep_search "argparse.ArgumentParser"
```

## 📊 File Size Guidelines

**Keep all files under 500 lines for optimal agent performance**

| File Type | Target Size | Max Size | Reason |
|-----------|-------------|----------|--------|
| Script modules | 200-400 | 500 | Agent attention span |
| Test files | 150-350 | 400 | Easy scanning |
| Config files | < 100 | 200 | Quick reference |

**When a file approaches 400 lines:**
1. Identify logical feature boundaries
2. Split into focused modules
3. Update imports and tests
4. Verify 100% coverage maintained

## 🧪 Testing Pattern Reference

### Test File Organization

Each test file should focus on ONE major feature or component:

```python
# tests/test_filter_s3.py - S3 functionality only
class TestS3PathConstruction:
    """Test S3 path building"""
    
class TestS3PathVerification:
    """Test S3 availability checking"""
    
class TestS3Integration:
    """Test end-to-end S3 workflows"""
```

### Test Naming Convention

```python
def test_<function>_<scenario>_<expected_result>()
    
# ✅ GOOD examples:
def test_calculate_coverage_listeria_returns_correct_value()
def test_verify_s3_path_invalid_format_returns_false()
def test_construct_s3_path_valid_accession_builds_uri()

# ❌ BAD examples:
def test_coverage()  # Too vague
def test_stuff()     # No meaning
def test1()          # No description
```

## 🛠️ Common Modifications

### Adding a New Organism

1. **Find the constant:**
   ```bash
   grep_search "GENOME_SIZES"
   ```

2. **Add entry with documentation:**
   ```python
   GENOME_SIZES = {
       # ... existing ...
       "NewGenus": 4_500_000,  # Average genome size, source: NCBI
   }
   ```

3. **Add test:**
   ```bash
   # Find test location
   grep_search "test.*coverage.*organism"
   # Add test case
   ```

### Adding S3 Functionality

1. **Locate S3 code:**
   ```bash
   grep_search "def.*s3" isRegexp=true
   ```

2. **Read S3 test patterns:**
   ```bash
   read_file tests/test_filter_s3.py 1 100
   ```

3. **Follow existing patterns for:**
   - boto3 client with `UNSIGNED` config
   - Error handling (ClientError, NoCredentialsError)
   - Test mocking with `@patch`

### Adding New CLI Arguments

1. **Find argument parser:**
   ```bash
   grep_search "ArgumentParser"
   ```

2. **Follow pattern:**
   ```python
   parser.add_argument(
       "--new-flag",
       type=str,
       default="value",
       help="Clear description"
   )
   ```

3. **Update help text in README.md**

## 🚨 Before Making Changes

### Pre-Change Checklist

- [ ] Use `grep_search` or `semantic_search` to locate relevant code
- [ ] Read only the specific sections needed (not entire large files)
- [ ] Check for existing tests before adding new ones
- [ ] Verify function signatures in use before modifying them
- [ ] Check if constants/config already exist before adding new ones

### Post-Change Checklist

- [ ] Run: `black scripts/ tests/`
- [ ] Run: `flake8 scripts/ tests/`
- [ ] Run: `mypy scripts/`
- [ ] Run: `pytest tests/ --cov=scripts`
- [ ] Verify: 100% coverage maintained
- [ ] Check: No files exceed 500 lines
- [ ] Update: Docstrings and type hints

## 📋 Common Tasks - Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| Run all tests | `pytest tests/` | Should show 100% coverage |
| Run specific test file | `pytest tests/test_filter_s3.py -v` | Use `-v` for verbose |
| Run one test | `pytest tests/test_filter_s3.py::test_name -v` | Specific function |
| Check coverage | `pytest --cov=scripts --cov-report=term-missing` | Shows missing lines |
| Format code | `black scripts/ tests/` | Auto-formats to 100 chars |
| Lint code | `flake8 scripts/ tests/` | Must pass before commit |
| Type check | `mypy scripts/` | Checks type hints |
| Run quality checks | `make check` | Runs all checks |

## 🔗 Cross-Reference Map

This map shows how components connect:

```
User runs script:
  scripts/search_sra.py
    ↓ validates with
  scripts/schemas.py (SRASearchResult)
    ↓ saves to
  data/organism_metadata.json
    ↓ processes with
  scripts/filter_metadata.py
    ↓ calculates using
  GENOME_SIZES constant
    ↓ constructs with
  construct_s3_path()
    ↓ verifies with
  verify_s3_path()
    ↓ outputs to
  results/organism_filtered.csv
```

## 💡 Agent Tips

1. **Always search before reading** - Use `grep_search` to find exact locations
2. **Read in chunks** - Request specific line ranges, not entire files
3. **Check existing patterns** - Look for similar code before adding new
4. **Preserve coverage** - Every change must maintain 100% test coverage
5. **Keep files small** - Split before reaching 500 lines
6. **Use type hints** - All functions need proper type annotations
7. **Mock external calls** - No real NCBI/AWS calls in tests

## ❓ When Stuck

1. Check `.cursorrules` for coding standards
2. Use `semantic_search` with natural language queries
3. Look at existing tests for patterns
4. Read this guide's cross-reference map
5. Check README.md for user-facing documentation

## 📞 Key Constants to Remember

| Constant | Location | Value | Purpose |
|----------|----------|-------|---------|
| `GENOME_SIZES` | filter_metadata.py | Dict | Organism genome sizes |
| `SRA_S3_BUCKET` | filter_metadata.py | `"sra-pub-run-odp"` | NCBI public bucket |
| `SRA_S3_PREFIX` | filter_metadata.py | `"sra"` | S3 path prefix |
| Line limit | .cursorrules | 500 | Max file length |
| Coverage requirement | pyproject.toml | 100% | Test coverage |
| Line length | pyproject.toml | 100 | Code formatting |

---

**Last Updated**: 2026-01-02
**Maintained By**: Project contributors
**For Issues**: See README.md troubleshooting section
