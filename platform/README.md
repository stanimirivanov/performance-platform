# PerfEng Platform

Core orchestration and analysis platform for continuous performance engineering.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .

# Start API server
uv run uvicorn perfeng.api.main:app --reload

# Use CLI
uv run perfeng --help
```

## Testing

```bash
# From the platform directory
cd platform

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/metadata/test_collector.py -v

# Run specific test
pytest tests/metadata/test_collector.py::TestMetadataCollector::test_init_default -v
```

```bash
# Unit tests only (fast)
pytest tests/metadata/ -m "not integration"

# Integration tests only
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"

# Tests that require kubectl
pytest tests/ -m "requires_kubectl"
```

**Test Coverage Requirements**
- Minimum coverage: 80%
- Critical paths: 100% (collector, config loader)

**Writing New Tests**

```python
# platform/tests/metadata/test_new_feature.py
import pytest
from perfeng.metadata.collector import MetadataCollector

class TestNewFeature:
    def test_feature_basic(self, collector):
        """Basic test for new feature."""
        result = collector.do_something()
        assert result is not None
    
    def test_feature_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            MetadataCollector.invalid_operation()
```

**Marking Tests**

```python
@pytest.mark.unit
def test_unit_example():
pass

@pytest.mark.integration
def test_integration_example():
pass

@pytest.mark.slow
def test_slow_example():
pass
```

## Troubleshooting

**Import Errors**

If you see import errors, make sure:

1. The `perfeng` module is in your Python path
2. The generated `environment.py` exists
3. All dependencies are installed

**Mock Issues**

If subprocess mocks aren't working:

```python
@pytest.fixture
def test_db():
    # Use test database
    pass
```

**Test Database**

For tests requiring PostgreSQL:

```python
@pytest.fixture
def test_db():
    # Use test database
    pass
```

**CI/CD Integration**

Tests are automatically run in CI/CD pipeline:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          pytest tests/ --cov=perfeng --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

**Test Data**

Test data is stored in:

- `examples/metadata/` - Example JSON structures
- `tests/data/` - Test-specific data files

Use fixtures for test data:

```python
@pytest.fixture
def sample_run_metadata():
    with open('examples/metadata/run-metadata-example.json') as f:
        return json.load(f)
```
