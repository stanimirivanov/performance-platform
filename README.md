# Continuous Performance Engineering Platform

A platform for automated performance validation, regression detection, and 
continuous performance engineering.

For more background, read the AI assisted research:

- [Continuous Performance Engineering - Research](docs/research.md)
- [Continuous Performance Engineering - Platform Proposal](docs/project-proposal.md)

We are going to implement a proof of concept of the above research.

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
