# Architecture Decision Records

This document captures key technical decisions made in the SRA Accession Search project, explaining the rationale, alternatives considered, and consequences.

---

## ADR-001: Use pytest over unittest

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Needed to choose a testing framework for Python code

### Decision
Use pytest as the testing framework instead of unittest.

### Rationale
- **Fixtures**: pytest's fixture system is more flexible than unittest's setUp/tearDown
  - Can inject fixtures selectively into test functions
  - Fixtures can depend on other fixtures
  - Scope control (function, class, module, session)
- **Parametrization**: `@pytest.mark.parametrize` makes testing multiple inputs cleaner
  - Reduces code duplication
  - Each parameter gets its own test result
- **Assertions**: Simple `assert` statements vs unittest's `self.assertEqual`, `self.assertTrue`, etc.
  - More Pythonic and readable
  - Better assertion introspection in failures
- **Plugins**: Rich ecosystem (pytest-cov, pytest-mock, pytest-xdist)
- **Discovery**: Automatic test discovery without inheritance

### Alternatives Considered
1. **unittest** (standard library)
   - Pros: No dependencies, familiar to many
   - Cons: More verbose, weaker fixtures, class-based boilerplate
2. **nose/nose2**
   - Pros: Compatible with unittest
   - Cons: Less actively maintained than pytest

### Consequences
- **Positive**:
  - Tests are more concise and readable
  - Easy coverage integration with pytest-cov
  - Powerful mocking with pytest-mock
  - Better parametrized testing reduces duplication
- **Negative**:
  - External dependency (not stdlib)
  - Learning curve for unittest-experienced developers
- **Neutral**:
  - Need to install pytest in CI/CD environments

---

## ADR-002: Use black for code formatting

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Need consistent code style across project

### Decision
Use black as the automatic code formatter with 100-character line length.

### Rationale
- **Deterministic**: No debates about style—black's decisions are final
  - Removes bikeshedding in code reviews
  - Consistent style across all contributors
- **Automated**: Can be run as pre-commit hook or CI check
- **Community adoption**: De facto standard in Python community
- **100-char lines**: Balances readability with screen real estate
  - Black default is 88, but 100 is also widely used
  - Aligns with flake8 config

### Alternatives Considered
1. **Manual PEP 8 compliance**
   - Pros: No dependencies
   - Cons: Inconsistent, time-consuming, subjective
2. **autopep8**
   - Pros: Only fixes PEP 8 violations
   - Cons: Less opinionated, more configuration needed
3. **yapf**
   - Pros: Highly configurable
   - Cons: Configuration complexity, not as widely adopted

### Consequences
- **Positive**:
  - Zero style discussions in PRs
  - Automatic consistency
  - Easy to integrate with pre-commit
- **Negative**:
  - Some developers dislike black's specific choices (e.g., string quotes)
  - 100-char limit occasionally forces awkward line breaks
- **Neutral**:
  - Need to configure editor integrations
  - Need flake8 compatibility rules (E203, W503)

---

## ADR-003: Use flake8 for linting

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Need static analysis to catch common errors

### Decision
Use flake8 for linting with 100-character line limit and black-compatibility rules.

### Rationale
- **Comprehensive**: Combines PyFlakes, pycodestyle, and McCabe complexity checker
- **Fast**: Runs quickly even on larger codebases
- **Configurable**: Easy to ignore specific rules via .flake8
- **CI-friendly**: Simple to integrate into GitHub Actions
- **Black compatibility**: Can coexist with black by ignoring E203, W503

### Alternatives Considered
1. **pylint**
   - Pros: More extensive checks, complexity metrics
   - Cons: Slower, more opinionated, noisy default config
2. **pycodestyle** (formerly pep8)
   - Pros: Lightweight, focused on PEP 8
   - Cons: Doesn't catch logic errors like PyFlakes does
3. **ruff**
   - Pros: Extremely fast (Rust-based), combines multiple tools
   - Cons: Newer, less mature (though gaining adoption)

### Consequences
- **Positive**:
  - Catches common errors before runtime
  - Fast enough for pre-commit hooks
  - Well-established tool chain
  - Good balance of strictness and practicality
- **Negative**:
  - Some rules need to be ignored for black compatibility
  - Doesn't catch type errors (would need mypy for that)
- **Neutral**:
  - Requires .flake8 configuration file

---

## ADR-004: Store genome sizes as hardcoded dictionary

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Need genome size data for coverage calculations

### Decision
Store genome sizes in a `GENOME_SIZES` dictionary in `filter_metadata.py`, with values sourced from NCBI genome assemblies.

