# Coding Conventions

This document describes naming patterns, code organization, and style conventions beyond what's enforced by black and flake8.

---

## Naming Conventions

### Functions

**Style**: `snake_case`, descriptive verb phrases

**Examples**:
```python
✅ Good
def calculate_coverage(bases, genus):
def build_query(organism, date_range):
def extract_summary_data(summaries):

❌ Bad
def calcCov(b, g):  # camelCase, unclear abbreviations
def query(x, y):     # Too vague
def process(data):   # Generic verb, what does it do?
```

**Guidelines**:
- Use verbs that describe the action: `calculate`, `build`, `extract`, `parse`, `filter`, `fetch`
- Parameter names should be self-documenting
- Avoid abbreviations unless universally understood (e.g., `df` for DataFrame is acceptable)

### Variables

**Style**: `snake_case`, descriptive nouns

**Examples**:
```python
✅ Good
genome_size_mb = 4.8
estimated_coverage = 100
min_coverage = 50
file_path = "data.json"

❌ Bad
gs = 4.8           # Unclear abbreviation
cov = 100          # Too terse
minCov = 50        # camelCase
fp = "data.json"   # Single letter with suffix
```

**Special cases**:
- `df` for pandas DataFrame (widely understood convention)
- `i`, `j`, `k` for loop indices in simple loops only
- Single-letter variables acceptable in list comprehensions: `[x for x in items if x > 0]`

### Constants

**Style**: `UPPER_SNAKE_CASE`, module-level

**Examples**:
```python
✅ Good
GENOME_SIZES = {...}
DEFAULT_MIN_COVERAGE = 50
DEFAULT_MAX_COVERAGE = 250
DEFAULT_DATE_RANGE = "2020/01/01:2025/12/31"

❌ Bad
genome_sizes = {...}    # Not uppercase
GenomeSizes = {...}     # PascalCase
GENOMESIZES = {...}     # No underscores
```

**Guidelines**:
- Use for values that don't change during execution
- Include units in name if applicable: `TIMEOUT_SECONDS`, `SIZE_MB`
- Group related constants in a dictionary if appropriate

### Classes

**Style**: `PascalCase`, noun or noun phrase

**Examples** (if we added classes):
```python
✅ Good
class SRASearcher:
class MetadataFilter:
class CoverageCalculator:

❌ Bad
class sra_searcher:     # snake_case
class search_sra:       # Verb phrase, snake_case
class SRASearcherClass: # Redundant "Class" suffix
```

### Files and Modules

**Style**: `snake_case.py`

**Current structure**:
```
scripts/
  search_sra.py        # Verb phrase, describes action
  filter_metadata.py   # Verb + noun, describes action

tests/
  test_search_sra.py   # Mirror script name with test_ prefix
  test_filter_metadata.py
```

**Guidelines**:
- Module names should match primary function or purpose
- Test files mirror the module they test: `test_<module>.py`
- Use underscores, not hyphens: `search_sra.py`, not `search-sra.py`

---

## Code Organization

### Import Order

**Pattern**: stdlib → third-party → local (enforced by linting tools, documented here for clarity)

```python
# 1. Standard library
import argparse
import json
import sys
from pathlib import Path

# 2. Third-party libraries
import pandas as pd
from Bio import Entrez

# 3. Local imports (if any)
from .utils import helper_function
```

**Within each group**: Alphabetical order

### Function Order in Files

**Pattern**: Public functions → Private helpers → Main entry point

```python
# Public API functions (what users call)
def build_query(organism, date_range):
    ...

def search_sra(query, retmax):
    ...

# Private helper functions
def _parse_xml_run_info(xml_string):
    ...

# Main entry point (if CLI script)
def main():
    ...

if __name__ == "__main__":
    main()
```

**Guidelines**:
- Most important/public functions near top
- Helpers prefixed with `_` to indicate private
- `main()` always at bottom, above `if __name__`
- Order functions by dependency if possible (called functions before callers)

### Constant Placement

**Pattern**: After imports, before functions

