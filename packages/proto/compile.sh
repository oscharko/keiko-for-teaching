#!/bin/bash
# Proto compilation script for generating code from Protocol Buffers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Protocol Buffers compilation...${NC}"

# Check if buf is installed
if ! command -v buf &> /dev/null; then
    echo -e "${RED}Error: buf is not installed${NC}"
    echo "Please install buf: https://docs.buf.build/installation"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}Linting proto files...${NC}"
buf lint

echo -e "${YELLOW}Generating code...${NC}"
buf generate

echo -e "${GREEN}Proto compilation completed successfully!${NC}"
echo ""
echo "Generated files:"
echo "  - Python: services/ingestion-service/proto/"
echo "  - TypeScript: packages/proto-ts/"

