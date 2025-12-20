#!/bin/bash

# ============================================================================
# Keiko for Teaching - Stop Development Services
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env.local"
LOG_DIR="${PROJECT_ROOT}/.dev-logs"
PIDS_FILE="${LOG_DIR}/pids.txt"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header "Stopping Keiko Development Services"

# Kill background processes
if [ -f "$PIDS_FILE" ]; then
    print_info "Stopping background services..."
    while IFS= read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            print_info "Stopping process $pid..."
            kill "$pid" 2>/dev/null || true
            sleep 1
        fi
    done < "$PIDS_FILE"
    rm "$PIDS_FILE"
    print_success "Background services stopped"
fi

# Stop Docker Compose (all services)
print_info "Stopping Docker Compose services..."
cd "$PROJECT_ROOT"
docker-compose --env-file "$ENV_FILE" down 2>&1 | grep -E "Stopping|Removing|Done" || true
print_success "Docker Compose services stopped"

print_header "All Services Stopped"
echo -e "${GREEN}Development environment is now stopped.${NC}\n"