### Rationale
- **Simplicity**: No external file to manage or parse
- **Version control**: Changes to genome sizes are tracked in git
- **Performance**: Instant lookup, no file I/O
- **Self-documenting**: Values include source comments
- **Testability**: Easy to mock or override in tests
- **Stability**: Genome sizes don't change frequently

### Alternatives Considered
1. **External JSON/YAML file**
   - Pros: Non-developers could edit, separation of data/code
   - Cons: Extra file to manage, parsing overhead, deployment complexity
2. **Database lookup**
   - Pros: Could support many organisms
   - Cons: Overkill for ~10 organisms, adds dependency
3. **NCBI API call per organism**
   - Pros: Always up-to-date
   - Cons: Network dependency, rate limits, slow, overcomplicated
4. **User-provided parameter**
   - Pros: Maximum flexibility
   - Cons: Requires user to research genome size, error-prone

### Consequences
- **Positive**:
  - Fast and reliable
  - No external dependencies for genome size data
  - Easy to add new organisms (edit Python file, add test)
  - Clear source attribution in comments
- **Negative**:
  - Code change required to add organisms (not just config)
  - Could become unwieldy if supporting 100+ organisms
- **Neutral**:
  - Genome size updates require version bump and release

### Future Considerations
If we need to support 50+ organisms, consider moving to JSON config file.

---

## ADR-005: Enforce 100% code coverage

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Define acceptable test coverage threshold

### Decision
Require 100% code coverage, enforced in CI/CD pipeline.

### Rationale
- **Quality assurance**: Every line of code is tested
- **Prevents regressions**: New code must include tests
- **Confidence**: Safe to refactor with full test coverage
- **Small codebase**: Achievable for ~400 lines of code
- **Best practices**: Encourages thinking about edge cases

### Alternatives Considered
1. **80-90% coverage**
   - Pros: More flexible, allows "obvious" code to be untested
   - Cons: Arbitrary threshold, edge cases may be missed
2. **No coverage requirement**
   - Pros: Maximum flexibility
   - Cons: Code quality can degrade over time
3. **Mutation testing**
   - Pros: Tests quality of tests, not just coverage
   - Cons: Slow, complex, overkill for this project size

### Consequences
- **Positive**:
  - Very high confidence in code correctness
  - Easy to refactor without fear
  - Documentation via tests (every code path has example)
- **Negative**:
  - Can't merge without 100% coverage (could block urgent fixes)
  - Some trivial code requires boilerplate tests
  - Tests can become coupled to implementation
- **Neutral**:
  - CI builds fail if coverage drops

### Escape Hatch
For truly untestable code (rare), use `# pragma: no cover` with justification comment.

---

## ADR-006: Use two-step pipeline (search then filter)

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Architecture for querying and filtering SRA data

### Decision
Implement as two separate CLI scripts:
1. `search_sra.py` - Query NCBI and save raw metadata
2. `filter_metadata.py` - Filter and rank results

### Rationale
- **Separation of concerns**: Search and filter are distinct operations
- **Intermediate inspection**: Users can examine raw results before filtering
- **Reusability**: Can filter same search results with different parameters
- **Rate limiting**: Don't re-query NCBI when adjusting filters
- **Testing**: Easier to test search and filter logic independently
- **Caching**: JSON output serves as cache of NCBI API response

### Alternatives Considered
1. **Single combined script**
   - Pros: Simpler for end users (one command)
   - Cons: Can't inspect intermediate results, must re-query to change filters
2. **Library with CLI wrapper**
   - Pros: Reusable as Python package
   - Cons: Overkill for current use case, more complex
3. **Nextflow/Snakemake pipeline**
   - Pros: Workflow orchestration, parallelization
   - Cons: Heavy dependency, unnecessary complexity

### Consequences
- **Positive**:
  - Can experiment with different filters without re-querying NCBI
  - Intermediate JSON is useful for debugging and auditing
  - Each script is simpler and easier to test
  - Respects NCBI rate limits
- **Negative**:
  - Users must run two commands instead of one
  - JSON intermediate file takes disk space
- **Neutral**:
  - Could add convenience script to run both steps if needed

---

## ADR-007: Default to 50-250x coverage range

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Choose default coverage filter thresholds

### Decision
Default coverage range: 50x minimum, 250x maximum

### Rationale
- **50x minimum**: Adequate for high-quality assembly
  - Most assemblers recommend 50-100x for bacterial genomes
  - Below 50x: Assembly quality degrades significantly
- **250x maximum**: Diminishing returns, potential issues
  - Excessive coverage can slow assembly and increase errors
  - SPAdes/SKESA perform well up to ~200x
  - Very high coverage may indicate contamination or poor library prep
