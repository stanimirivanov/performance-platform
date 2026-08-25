# Workload Profiles

## Overview

Workload profiles define the load characteristics for performance tests. Each profile represents a different testing purpose and is stored as JSON configuration files compatible with k6's `--config` flag.

## Profile Types

| Profile    | Duration | Purpose                         | Typical Use Case         |
| ---------- | -------- | ------------------------------- | ------------------------ |
| smoke      | 2 min    | Verify basic functionality      | PR validation            |
| average    | 9 min    | Simulate production load        | Daily baseline           |
| regression | 15 min   | Detect performance regressions  | Nightly suite            |
| stress     | 10 min   | Test extreme load               | Breaking point discovery |
| capacity   | 30 min   | Find max sustainable throughput | Capacity planning        |

## Directory Structure

```text
workloads/
├── registry.json       # Profile metadata and test scenario mappings
├── smoke/
│ ├── checkout.json     # Checkout smoke test
│ ├── search.json       # Search smoke test
│ └── account.json      # Account smoke test
├── average/
│ ├── checkout.json
│ ├── search.json
│ └── account.json
├── regression/
│ ├── checkout.json
│ ├── search.json
│ └── account.json
├── stress/
│ ├── checkout.json
│ └── search.json
└── capacity/
└── checkout.json
```

## Profile Configuration

Each profile JSON file contains:

### Scenarios

```json
"scenarios": {
  "scenario_name": {
    "executor": "ramping-arrival-rate",
    "startRate": 10,
    "timeUnit": "1s",
    "preAllocatedVUs": 20,
    "maxVUs": 100,
    "stages": [...]
  }
}
```

### Thresholds

```json
"thresholds": {
"biz_checkout_duration": ["p(95)<400"],
"http_req_failed": ["rate<0.005"]
}
```

Executor Types

| Executor                | Description                          | Use Case                |
| ----------------------- | ------------------------------------ | ----------------------- |
| `ramping-arrival-rate`  | Open model with varying arrival rate | HTTP APIs               |
| `constant-arrival-rate` | Open model with constant rate        | Steady-state testing    |
| `ramping-vus`           | Closed model with varying VUs        | Session-based workflows |

### Selection

Profiles are selected via the --config flag:

```bash
k6 run --config workloads/smoke/checkout.json tests/checkout/scenario.js
```

Or via `package.json` scripts:

```bash
pnpm smoke:checkout
pnpm regression:checkout
pnpm stress:checkout
```

### Adding New Profiles

1. Create a new directory under `workloads/` if needed
2. Create JSON files for each test scenario
3. Update `registry.json` with profile metadata
4. Add package.json scripts for convenience
