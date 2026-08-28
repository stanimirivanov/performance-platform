#!/bin/bash
# platform/scripts/run_tests.sh
# Run all tests with options to filter by group

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLATFORM_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PLATFORM_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== PerfEng Test Runner ===${NC}"
echo ""

# Function to run tests with a specific marker
run_test_group() {
    local marker=$1
    local name=$2
    
    echo -e "${YELLOW}Running $name tests...${NC}"
    pytest tests/ -m "$marker" -v --cov=perfeng --cov-report=term-missing --no-cov-on-fail
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ $name tests passed${NC}"
    else
        echo -e "${RED}✗ $name tests failed${NC}"
    fi
    echo ""
    return $exit_code
}

# Parse arguments
if [ $# -eq 0 ]; then
    # Run all tests
    echo -e "${YELLOW}Running all tests...${NC}"
    pytest tests/ -v --cov=perfeng --cov-report=html --cov-report=term
    exit $?
fi

case "$1" in
    metadata)
        run_test_group "metadata" "Metadata"
        ;;
    normalization)
        run_test_group "normalization" "Normalization"
        ;;
    core)
        run_test_group "core" "Core"
        ;;
    integration)
        run_test_group "integration" "Integration"
        ;;
    unit)
        run_test_group "not integration and not slow" "Unit"
        ;;
    fast)
        run_test_group "not integration and not slow and not requires_kubectl" "Fast"
        ;;
    all)
        pytest tests/ -v --cov=perfeng --cov-report=html --cov-report=term
        ;;
    help|--help|-h)
        echo "Usage: $0 [group]"
        echo ""
        echo "Groups:"
        echo "  metadata       - Run metadata tests only"
        echo "  normalization  - Run normalization tests only"
        echo "  core           - Run core tests only"
        echo "  integration    - Run integration tests only"
        echo "  unit           - Run unit tests only (excludes integration)"
        echo "  fast           - Run fast tests only (excludes integration, slow, kubectl)"
        echo "  all            - Run all tests (default)"
        echo "  help           - Show this help"
        ;;
    *)
        echo -e "${RED}Unknown group: $1${NC}"
        echo "Run '$0 help' for available groups"
        exit 1
        ;;
esac