- **Practical range**: Balances quality and quantity of results
  - Too strict (e.g., 80-120x): May exclude many usable datasets
  - Too loose (e.g., 20-500x): Includes poor quality or problematic data

### Alternatives Considered
1. **30-150x**
   - Pros: More permissive, more results
   - Cons: 30x is borderline for quality assemblies
2. **80-200x**
   - Pros: Optimal for most assemblers
   - Cons: May exclude usable datasets, overly restrictive
3. **No default** (user always specifies)
   - Pros: Forces user to think about requirements
   - Cons: Inconvenient, requires user expertise

### Consequences
- **Positive**:
  - Reasonable defaults for most use cases
  - Filters out poor quality data (too low coverage)
  - Filters out potential problem datasets (too high coverage)
  - Users can override via CLI arguments
- **Negative**:
  - May exclude edge cases that could be useful
  - Defaults are somewhat arbitrary (based on experience)
- **Neutral**:
  - Can adjust based on user feedback

### Data Source
Based on:
- SPAdes documentation (recommended 20-150x)
- SKESA documentation (optimal 50-150x)
- CDC internal best practices
- Literature on WGS assembly quality

---

## ADR-008: Output JSON for search, CSV for filter

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Choose output formats for each script

### Decision
- `search_sra.py` outputs JSON (structured metadata)
- `filter_metadata.py` outputs CSV (tabular results)

### Rationale
- **JSON for search**:
  - Preserves full structure of NCBI API responses
  - Easy to parse in Python (json.load)
  - Human-readable but machine-friendly
  - Can include nested data (Runs XML, ExpXml)
- **CSV for filter**:
  - Standard format for spreadsheets (Excel, Google Sheets)
  - Easy to import into R, pandas, other tools
  - Flat structure suitable for filtered results
  - Widely compatible

### Alternatives Considered
1. **CSV for both**
   - Pros: Consistency
   - Cons: Loses nested structure from NCBI API, harder to parse XML in CSV
2. **JSON for both**
   - Pros: Consistency, programmatic access
   - Cons: Less convenient for manual inspection in spreadsheets
3. **SQLite database**
   - Pros: Queryable, relational
   - Cons: Overkill, binary format, less portable
4. **Parquet**
   - Pros: Efficient, typed columns
   - Cons: Not human-readable, requires pandas

### Consequences
- **Positive**:
  - JSON preserves full API response for future processing
  - CSV is immediately usable in Excel or other tools
  - Each format is well-suited to its use case
- **Negative**:
  - Inconsistent output formats between scripts
  - JSON → CSV conversion loses some detail
- **Neutral**:
  - Users comfortable with both formats in bioinformatics

---

## ADR-009: Use conditional git configuration for token scoping

**Date**: 2024-12  
**Status**: Accepted  
**Context**: Need different GitHub token permissions for personal vs org repos

### Decision
Use git's `includeIf` directives to apply different credentials based on repository path:
- Personal repos: Workflow-scoped token (can modify .github/workflows/)
- CDC org repos: Standard token (no workflow scope)

### Rationale
- **Security**: Prevents accidental workflow modifications in org repos
- **Principle of least privilege**: Each repo gets minimum needed permissions
- **Automation**: Automatic based on directory, no manual switching
- **Transparent**: Git handles it, no script wrappers needed

### Alternatives Considered
1. **Single token with workflow scope everywhere**
   - Pros: Simple, one credential
   - Cons: Security risk in org repos, violates least privilege
2. **Manual token switching**
   - Pros: Full control
   - Cons: Error-prone, easy to forget, inconvenient
3. **SSH keys instead of HTTPS**
   - Pros: No token scoping issues
   - Cons: Doesn't solve different permission needs, more complex setup
4. **Git credential helpers per remote**
   - Pros: Fine-grained control
   - Cons: Complex configuration, must specify remote explicitly

### Consequences
- **Positive**:
  - Right permissions automatically per repo context
  - No risk of accidentally modifying org workflows
  - Transparent to user after setup
- **Negative**:
  - Requires careful .gitconfig setup
  - Must remember directory structure matters
- **Neutral**:
  - Two tokens to manage instead of one

---

## Summary

These decisions reflect the project's priorities:
- **Quality**: 100% coverage, linting, formatting
- **Simplicity**: Minimal dependencies, straightforward architecture
- **Usability**: Reasonable defaults, standard formats, good documentation
- **Maintainability**: Clear code, comprehensive tests, documented decisions

Future decisions should align with these principles.
