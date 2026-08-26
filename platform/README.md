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
# By Group

# Metadata only
pytest tests/metadata/ -v

# Normalization only
pytest tests/normalization/ -v

# Core only
pytest tests/core/ -v

# Integration only
pytest tests/integration/ -v
```

`````bash
# By Marker

# All unit tests
pytest tests/ -m unit -v

# All integration tests
pytest tests/ -m integration -v

# Metadata unit tests only
pytest tests/ -m "metadata and unit" -v

# Fast tests (excludes integration, slow, kubectl)
pytest tests/ -m "not integration and not slow and not requires_kubectl" -v
```


```bash
# With Coverage
# All tests with coverage
pytest tests/ --cov=perfeng --cov-report=html --cov-report=term

# Metadata only with coverage
pytest tests/metadata/ --cov=perfeng.metadata --cov-report=term
```

**Test Coverage Requirements**

- Minimum coverage: 80%
- Critical paths (collector, normalizer): 90%
- Generated code (environment.py): Excluded from coverage

**Writing New Tests**

1. Place tests in the appropriate group directory
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

2. Add the group marker at the module level:

````python
import pytest
pytestmark = pytest.mark.metadata # or .normalization, .core, .integration
```

3. Mark individual tests with additional markers:

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
`````

**Test Groups**

| Group         | Path                   | Marker                       | Description                                |
| ------------- | ---------------------- | ---------------------------- | ------------------------------------------ |
| Metadata      | `tests/metadata/`      | `@pytest.mark.metadata`      | Metadata collection, environment detection |
| Normalization | `tests/normalization/` | `@pytest.mark.normalization` | Data normalization (k6, etc.)              |
| Core          | `tests/core/`          | `@pytest.mark.core`          | Core utilities (run ID, validation)        |
| Integration   | `tests/integration/`   | `@pytest.mark.integration`   | End-to-end tests                           |

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

Tests run automatically on:

- Pull requests
- Pushes to main branch
- Release tags

Required checks:

- All tests pass
- Coverage meets minimum
- No regressions in critical paths

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
