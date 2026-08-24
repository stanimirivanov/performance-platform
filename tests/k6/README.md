# k6 Performance Tests

## Structure

- `lib/` - Shared libraries (metrics, HTTP helpers, config)
- `checkout/` - Checkout flow tests
- `search/` - Search functionality tests
- `account/` - Account management tests

## Running Tests

```bash
# Run smoke test
k6 run --config ../../workloads/smoke/checkout.yaml checkout/scenario.js

# Run regression test
k6 run --config ../../workloads/regression/checkout.yaml checkout/scenario.js

# Run stress test
k6 run --config ../../workloads/stress/checkout.yaml checkout/scenario.js

# Run with environment variables
BASE_URL=http://test.example.com AUTH_TOKEN=xyz k6 run checkout/scenario.js
```

## Workload Profiles

Workload profiles are stored in `../../workloads/` and include:

- `smoke/` - Quick validation tests
- `regression/` - Standard regression tests
- `stress/` - High load stress tests
- `capacity/` - Maximum capacity tests
- `average/` - Average production load simulation
