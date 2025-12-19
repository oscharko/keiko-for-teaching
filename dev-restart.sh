#!/bin/bash

# ============================================================================
# Keiko for Teaching - Restart Development Services
# ============================================================================

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_header "Restarting Keiko Development Services"

# Stop services
print_success "Stopping services..."
"${PROJECT_ROOT}/dev-stop.sh" > /dev/null 2>&1 || true

sleep 2

# Start services
print_success "Starting services..."
"${PROJECT_ROOT}/dev-start.sh"

