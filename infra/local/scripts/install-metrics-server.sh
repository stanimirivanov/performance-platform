#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
METRICS_SERVER_MANIFEST="${REPO_ROOT}/infra/local/kind/metrics-server.yaml"

echo "Installing metrics-server..."

# Apply the metrics-server manifest
kubectl apply -f "${METRICS_SERVER_MANIFEST}"

# Wait for metrics-server to be ready
echo "Waiting for metrics-server to be ready..."
kubectl wait --for=condition=ready pod \
    -l k8s-app=metrics-server \
    -n kube-system \
    --timeout=120s

# Verify installation
echo "Verifying metrics-server..."
kubectl get apiservice v1beta1.metrics.k8s.io

echo "Metrics-server installed successfully!"