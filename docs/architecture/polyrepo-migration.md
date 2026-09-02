# Polyrepo Migration Blueprint

## Purpose and decision

This repository is the proof-of-concept source repository. It is not the
long-term home for every component of the platform. The target is a small
polyrepo system in which each repository has one deployable, consumable, or
operational responsibility.

Do **not** use Git submodules to recreate the current repository structure. Each
repository publishes a versioned artifact. `perfeng-environment` selects the
compatible artifact versions and assembles local, development, and production
environments.

The initial target is seven repositories. `perfeng-ui` and
`perfeng-sut-example` are deliberately deferred until there is a real user
interface or a reusable reference SUT to extract.

```text
contracts ──> control-plane ──> Kubernetes Jobs
     │                │                 │
     │                └──> PostgreSQL   ├──> k6 workloads
     │                                  ├──> Playwright workloads
     └──> analysis <── raw artifacts    └──> Kubernetes benchmarks

environment: deploys and wires every released artifact above
```

## Target repositories

| Repository              | Responsibility                                                                  | Primary technology                     | Produced artifact                                   |
|-------------------------|---------------------------------------------------------------------------------|----------------------------------------|-----------------------------------------------------|
| `perfeng-contracts`     | Language-neutral API, event, and data contracts                                 | JSON Schema, OpenAPI, YAML             | versioned contract release                          |
| `perfeng-control-plane` | Run lifecycle, scheduling, persistence, and Kubernetes integration              | Go, PostgreSQL, Kubernetes client      | container image and OpenAPI client generation input |
| `perfeng-analysis`      | Result normalization, quality checks, SLO evaluation, and regression analysis   | Python                                 | package, CLI, and container image                   |
| `perfeng-k6`            | API and service load-test definitions                                           | JavaScript/TypeScript, k6              | test image or immutable test bundle                 |
| `perfeng-playwright`    | Browser and business-interaction performance tests                              | TypeScript, Playwright                 | test image or immutable test bundle                 |
| `perfeng-k8s`           | Kubernetes/OpenShift benchmark definitions and adapters                         | YAML, scripts, kube-burner ecosystem   | benchmark image or immutable bundle                 |
| `perfeng-environment`   | Developer workspace bootstrap, deployment composition, and GitOps configuration | Helm/Kustomize, YAML, shell/PowerShell | deployable environment configuration                |

### Ownership rules

- `perfeng-contracts` defines shared shapes, not language implementations or
  database tables.
- `perfeng-control-plane` decides *what runs, where, and when*. It does not
  calculate regression statistics or contain workload scripts.
- `perfeng-analysis` decides *what results mean*. It starts as a library and CLI
  executed in a Job, not a permanently running service.
- Workload repositories generate measurements and emit contract-conformant raw
  artifacts. They do not manage baselines or platform state.
- `perfeng-environment` references released versions; it never copies source
  from the other repositories.

## Detailed source-to-target mapping

Paths below are relative to the current `performance-platform` repository.
“Move” means preserve history where practical (`git filter-repo` or
`git subtree split`) and remove the source path only after consumers have
migrated. “Reimplement” is intentional: the existing proof-of-concept is useful
behaviour/specification, but is not transplanted as production code.

