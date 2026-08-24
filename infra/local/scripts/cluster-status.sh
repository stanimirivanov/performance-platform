#!/bin/bash
set -euo pipefail

CLUSTER_NAME="perfeng-local"

echo "========================================="
echo "PerfEng Local Kubernetes Cluster Status"
echo "========================================="

# Check if cluster exists
if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster '${CLUSTER_NAME}' does not exist"
    exit 1
fi

echo "Cluster exists: ${CLUSTER_NAME}"
echo ""

# Show nodes
echo "=== Nodes ==="
kubectl get nodes -o wide

echo ""
echo "=== Node Labels ==="
kubectl get nodes --show-labels

echo ""
echo "=== Node Taints ==="
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

echo ""
echo "=== Pods (all namespaces) ==="
kubectl get pods --all-namespaces -o wide

echo ""
echo "=== Resource Usage ==="
kubectl top nodes 2>/dev/null || echo "metrics-server not installed yet"

echo ""
echo "=== Kubernetes Version ==="
kubectl version --short