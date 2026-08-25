#!/bin/bash
set -euo pipefail

# Default values
TEST_NAME=""
PROFILE=""
BASE_URL="http://perf-sut-service.perf-sut:8080"
OUTPUT_DIR="results"
TIMEOUT_SECONDS=900

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --test-name)
            TEST_NAME="$2"
            shift 2
            ;;
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT_SECONDS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$TEST_NAME" ]]; then
    echo "Error: --test-name is required"
    exit 1
fi

if [[ -z "$PROFILE" ]]; then
    echo "Error: --profile is required"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
K6_DIR="${REPO_ROOT}/tests/k6"
OUTPUT_DIR_PATH="${REPO_ROOT}/${OUTPUT_DIR}"

echo "========================================="
echo "Running k6 Test as Kubernetes Job"
echo "========================================="
echo "Test: ${TEST_NAME}"
echo "Profile: ${PROFILE}"
echo "Base URL: ${BASE_URL}"
echo ""

# Generate unique run ID
RUN_ID="perf-$(date +%Y%m%d-%H%M%S)-$(uuidgen | cut -c1-8)"
echo "Run ID: ${RUN_ID}"

# Define paths
TEST_SCRIPT="tests/${TEST_NAME}/scenario.js"
WORKLOAD_CONFIG="workloads/${PROFILE}/${TEST_NAME}.json"
CONFIG_MAP_NAME="k6-test-scripts-${TEST_NAME}"
JOB_NAME="k6-test-${TEST_NAME}-$(uuidgen | cut -c1-8)"

# Check if test files exist
if [[ ! -f "${K6_DIR}/${TEST_SCRIPT}" ]]; then
    echo "Error: Test script not found: ${K6_DIR}/${TEST_SCRIPT}"
    exit 1
fi

if [[ ! -f "${K6_DIR}/${WORKLOAD_CONFIG}" ]]; then
    echo "Error: Workload config not found: ${K6_DIR}/${WORKLOAD_CONFIG}"
    exit 1
fi

# Create ConfigMap
echo "Creating ConfigMap with test scripts..."
kubectl create configmap "${CONFIG_MAP_NAME}" \
    -n perf-generators \
    --from-file="${K6_DIR}/${TEST_SCRIPT}" \
    --from-file="${K6_DIR}/${WORKLOAD_CONFIG}"

# Create Job
echo "Creating Kubernetes Job..."
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: ${JOB_NAME}
  namespace: perf-generators
  labels:
    app: k6-test
    perfeng.io/component: test-runner
    perfeng.io/test: "${TEST_NAME}"
    perfeng.io/profile: "${PROFILE}"
    perfeng.io/run-id: "${RUN_ID}"
spec:
  backoffLimit: 2
  activeDeadlineSeconds: ${TIMEOUT_SECONDS}
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app: k6-test
        perfeng.io/test: "${TEST_NAME}"
        perfeng.io/run-id: "${RUN_ID}"
    spec:
      restartPolicy: Never
      serviceAccountName: perf-generator
      nodeSelector:
        workload: performance-generator
      containers:
        - name: k6
          image: perfeng-k6-tests:latest
          imagePullPolicy: IfNotPresent
          command:
            - k6
            - run
            - --config
            - "/test-data/${WORKLOAD_CONFIG}"
            - "/test-data/${TEST_SCRIPT}"
            - --out
            - "json=/results/results.json"
            - --summary-export
            - "/results/summary.json"
          env:
            - name: BASE_URL
              value: "${BASE_URL}"
            - name: PERF_RUN_ID
              value: "${RUN_ID}"
            - name: PERF_PROFILE
              value: "${PROFILE}"
            - name: PERF_TEST_NAME
              value: "${TEST_NAME}"
          volumeMounts:
            - name: test-data
              mountPath: /test-data
            - name: results
              mountPath: /results
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
      volumes:
        - name: test-data
          configMap:
            name: ${CONFIG_MAP_NAME}
        - name: results
          emptyDir: {}
EOF

# Wait for job completion
echo "Waiting for job to complete..."
kubectl wait --for=condition=complete \
    --timeout="${TIMEOUT_SECONDS}s" \
    job/"${JOB_NAME}" \
    -n perf-generators

# Collect results
echo "Collecting results..."

RUN_OUTPUT_DIR="${OUTPUT_DIR_PATH}/${RUN_ID}"
mkdir -p "${RUN_OUTPUT_DIR}"

POD_NAME=$(kubectl get pods -n perf-generators \
    -l "perfeng.io/run-id=${RUN_ID}" \
    -o jsonpath='{.items[0].metadata.name}')

if [[ -n "${POD_NAME}" ]]; then
    kubectl cp "perf-generators/${POD_NAME}:/results/results.json" "${RUN_OUTPUT_DIR}/results.json"
    kubectl cp "perf-generators/${POD_NAME}:/results/summary.json" "${RUN_OUTPUT_DIR}/summary.json"
    kubectl logs "${POD_NAME}" -n perf-generators > "${RUN_OUTPUT_DIR}/pod.log"
    
    echo "Results saved to: ${RUN_OUTPUT_DIR}"
else
    echo "Error: Could not find pod for run ${RUN_ID}"
fi

# Clean up
echo "Cleaning up..."
kubectl delete configmap "${CONFIG_MAP_NAME}" -n perf-generators 2>/dev/null || true
kubectl delete job "${JOB_NAME}" -n perf-generators 2>/dev/null || true

echo ""
echo "k6 test execution complete!"
echo "Run ID: ${RUN_ID}"
echo "Results: ${RUN_OUTPUT_DIR}"