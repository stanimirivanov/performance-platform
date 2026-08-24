# Local Kubernetes Cluster Setup

## Prerequisites

- Docker Desktop (or Docker Engine)
- kind (Kubernetes in Docker)
- kubectl

## Installation

### Install Docker

Download and install Docker Desktop from: https://www.docker.com/products/docker-desktop

### Install kind

```bash
# Windows (using winget)
winget install Kubernetes.kind

# macOS (using Homebrew)
brew install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Install kubectl

```bash
# Windows (using winget)
winget install Kubernetes.kubectl

# macOS (using Homebrew)
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Cluster Management

#### Create Cluster

```bash
make cluster-up
```

This creates a kind cluster named perfeng-local with:

- 1 control plane node
- 1 worker node for performance generators (workload=performance-generator)
- 1 worker node for SUT (workload=sut)

#### Check Cluster Status

```bash
make cluster-status
```

#### Run Health Check

```bash
make cluster-health
```

#### Install metrics-server

```bash
make install-metrics
```

#### Delete Cluster

```bash
make cluster-down
```

### Node Labels

| Node Type     | Label                                   | Purpose                      |
| ------------- | --------------------------------------- | ---------------------------- |
| Control Plane | `node-role.kubernetes.io/control-plane` | Kubernetes control plane     |
| Generator     | `workload=performance-generator`        | Runs k6/Playwright test jobs |
| SUT           | `workload=sut`                          | Runs system under test       |

### Node Labels (Repeated Configuration)

| Node Type     | Label                                   | Purpose                      |
| ------------- | --------------------------------------- | ---------------------------- |
| Control Plane | `node-role.kubernetes.io/control-plane` | Kubernetes control plane     |
| Generator     | `workload=performance-generator`        | Runs k6/Playwright test jobs |
| SUT           | `workload=sut`                          | Runs system under test       |

### Node Taints

| Node Type | Taint                                       | Effect                      |
| --------- | ------------------------------------------- | --------------------------- |
| Generator | `workload=performance-generator:NoSchedule` | Prevents non-generator pods |
| SUT       | `workload=sut:NoSchedule`                   | Prevents non-SUT pods       |

### Verification

After cluster creation, verify:

```bash
# Check nodes
kubectl get nodes -o wide

# Check labels
kubectl get nodes --show-labels

# Check taints
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# Check metrics-server
kubectl top nodes
```

### Troubleshooting

#### Cluster creation fails

Check Docker is running:

```bash
docker info
```

#### metrics-server not working

Check pod status:

```bash
kubectl get pods -n kube-system -l k8s-app=metrics-server
kubectl logs -n kube-system -l k8s-app=metrics-server
```

#### Cannot connect to cluster

Check kubeconfig:

```bash
kind get kubeconfig --name perfeng-local
kubectl config current-context
```

## Step 9: Run Setup

```bash
# From repository root
cd /path/to/perfeng

# Create cluster
make cluster-up

# Install metrics-server
make install-metrics

# Check status
make cluster-status

# Run health check
make cluster-health
```

### Expected Output

After successful setup, you should see:

Cluster nodes:

````text
NAME STATUS ROLES AGE VERSION
perfeng-local-control-plane Ready control-plane 1m v1.28.0
perfeng-local-worker Ready <none> 1m v1.28.0
perfeng-local-worker2 Ready <none> 1m v1.28.0
```

Node labels:

```text
perfeng-local-control-plane: workload=control-plane
perfeng-local-worker: workload=performance-generator, perfeng.io/node-type=generator
perfeng-local-worker2: workload=sut, perfeng.io/node-type=sut
```
````
