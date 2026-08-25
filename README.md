# Continuous Performance Engineering Platform

A production-grade platform for automated performance validation, regression
detection, and continuous performance engineering.

For more background, read the AI assisted research:

- [Continuous Performance Engineering - Research](docs/research.md)
- [Continuous Performance Engineering - Platform Proposal](docs/project-proposal.md)

We are going to implement a POC of the above research.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm 8+
- k6 (for running load tests)
- Docker (for local Kubernetes)

## Local Development Setup

### Prerequisites

- Docker Desktop
- kind
- kubectl
- Helm 3+

### Quick Start

```bash
# 1. Create cluster
make cluster-up

# 2. Install infrastructure
make infra-install

# 3. Install sample SUT
make sut-install

# 4. Run a smoke test
make k6-search-smoke
````

## Documentation

- [Local Setup Guide](docs/local-setup.md)
- [Monitoring Stack](docs/monitoring-stack.md)
- [Architecture](docs/architecture)

## Helm Charts

| Chart           | Location                     | Purpose                   |
|-----------------|------------------------------|---------------------------|
| `perfeng-infra` | `infra/charts/perfeng-infra` | Infrastructure components |
| `sample-sut`    | `infra/charts/sample-sut`    | Test target               |
| `k6-runner`     | `infra/charts/k6-runner`     | k6 test execution         |
