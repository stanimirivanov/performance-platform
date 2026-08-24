#!/bin/bash
set -euo pipefail

CLUSTER_NAME="perfeng-local"
FAILED=0

echo "========================================="
echo "PerfEng Cluster Health Check"
echo "========================================="

# Check 1: Cluster exists
echo "Checking cluster existence..."
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "✓ Cluster '${CLUSTER_NAME}' exists"
else
    echo "✗ Cluster '${CLUSTER_NAME}' does not exist"
    FAILED=1
fi

# Check 2: All nodes ready
echo "Checking node readiness..."
READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c " Ready " || echo "0")
TOTAL_NODES=$(kubectl get nodes --no-headers 2>/dev/null | wc -l || echo "0")
echo "Ready nodes: ${READY_NODES}/${TOTAL_NODES}"
if [ "${READY_NODES}" -lt "${TOTAL_NODES}" ]; then
    echo "✗ Not all nodes are ready"
    FAILED=1
fi

# Check 3: Node labels present
echo "Checking node labels..."
if kubectl get nodes -l workload=performance-generator --no-headers 2>/dev/null | grep -q .; then
    echo "✓ Generator node label present"
else
    echo "✗ Generator node label missing"
    FAILED=1
fi

if kubectl get nodes -l workload=sut --no-headers 2>/dev/null | grep -q .; then
    echo "✓ SUT node label present"
else
    echo "✗ SUT node label missing"
    FAILED=1
fi

# Check 4: Control plane ready
echo "Checking control plane..."
if kubectl get nodes -l node-role.kubernetes.io/control-plane --no-headers 2>/dev/null | grep -q " Ready "; then
    echo "✓ Control plane is ready"
else
    echo "✗ Control plane not ready"
    FAILED=1
fi

# Check 5: CoreDNS running
echo "Checking CoreDNS..."
if kubectl get pods -n kube-system -l k8s-app=kube-dns --no-headers 2>/dev/null | grep -q "Running"; then
    echo "✓ CoreDNS is running"
else
    echo "✗ CoreDNS not running"
    FAILED=1
fi

# Check 6: API server accessible
echo "Checking API server..."
if kubectl get --raw /healthz &>/dev/null; then
    echo "✓ API server is healthy"
else
    echo "✗ API server not accessible"
    FAILED=1
fi

echo ""
if [ "${FAILED}" -eq 0 ]; then
    echo "✓ All health checks passed!"
else
    echo "✗ Some health checks failed"
fi

exit ${FAILED}