```python
import pandas as pd

# Constants
GENOME_SIZES = {
    "Salmonella": 4.8,
    ...
}

DEFAULT_MIN_COVERAGE = 50

# Functions
def calculate_coverage(bases, genus):
    ...
```

---

## Docstrings

### Style: Google-style docstrings

**Function docstrings**:
```python
def calculate_coverage(bases, genus):
    """Calculate estimated sequencing coverage.

    Args:
        bases: Total number of sequencing bases (int or str)
        genus: Genus name for genome size lookup (str)

    Returns:
        Estimated coverage as integer (bases / genome_size)

    Raises:
        ValueError: If bases cannot be converted to int
    """
```

**Guidelines**:
- First line: Brief summary (imperative mood: "Calculate", not "Calculates")
- Args: Parameter name, type in parentheses, description
- Returns: Type and description
- Raises: Only if function explicitly raises exceptions (not incidental)

**Module docstrings**:
```python
"""Search NCBI SRA for bacterial WGS data.

This script queries the NCBI Sequence Read Archive for whole genome
sequencing data matching specific organisms and criteria.

Usage:
    python search_sra.py --organism "Listeria monocytogenes" --output results.json
"""
```

**When to skip docstrings**:
- Test functions (test name is self-documenting)
- Very simple one-liners: `def is_paired(layout): return layout == "PAIRED"`
- Private helpers that are obvious from name and context

---

## Comments

### Inline Comments

**Use for**:
- Non-obvious logic
- Workarounds for bugs or limitations
- Complex regex or algorithms
- Business logic that needs explanation

**Examples**:
```python
✅ Good
# Sleep 0.4s to respect NCBI rate limit (3 req/s without API key)
time.sleep(0.4)

# Extract accession from Run XML: <Run acc="SRR123" .../>
accession = run_xml.split('acc="')[1].split('"')[0]

# Default to 5.0 Mb for unknown organisms (conservative estimate)
genome_size_mb = GENOME_SIZES.get(genus, 5.0)

❌ Bad
# Increment i  (obvious from code)
i += 1

# Create DataFrame  (obvious from code)
df = pd.DataFrame(data)
```

**Guidelines**:
- Explain *why*, not *what* (code shows what)
- Place comment on line above code, not inline (unless very short)
- Use full sentences with punctuation
- Keep comments up-to-date with code

### TODO Comments

**Format**: `# TODO(name): Description`

```python
# TODO(zsb3): Add support for single-end reads
# TODO: Consider using multiprocessing for large batch sizes
```

### Source Comments

**For constants from external sources**:
```python
GENOME_SIZES = {
    "Salmonella": 4.8,  # Source: NCBI RefSeq NZ_CP014051.1
    "Escherichia": 5.0, # Source: NCBI RefSeq NC_000913.3 (E. coli K-12)
}
```

---

## Data Structures

### Dictionary Keys

**Style**: `snake_case` strings, descriptive

**Examples**:
```python
✅ Good
result = {
    "organism": "Listeria monocytogenes",
    "total_count": 1500,
    "retrieved_count": 1500,
}

❌ Bad
result = {
    "org": "Listeria",      # Unclear abbreviation
    "totalCount": 1500,     # camelCase
    "retrievedcount": 1500, # No separator
}
```

### DataFrame Column Names

**Style**: `PascalCase` for compatibility with NCBI/CSV conventions

**Examples**:
```python
# Input from NCBI (preserve original naming)
df["Accession"]
df["ScientificName"]
df["LibraryLayout"]

# Computed columns (match existing style)
df["Estimated_Coverage"]  # Matches: Total_Bases, Library_Layout
```

**Rationale**: NCBI uses PascalCase in their APIs and CSV outputs. We preserve this for consistency and to avoid column renaming overhead.

---

## Error Handling

### Print and Exit Pattern

**For CLI scripts** (current pattern):
```python
if not Path(input_file).exists():
    print(f"Error: File not found: {input_file}")
    sys.exit(1)

if filtered_df.empty:
    print("Warning: No results match the specified criteria.")
    sys.exit(0)
```

