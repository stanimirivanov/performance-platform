## k6 Performance Tests

### Structure

```text
tests/k6/
├── Dockerfile              # Test runner Docker image
├── lib/                    # Shared libraries
│ ├── config.js                 # Configuration utilities
│ ├── http.js                   # HTTP helper functions
│ ├── metrics.js                # Custom metric definitions
│ ├── checks.js                 # Validation checks
│ ├── data-generators.js        # Random data generators
│ ├── session.js                # Session management
│ └── retry.js                  # Retry logic
├── workloads/              # Workload profiles
│ ├── smoke/                    # Quick validation (2 min)
│ ├── average/                  # Production load simulation
│ ├── regression/               # Standard regression (15 min)
│ ├── stress/                   # High load stress (10 min)
│ └── capacity/                 # Maximum capacity (30 min)
└── tests/                  # Test scenarios
├── checkout/                   # Checkout flow tests
├── search/                     # Search functionality tests
└── account/                    # Account management tests


```

### Running Tests

```bash
# Run checkout smoke test
k6 run --config workloads/smoke/checkout.json tests/checkout/scenario.js

# Run via package scripts
pnpm smoke:checkout

# Run all smoke tests
pnpm smoke

# Run with environment variables
BASE_URL=http://test.example.com AUTH_TOKEN=xyz \
    k6 run --config workloads/smoke/checkout.json tests/checkout/scenario.js
```

### Docker

```bash
# Build the image
pnpm docker:build

# Run with volume mount (recommended for development)
docker run --rm \
 -v $(pwd):/tests \
 perfeng-k6-tests \
 run --config workloads/smoke/checkout.json tests/checkout/scenario.js

# Run without volume mount (uses image contents)
docker run --rm \
 perfeng-k6-tests \
 run --config workloads/regression/checkout.json tests/checkout/scenario.js
```

### Environment Variables

| Variable      | Default                 | Description           |
| ------------- | ----------------------- | --------------------- |
| `BASE_URL`    | `http://localhost:8080` | Base URL of SUT       |
| `API_VERSION` | `v1`                    | API version prefix    |
| `AUTH_TOKEN`  | _(empty)_               | Bearer token          |
| `TIMEOUT`     | `30000`                 | Request timeout in ms |

### Custom Metrics

| Metric                        | Type    | Description                   |
| ----------------------------- | ------- | ----------------------------- |
| `biz_checkout_duration`       | Trend   | Checkout transaction duration |
| `biz_search_duration`         | Trend   | Search transaction duration   |
| `biz_successful_transactions` | Counter | Successful transaction count  |
| `biz_failed_transactions`     | Counter | Failed transaction count      |
| `biz_transaction_error_rate`  | Rate    | Transaction error rate        |
| `perf_ttfb`                   | Trend   | Time to first byte            |
| `perf_ttc`                    | Trend   | Time to complete              |
| `perf_active_vus`             | Gauge   | Active virtual users          |

## Nx
```bash
# Show all projects
pnpm nx show projects

# Show project details
pnpm nx show project k6-tests
pnpm nx show project tests-playwright

# Run specific target
pnpm nx run k6-tests:smoke
pnpm nx run tests-playwright:e2e

# Run multiple projects
pnpm nx run-many --target=test

# Show dependency graph
pnpm nx graph

# Generate new project
pnpm nx g @nx/js:lib my-lib

# Run affected projects only
pnpm nx affected --target=test

# Format all projects
pnpm nx format:write

# Lint all projects
pnpm nx run-many --target=lint
```