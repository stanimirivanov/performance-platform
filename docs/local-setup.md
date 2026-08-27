# Local Kubernetes Cluster Setup

- ## Overview

This guide explains how to set up the PerfEng local development environment
using:

- **kind** (Kubernetes in Docker) for the cluster
- **Helm** for infrastructure deployment
- **Docker** for container images

## Prerequisites

Install the following dependencies for your OS.

- Docker Desktop (or Docker Engine)
- kind (Kubernetes in Docker)
- kubectl
- Helm 3+

Ensure Docker Desktop is running and has at least:

- 4 CPUs
- 8GB RAM
- 60GB Disk Space

## Cluster Management

### Create Cluster

```bash
make cluster-up
```

This creates a kind cluster named `perfeng-local` with:

- 1 control plane node (`workload=control-plane`)
- 1 worker node for generators (`workload=performance-generator`)
- 1 worker node for SUT (`workload=sut`)

### Check Cluster Status

```bash
make cluster-health
```

### Delete Cluster

```bash
make cluster-down
```

## Infrastructure Deployment

The infrastructure is deployed via Helm charts.

### Manage Infrastructure

```bash
make infra-install
```

This installs:

- **Namespaces**: perf-platform, perf-generators, perf-sut, monitoring
- **RBAC**: ServiceAccounts, Roles, RoleBindings, ClusterRoles,
  ClusterRoleBindings
- **Network Policies**: Default deny, allow rules, DNS egress
- **Resource Quotas**: ResourceQuotas and LimitRanges
- **Metrics Server**: For kubectl top commands
- **MinIO**: Object storage for test artifacts
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **kube-state-metrics**: Kubernetes object metrics
- **node-exporter**: Node system metrics

Other infrastructure commands can be found in [Makefile](../Makefile).

## Run database migrations

Migrations are managed with a custom Python script that applies timestamped SQL
files in order.

**Prerequisites**:

- PostgreSQL is running (either locally or via the Helm chart).
- The migration script uses `localhost:5432` by default. If using Kubernetes,
  port‑forward the service first:

  ```bash
  make port-forward # or kubectl port-forward -n metadata-db svc/postgres-service 5432:5432
  ```

**Commands**:

```bash
# Apply all pending migrations (idempotent)
make apply-migrations

# Reset the database (drops all schemas and reapplies from scratch)
make reset-migrations
```

The script stores applied migration names in a `metadata.migrations` table, so
repeated runs only apply new files.

## Sample SUT Management

A sample System Under Test is provided for testing purposes. Install, check
status and uninstall can be achieved with:

```bash
make sut-install
make sut-status
make sut-uninstall
```

## k6 Performance Testing

K6 testing in the cluster depends on building the Docker image and the sample
sut or other target.

```bash
## Install sample SUT
make sut-install

# k6 Test Runner
make k6-build-image

## Run k6 checkout smoke test
k6-smoke: k6-build-image

## Run k6 search smoke test
k6-search-smoke: k6-build-image
```

Other k6 test commands can be found in [Makefile](../Makefile).

## Access Points

### Grafana

- **URL**: http://localhost:30300
- **Username**: admin
- **Password**: admin

### Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Access at: http://localhost:9090
```

### MinIO

```bash
kubectl port-forward -n perf-platform svc/minio 9001:9001
# Console: http://localhost:9001
# Username: perfeng
# Password: perfeng123
```

### Node Labels

| Node          | Label                            | Purpose                  |
| ------------- | -------------------------------- | ------------------------ |
| Control Plane | `workload=control-plane`         | Kubernetes control plane |
| Worker 1      | `workload=performance-generator` | k6 test generator pods   |
| Worker 2      | `workload=sut`                   | System under test        |

### Namespaces

| Namespace         | Purpose                           |
| ----------------- | --------------------------------- |
| `perf-platform`   | Platform orchestration components |
| `perf-generators` | Test generator pods (k6)          |
| `perf-sut`        | System under test                 |
| `monitoring`      | Prometheus, Grafana, exporters    |

### Helm Charts

| Chart           | Purpose                             |
| --------------- | ----------------------------------- |
| `perfeng-infra` | Full infrastructure (10 sub-charts) |
| `sample-sut`    | Sample System Under Test            |
| `k6-runner`     | k6 test execution                   |

## Troubleshooting

### Cluster creation fails

```bash
# Check Docker is running
docker info

# Delete and recreate
make cluster-down
make cluster-up
```

### Helm install fails

```bash
# Check what's installed
helm list --all-namespaces

# Check for orphaned resources
kubectl get all --all-namespaces | grep perfeng

# Clean up and retry
helm uninstall perfeng-infra
kubectl delete namespace perf-platform --force --grace-period=0
kubectl delete namespace perf-generators --force --grace-period=0
kubectl delete namespace perf-sut --force --grace-period=0
kubectl delete namespace monitoring --force --grace-period=0
make infra-install
```

### PVC not binding

```bash
# Check PVC status
kubectl get pvc --all-namespaces

# Check storage class
kubectl get storageclass

# Check local-path provisioner
kubectl get pods -n local-path-storage
kubectl logs -n local-path-storage -l app=local-path-provisioner --tail=50
```

### Pod can't schedule

```bash
# Check pod events
kubectl describe pod -n <namespace> <pod-name>

# Check node taints
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# Check resource quotas
kubectl get resourcequota -n <namespace>
kubectl describe limitrange -n <namespace>
```

### k6 test fails

```bash
# Check if SUT is running
kubectl get pods -n perf-sut

# Check k6 pod logs
kubectl logs -n perf-generators -l app=k6-test --tail=100

# Check network connectivity
kubectl run test-pod -n perf-generators --rm -it --image=busybox -- wget -qO- http://perf-sut-service.perf-sut:8080/
```

## Complete Workflow Example

```bash
# 1. Start cluster
make cluster-up

# 2. Install infrastructure
make infra-install

# 3. Verify infrastructure
make infra-status

# 4. Apply migrations
make apply-migrations

# 5. Install sample SUT
make sut-install

# 6. Build k6 image
make k6-build-image

# 7. Run smoke test
make k6-search-smoke

# 8. Check results
make k6-list
kubectl get jobs -n perf-generators
kubectl logs -n perf-generators -l app=k6-test --tail=50

# 9. Clean up
make k6-uninstall TEST=search PROFILE=smoke
make sut-uninstall
make reset-migrations
make infra-uninstall
make cluster-down
```

## See also

- [Monitoring Stack Documentation](monitoring-stack.md)
- [Metric Naming Conventions](architecture/metric-naming.md)
- [Schema Versioning](architecture/schema-versioning.md)