**Guidelines**:
- Use `print()` for user-facing messages (these are CLI tools)
- `sys.exit(1)` for errors (non-zero exit code)
- `sys.exit(0)` for graceful exits with warnings
- Prefix errors with "Error:", warnings with "Warning:"

### Don't use bare except

```python
❌ Bad
try:
    data = json.load(f)
except:  # Too broad, hides bugs
    print("Failed to load JSON")

✅ Good
try:
    data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in {filepath}: {e}")
    sys.exit(1)
```

---

## Testing Conventions

### Test Function Naming

**Pattern**: `test_<function_name>_<scenario>`

```python
def test_calculate_coverage_valid_genus():
def test_calculate_coverage_unknown_genus():
def test_calculate_coverage_zero_bases():
def test_build_query_with_date_range():
def test_build_query_without_date_range():
```

**Guidelines**:
- Start with `test_` (pytest requirement)
- Mirror function being tested
- Describe scenario in positive terms
- Use underscores, not hyphens

### Test Organization

**Pattern**: Group related tests in classes

```python
class TestCalculateCoverage:
    def test_valid_genus(self):
    def test_unknown_genus(self):
    def test_zero_bases(self):

class TestBuildQuery:
    def test_with_date_range(self):
    def test_without_date_range(self):
```

**Guidelines**:
- Class name: `Test<FunctionName>` in PascalCase
- One class per function being tested
- Helps organize test output and allows shared fixtures

### Mock Naming

```python
✅ Good
@patch("scripts.search_sra.Entrez.esearch")
def test_search_sra(mock_esearch):

@patch("builtins.open", new_callable=mock_open, read_data="test data")
def test_read_file(mock_file):

❌ Bad
@patch("scripts.search_sra.Entrez.esearch")
def test_search_sra(m):  # Unclear

@patch("builtins.open")
def test_read_file(mocked_open_function):  # Too verbose
```

**Pattern**: `mock_<thing_being_mocked>`

---

## File Paths

### Use pathlib for new code

```python
✅ Good (pathlib)
from pathlib import Path

file_path = Path("data/results.json")
if file_path.exists():
    data = file_path.read_text()

❌ Acceptable but discouraged (os.path)
import os

file_path = "data/results.json"
if os.path.exists(file_path):
    with open(file_path) as f:
        data = f.read()
```

**Exception**: When passing paths to external libraries that expect strings, convert with `str(path)`.

---

## Boolean Expressions

### Explicit comparisons for clarity

```python
✅ Good
if count > 0:
if results is not None:
if df.empty:  # pandas convention

❌ Acceptable but less clear
if count:
if results:
```

**Exception**: Checking for truthiness of collections is Pythonic:
```python
if items:  # List is not empty
if not items:  # List is empty
```

---

## String Formatting

### Prefer f-strings (Python 3.6+)

```python
✅ Good
message = f"Found {count} results for {organism}"
query = f'"{organism}"[Organism] AND "wgs"[Strategy]'

❌ Old style
message = "Found {} results for {}".format(count, organism)
message = "Found %d results for %s" % (count, organism)
```

**Exception**: For logging templates that are reused, `.format()` is acceptable.

---

## Line Length

### Black enforces 100 characters, but break logically before limit

```python
✅ Good (readable breaks)
filtered_df = df[
    (df["Estimated_Coverage"] >= min_coverage)
    & (df["Estimated_Coverage"] <= max_coverage)
]

❌ Technically valid but harder to read
filtered_df = df[(df["Estimated_Coverage"] >= min_coverage) & (df["Estimated_Coverage"] <= max_coverage)]
```

**Guidelines**:
- Break after operators when possible
- Align wrapped lines for readability
- Use implied line continuation (inside brackets) over backslashes

---

## Summary

These conventions prioritize:
- **Readability**: Code is read more than written
- **Consistency**: Similar problems solved similarly
- **Pythonic style**: Follow community norms
- **Self-documentation**: Names and structure reveal intent

When in doubt:
1. Check existing code for patterns
2. Consult PEP 8
3. Let black and flake8 guide you
4. Optimize for the next person reading your code
