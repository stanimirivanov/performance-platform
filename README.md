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

### Development Setup

```bash
# Install Python dependencies
cd platform
uv sync
cd ..

# Install JavaScript dependencies
pnpm install

# Set up pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run k6 smoke test
make k6-smoke

# Run all tests
make test
```

### Nx Commands

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