| Current path                                                                   | Target repository               | Action                                                                                                                                                    | Notes                                                                                                                                                          |
|--------------------------------------------------------------------------------|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `schemas/`                                                                     | `perfeng-contracts`             | Move                                                                                                                                                      | Reorganize into versioned `schemas/<domain>/v1/` directories.                                                                                                  |
| `examples/metadata/`                                                           | `perfeng-contracts`             | Move                                                                                                                                                      | Keep as contract fixtures and conformance examples.                                                                                                            |
| `docs/architecture/schema-versioning.md`                                       | `perfeng-contracts`             | Move and revise                                                                                                                                           | Replace document-level integer-only policy with versioned contract paths plus SemVer releases.                                                                 |
| `docs/architecture/metric-naming.md`                                           | `perfeng-contracts`             | Move                                                                                                                                                      | It defines a cross-component vocabulary.                                                                                                                       |
| `platform/src/perfeng/utils/validation.py`                                     | `perfeng-contracts`             | Reimplement per consumer                                                                                                                                  | Validation becomes generated or native consumers of published schemas; do not put Python code in contracts.                                                    |
| `platform/src/perfeng/api/`                                                    | `perfeng-control-plane`         | Reimplement                                                                                                                                               | Current FastAPI routes define useful behaviour; publish the API first in `perfeng-contracts/openapi/`, then implement it in Go.                                |
| `platform/src/perfeng/orchestrator/`                                           | `perfeng-control-plane`         | Move/reimplement                                                                                                                                          | Expand into the explicit run-state machine, scheduling, timeout, cancellation, and Job-dispatch boundary.                                                      |
| `platform/src/perfeng/storage/`                                                | `perfeng-control-plane`         | Reimplement                                                                                                                                               | Control plane owns PostgreSQL persistence, migrations, artifact references, and audit data.                                                                    |
| `platform/db/`                                                                 | `perfeng-control-plane`         | Move/rewrite                                                                                                                                              | Retain migration intent and data model; replace Python-specific model generation with Go migration tooling.                                                    |
| `platform/src/perfeng/metadata/`                                               | `perfeng-control-plane`         | Split                                                                                                                                                     | Kubernetes/environment collection moves to the control-plane infrastructure adapter. Shared serializable metadata shapes move to contracts.                    |
| `platform/src/perfeng/core/config.py`                                          | `perfeng-control-plane`         | Reimplement                                                                                                                                               | Runtime configuration belongs with the service.                                                                                                                |
| `platform/src/perfeng/cli.py`                                                  | `perfeng-control-plane`         | Split                                                                                                                                                     | Run-management commands become Go CLI/API client commands; analysis commands belong in `perfeng-analysis`.                                                     |
| `platform/tests/storage/`, `platform/tests/integration/test_storage_api.py`    | `perfeng-control-plane`         | Reimplement                                                                                                                                               | Preserve test cases as behavioural acceptance tests while changing implementation language.                                                                    |
| `platform/tests/metadata/`                                                     | `perfeng-control-plane`         | Split                                                                                                                                                     | Collection tests move here; contract fixture tests move to contracts.                                                                                          |
| `platform/src/perfeng/normalizer/`                                             | `perfeng-analysis`              | Move                                                                                                                                                      | k6 normalization is analysis, not orchestration.                                                                                                               |
| `platform/src/perfeng/quality/`                                                | `perfeng-analysis`              | Move                                                                                                                                                      | Implement measurement trustworthiness separately from SLO/regression outcomes.                                                                                 |
| `platform/src/perfeng/policy/`                                                 | `perfeng-analysis`              | Move                                                                                                                                                      | SLO and regression-policy evaluation belongs with interpretation. Policy document shapes remain contracts.                                                     |
| `platform/src/perfeng/reporting/`                                              | `perfeng-analysis`              | Move                                                                                                                                                      | Produce machine-readable analysis results first; presentation integrations can evolve later.                                                                   |
| `platform/tests/normalization/`                                                | `perfeng-analysis`              | Move                                                                                                                                                      | Retain as normalizer conformance tests.                                                                                                                        |
| `policies/slo/`, `policies/regression/`                                        | `perfeng-analysis`              | Move                                                                                                                                                      | Treat them as versioned example/default policies, not control-plane configuration.                                                                             |
| `examples/k6/sample-k6-output.json`                                            | `perfeng-analysis`              | Move                                                                                                                                                      | A raw-result fixture for the k6 normalizer; copy a minimal contract example to contracts if useful.                                                            |
| `tests/k6/`                                                                    | `perfeng-k6`                    | Move                                                                                                                                                      | Includes scenario code, workload profiles, catalogue, registry, Dockerfile, package metadata, and README.                                                      |
| `infra/charts/k6-runner/`                                                      | `perfeng-environment`           | Move initially                                                                                                                                            | This is deployment composition. Later the control plane creates Jobs directly, so the chart should become a compatibility/developer-runner tool or be retired. |
| `tests/playwright/`                                                            | `perfeng-playwright`            | Move                                                                                                                                                      | Includes generated Nx scaffolding; simplify the repository layout during extraction and replace `example.spec.ts` with a real contract-emitting test.          |
| Kubernetes/OpenShift benchmark definitions (none yet)                          | `perfeng-k8s`                   | Create empty repository                                                                                                                                   | Do not place application k6 or browser tests here. Add kube-burner adapters only when benchmark work begins.                                                   |
| `infra/charts/perfeng-infra/`                                                  | `perfeng-environment`           | Move                                                                                                                                                      | Observability, storage, namespaces, RBAC, quotas, and network policies are environment composition.                                                            |
| `infra/local/`                                                                 | `perfeng-environment`           | Move                                                                                                                                                      | Keep Windows and shell variants for local cluster lifecycle.                                                                                                   |
| `infra/charts/sample-sut/`                                                     | `perfeng-environment` initially | Move, then extract later                                                                                                                                  | It supports local integration. Extract to `perfeng-sut-example` only when it becomes a maintained, reusable SUT.                                               |
| root `Makefile`                                                                | `perfeng-environment`           | Replace                                                                                                                                                   | Becomes the developer entry point: bootstrap, cluster up/down, build, deploy, test, analyze, and report.                                                       |
| `docker-compose.metadata.yaml`                                                 | `perfeng-environment`           | Move                                                                                                                                                      | Local-only composition. Rename after the control-plane/database responsibility is clear.                                                                       |
| root `package.json`, `pnpm-workspace.yaml`, `nx.json`, root TypeScript configs | Split then retire               | k6 and Playwright own their Node tooling. Environment owns only tooling it actually needs.                                                                |
| root `README.md`, `docs/local-setup.md`, `docs/monitoring-stack.md`            | `perfeng-environment`           | Move/rewrite                                                                                                                                              | The workspace and operations documentation belongs with the environment.                                                                                       |
| `docs/research.md`, `docs/project-proposal.md`                                 | Keep temporarily                | These are programme/design records. Copy targeted operational content into the owning repositories; archive the originals once the migration is complete. |
| root CI/editor configuration, license                                          | Copy to each repository         | Establish a shared organization template; do not make one repository the source of truth by accident.                                                     |

