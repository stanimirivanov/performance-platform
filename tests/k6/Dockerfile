# PerfEng k6 Test Runner
# Base image with k6, test libraries, workload profiles, and test scenarios
#
# Build:
#   docker build -t perfeng-k6-tests .
#
# Run (development with volume mount):
#   docker run --rm -v $(pwd):/tests perfeng-k6-tests run --config workloads/smoke/checkout.json tests/checkout/scenario.js
#
# Run (production using image contents):
#   docker run --rm perfeng-k6-tests run --config workloads/regression/checkout.json tests/checkout/scenario.js

FROM grafana/k6:2.2.0

WORKDIR /tests

COPY lib/ /tests/lib/
COPY workloads/ /tests/workloads/
COPY tests/ /tests/tests/

ENTRYPOINT ["k6"]
CMD ["run", "--help"]