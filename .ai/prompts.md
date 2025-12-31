# AI Agent Task Prompts

Common tasks for AI assistants working on this project, with example prompts and expected outcomes.

## Adding New Organisms

### Task: Add support for a new bacterial organism

**Example Prompt:**
```
Add support for Vibrio cholerae to the project. The genome size is approximately 4.0 Mb 
according to NCBI genome assembly GCA_000006745.1.
```

**Expected Actions:**
1. Add to `GENOME_SIZES` in `scripts/filter_metadata.py`:
   ```python
   "Vibrio": 4.0,  # V. cholerae ~4.0 Mb (NCBI GCA_000006745.1)
   ```

2. Add test case in `tests/test_filter_metadata.py`:
   ```python
   def test_vibrio_coverage():
       """Test coverage calculation for Vibrio"""
       coverage = calculate_coverage(400_000_000, "Vibrio")
       assert coverage == 100  # 400M bases / 4.0 Mb = 100x
   ```

3. Run tests to verify 100% coverage maintained
4. Update README target organisms list if it's a primary focus organism

---

## Searching for Data

### Task: Search SRA for a specific organism

**Example Prompt:**
```
Search SRA for Salmonella enterica data from 2023-2024, limiting to 1000 results.
Save output to data/salmonella_2023.json
```

**Expected Command:**
```bash
python scripts/search_sra.py \
  --organism "Salmonella enterica" \
  --output data/salmonella_2023.json \
  --date-range "2023:2024" \
  --max-results 1000
```

**Verification:**
- Check `data/salmonella_2023.json` exists
- Verify JSON structure: `organism`, `query`, `total_count`, `retrieved_count`, `summaries`
- Confirm summaries contain expected fields: `Runs`, `ExpXml`, dates

---

## Filtering Results

### Task: Filter search results by coverage

**Example Prompt:**
```
Filter the Listeria search results to only include samples with 80-150x coverage.
Save to results/listeria_high_cov.csv
```

**Expected Command:**
```bash
python scripts/filter_metadata.py \
  --input data/listeria_metadata.json \
  --output results/listeria_high_cov.csv \
  --min-coverage 80 \
  --max-coverage 150
```

**Verification:**
- CSV contains columns: `Accession`, `bases`, `Genus`, `Estimated_Coverage`, dates, `Title`
- All `Estimated_Coverage` values between 80-150
- Sorted by coverage (highest first)

---

## Writing Tests

### Task: Add test for new functionality

**Example Prompt:**
```
Add a test for filtering by instrument type. We want to verify that when we specify 
preferred instruments, only those instruments are included in results.
```

**Expected Test:**
```python
def test_filter_by_preferred_instruments(self):
    """Test filtering by preferred instrument models"""
    df = pd.DataFrame({
        'Accession': ['SRR001', 'SRR002', 'SRR003'],
        'bases': [300_000_000, 300_000_000, 300_000_000],
        'Genus': ['Listeria', 'Listeria', 'Listeria'],
        'Model': ['Illumina MiSeq', 'Illumina HiSeq 2500', 'Illumina NovaSeq 6000']
    })
    
    filtered = filter_metadata(
        df, 
        preferred_instruments=['Illumina MiSeq', 'Illumina NovaSeq 6000']
    )
    
    assert len(filtered) == 2
    assert 'SRR002' not in filtered['Accession'].values
```

**Verification:**
```bash
pytest tests/test_filter_metadata.py::test_filter_by_preferred_instruments -v
pytest tests/ --cov=scripts --cov-report=term-missing  # Check coverage
```

---

## Code Quality Tasks

### Task: Fix linting errors

**Example Prompt:**
```
Run flake8 and fix any linting issues found in the codebase.
```

**Expected Actions:**
1. Run flake8: `flake8 scripts/ tests/`
2. Common fixes:
   - Remove unused imports
   - Break long lines (>100 chars)
   - Remove trailing whitespace
   - Fix indentation
3. Re-run flake8 to verify
4. Run tests to ensure nothing broken

---

## Updating Dependencies

### Task: Add new dependency

**Example Prompt:**
```
We need to add click library for better CLI argument handling. Add it as a dependency
and update the search_sra.py script to use it.
```

**Expected Actions:**
1. **Evaluate necessity** - Is argparse sufficient? Why do we need click?
2. Add to `requirements.txt` with version pin:
   ```
   click>=8.1.0,<9.0.0
   ```