## Required repository starting layouts

### `perfeng-contracts`

```text
openapi/control-plane/v1/openapi.yaml
schemas/run/v1/
schemas/result/v1/
schemas/environment/v1/
schemas/policy/v1/
events/v1/
examples/
docs/compatibility.md
```

Publish a release only after compatibility validation. Consumers pin a SemVer
release. A breaking wire-format change creates a new contract major/path (for
example `result/v2`) rather than silently changing `result/v1`.

### `perfeng-control-plane`

```text
cmd/perfeng-control-plane/
cmd/perfengctl/
internal/domain/
internal/application/
internal/adapters/kubernetes/
internal/adapters/postgres/
internal/adapters/objectstore/
migrations/
deploy/
```

The first implementation may launch Kubernetes Jobs through the Kubernetes API.
A `PerformanceRun` CRD/operator is an explicitly later evolution, not a
prerequisite for the extraction.

### `perfeng-analysis`

```text
src/perfeng_analysis/normalization/
src/perfeng_analysis/quality/
src/perfeng_analysis/requirements/
src/perfeng_analysis/comparison/
src/perfeng_analysis/regression/
src/perfeng_analysis/historical/
tests/
```

Requirement evaluation, regression detection, and measurement quality must
remain separate outputs. A result may be SLO-pass yet a regression, or be
inconclusive because the measurement is invalid.

### Workload repositories

`perfeng-k6` owns `scenarios/`, `workloads/`, `lib/`, and a test catalogue.
`perfeng-playwright` owns business-latency measurements, fixtures, and browser
test utilities. `perfeng-k8s` owns workload definitions and adapters for cluster
benchmarks. Each publishes raw artifacts that identify the test, workload, tool
version, and contract version.

### `perfeng-environment`

```text
repositories.yaml
environments/local/
environments/dev/
environments/staging/
environments/production/
charts/
scripts/bootstrap/
scripts/validate/
docs/
Makefile
```

`repositories.yaml` is a developer convenience manifest for cloning checked out
sources beside each other. Deployment references are immutable image, chart, or
bundle versions—not local filesystem paths and not Git submodules.

## Extraction sequence and exit criteria

1. **Freeze the boundaries.** Adopt this blueprint, name repository owners, and
   create an artifact registry and CI template. No production code moves yet.
2. **Create `perfeng-contracts` first.** Move the four schemas, examples, and
   shared vocabulary. Publish `v1.0.0`. Add validation that every example is
   valid and compatibility checks for future changes.
3. **Extract `perfeng-k6` and `perfeng-playwright`.** Their current source trees
   are already distinct. Build and publish a pinned test image/bundle from each.
   Ensure outputs include the contracts release they conform to.
4. **Create `perfeng-analysis`.** Move the normalizer and its tests first. Add a
   CLI that transforms a k6 fixture into `NormalizedResult`; then add quality,
   SLO, and comparison modules in that order.
5. **Create `perfeng-environment`.** Move Helm charts, local cluster scripts,
   and deployment documentation. Make a clean checkout capable of deploying
   released artifacts, not code from this source repository.
6. **Create `perfeng-control-plane`.** First publish the OpenAPI contract; then
   implement the Go run API, PostgreSQL migrations, and Kubernetes Job
   dispatcher. Port existing Python tests as API/domain acceptance tests.
7. **Create the empty `perfeng-k8s` skeleton only when its first benchmark is
   scheduled.** Avoid a repository with no owner or executable purpose.
8. **Retire this repository.** After an end-to-end run works from
   `perfeng-environment`, make this repository read-only/archived and retain it
   as the prototype history. Do not delete it until the migration has been
   accepted.

The migration is complete when a new clone of `perfeng-environment` can
bootstrap all repositories, deploy only released artifacts, run a k6 test,
collect its raw output, invoke analysis, persist the result through the control
plane, and display/return the resulting decision.

## Explicit non-goals for the first coding phase

- No dedicated UI repository.
- No Kubernetes operator or CRD before direct Job orchestration works.
- No event bus or permanently running analysis service.
- No cross-repository shared database access: only the control plane owns its
  database schema.
- No duplication of Cloud-Bulldozer tools; `perfeng-k8s` integrates them.
- No removal of working prototype paths before their extracted replacement is
  verified.
