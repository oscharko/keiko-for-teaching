#!/bin/bash
# Validate all OpenAPI specifications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  OpenAPI Specification Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if redocly is installed
if ! command -v redocly &> /dev/null; then
    echo -e "${YELLOW}Warning: redocly is not installed${NC}"
    echo "Installing @redocly/cli..."
    npm install -g @redocly/cli
fi

# Get the repository root
REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
cd "$REPO_ROOT"

# Array of OpenAPI specification files
SPECS=(
    "services/chat-service/openapi.yaml"
    "services/search-service/openapi.yaml"
    "services/document-service/openapi.yaml"
    "services/ideas-service/openapi.yaml"
    "services/gateway-bff/openapi.yaml"
)

# Validation results
TOTAL=0
PASSED=0
FAILED=0

echo -e "${YELLOW}Validating OpenAPI specifications...${NC}"
echo ""

# Validate each specification
for spec in "${SPECS[@]}"; do
    TOTAL=$((TOTAL + 1))
    echo -e "${BLUE}Validating: ${spec}${NC}"
    
    if [ ! -f "$spec" ]; then
        echo -e "${RED}  ✗ File not found${NC}"
        FAILED=$((FAILED + 1))
        echo ""
        continue
    fi
    
    if redocly lint "$spec" --skip-rule=no-unused-components; then
        echo -e "${GREEN}  ✓ Valid${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}  ✗ Invalid${NC}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

# Print summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total:  ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED}${NC}"
else
    echo -e "Failed: ${FAILED}"
fi
echo ""

# Exit with error if any validation failed
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Validation failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All OpenAPI specifications are valid!${NC}"
    exit 0
fi