3. Update script imports and argument parsing
4. Update tests to work with new CLI interface
5. Run full test suite
6. Update README if CLI interface changed
7. Document in commit message why dependency was added

---

## Debugging Issues

### Task: Investigate test failure

**Example Prompt:**
```
The test test_main_empty_json_file is failing with "assert 0 == 1". 
Debug this and fix the issue.
```

**Expected Investigation:**
1. Run test in isolation with verbose output:
   ```bash
   pytest tests/test_filter_metadata.py::test_main_empty_json_file -vvs
   ```

2. Check what's being asserted:
   ```python
   # Look at the assertion
   assert exc_info.value.code == 0  # Expected exit code 0
   ```

3. Check the actual behavior - does empty file exit with code 0 or 1?

4. Fix either:
   - The test (if expectation is wrong)
   - The code (if behavior is wrong)

5. Verify with: `pytest tests/ --cov=scripts`

---

## Documentation Tasks

### Task: Update README for new feature

**Example Prompt:**
```
We added a --quality-filter option to filter_metadata.py. Update the README to 
document this new option.
```

**Expected Changes:**
1. Add to filter options section:
   ```markdown
   - `--quality-filter`: Minimum quality score (default: 30)
   ```

2. Add example usage:
   ```bash
   python scripts/filter_metadata.py \
     --input data/ecoli.json \
     --output results/ecoli_high_quality.csv \
     --quality-filter 35
   ```

3. Update "What Gets Filtered" section if applicable

---

## Performance Optimization

### Task: Optimize slow operation

**Example Prompt:**
```
The coverage calculation is slow for large datasets. Profile it and suggest optimizations.
```

**Expected Actions:**
1. Add profiling:
   ```python
   import cProfile
   cProfile.run('filter_metadata(large_df)')
   ```

2. Identify bottleneck (likely pandas operations)

3. Potential optimizations:
   - Vectorize operations (avoid iterrows)
   - Use apply() with vectorized functions
   - Cache GENOME_SIZES lookups
   - Use categorical dtype for Genus column

4. Benchmark before/after
5. Ensure tests still pass
6. Document optimization in commit

---

## CI/CD Tasks

### Task: Fix failing GitHub Actions workflow

**Example Prompt:**
```
The CI workflow is failing on Python 3.12 but passes locally. Investigate and fix.
```

**Expected Investigation:**
1. Check GitHub Actions logs for specific error
2. Common issues:
   - Different package versions
   - Missing system dependencies
   - Path differences
   - Environment variable not set

3. Reproduce locally:
   ```bash
   python3.12 -m venv test_env
   source test_env/bin/activate
   pip install -r requirements.txt
   pytest tests/
   ```

4. Fix in workflow file or code as needed
5. Push and verify CI passes

---

## Refactoring Tasks

### Task: Extract reusable function

**Example Prompt:**
```
The code for parsing organism names to genus is duplicated in multiple places.
Extract it into a reusable function.
```

**Expected Actions:**
1. Identify all occurrences of the pattern
2. Create new function:
   ```python
   def extract_genus(organism_name: str) -> str:
       """Extract genus from organism scientific name.
       
       Args:
           organism_name: Full scientific name (e.g., "Listeria monocytogenes")
           
       Returns:
           Genus name (first word)
       """
       return organism_name.split()[0]
   ```

3. Replace all occurrences
4. Add comprehensive tests for edge cases
5. Update existing tests if needed
6. Verify 100% coverage maintained

---

## Quick Reference

### Always Remember
- Run tests after any code change: `pytest tests/`
- Format before committing: `black scripts/ tests/`
- Check linting: `flake8 scripts/ tests/`
- Maintain 100% coverage
- Mock all external API calls in tests
- Use tempfile for test file operations
- Add type hints to new functions
- Follow patterns in `.cursorrules`

### File Structure
```
sra-accession-search/
├── scripts/
│   ├── search_sra.py      # Search NCBI SRA
│   └── filter_metadata.py # Filter by coverage
├── tests/
│   ├── test_search_sra.py
│   ├── test_filter_metadata.py
│   └── fixtures/          # Mock API responses
├── .github/workflows/     # CI/CD
├── .cursorrules          # AI coding standards
└── .ai/
    └── prompts.md        # This file
```
