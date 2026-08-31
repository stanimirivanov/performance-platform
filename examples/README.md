# examples/README.md

## Metadata Examples

This directory contains examples of metadata structures used by PerfEng.

### Data Examples (`metadata/`)

- `run-metadata-example.json` - Example of complete run metadata
- `test-result-example.json` - Example of test results
- `normalized-result-example.json` - Normalized test result format

These are reference JSON structures showing the expected data format.

### Code Examples (`platform/examples`)

- `metadata_collection_demo.py` - Demonstration of the metadata collector

Run the demo:

```bash
cd platform
uv run python examples/metadata_collection_demo.py
```

## Integration Examples

For integration with k6, see the `k6/` directory for sample outputs.

### Summary of Changes

1. **Moved code example** from `examples/` to `examples/usage/collect_metadata_demo.py`
2. **Kept data examples** in `examples/metadata/` - these are documentation/reference
3. **Clear separation** between data examples and code examples
4. **Added README** explaining the purpose of each directory
5. **Three demo functions**:
   - `collect_metadata_demo()` - Shows full run metadata structure
   - `demo_collect_from_environment()` - Shows actual environment collection
   - `demo_compare_environments()` - Shows environment comparison

The example JSON files in `examples/metadata/` are **reference data** showing what the final output should look like, while the code in `examples/usage/` shows **how to generate** that data using the collector.
