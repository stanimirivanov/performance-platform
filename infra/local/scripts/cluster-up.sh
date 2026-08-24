#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
CLUSTER_CONFIG="${REPO_ROOT}/infra/local/kind/cluster-config.yaml"
CLUSTER_NAME="perfeng-local"

echo "========================================="
echo "Starting PerfEng Local Kubernetes Cluster"
echo "========================================="

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Error: kind is not installed"
    echo "Install from: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running"
    exit 1
fi

# Check if cluster already exists
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster '${CLUSTER_NAME}' already exists"
    echo "Use 'make cluster-down' to delete it first"
    exit 1
fi

# Create cluster
echo "Creating kind cluster '${CLUSTER_NAME}'..."
kind create cluster \
    --name "${CLUSTER_NAME}" \
    --config "${CLUSTER_CONFIG}" \
    --wait 120s

echo ""
echo "Cluster created successfully!"

# Wait for nodes to be ready
echo "Waiting for nodes to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Display cluster info
echo ""
echo "Cluster nodes:"
kubectl get nodes -o wide

echo ""
echo "Cluster setup complete!"