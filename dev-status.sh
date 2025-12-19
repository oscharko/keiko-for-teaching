#!/bin/bash

# ============================================================================
# Keiko for Teaching - Check Development Services Status
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env.local"

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

check_service() {
    local name=$1
    local url=$2
    local port=$3
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} $name (port $port)"
        return 0
    else
        echo -e "  ${RED}❌${NC} $name (port $port) - Not responding"
        return 1
    fi
}

print_header "Keiko Development Services Status"

# Check Docker Compose services
echo -e "${BLUE}Docker Compose Services:${NC}"
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.dev.yml --env-file "$ENV_FILE" ps 2>/dev/null | tail -n +2 | awk '{
    if ($NF ~ /Up/) {
        print "  \033[0;32m✅\033[0m " $1 " (" $NF ")"
    } else {
        print "  \033[0;31m❌\033[0m " $1 " (" $NF ")"
    }
}' || echo "  ${RED}Docker Compose not running${NC}"

echo -e "\n${BLUE}Backend Services:${NC}"
check_service "Gateway BFF" "http://localhost:8000/health" "8000" || true
check_service "Chat Service" "http://localhost:8001/health" "8001" || true
check_service "Search Service" "http://localhost:8002/health" "8002" || true
check_service "Document Service" "http://localhost:8003/health" "8003" || true

echo -e "\n${BLUE}Frontend:${NC}"
check_service "Next.js Frontend" "http://localhost:3000" "3000" || true

echo -e "\n${BLUE}Infrastructure:${NC}"
check_service "Redis" "redis://localhost:6379" "6379" || true
check_service "Azurite" "http://localhost:10000" "10000" || true

echo -e "\n${BLUE}Quick Links:${NC}"
echo -e "  ${BLUE}🌐${NC} Frontend:     http://localhost:3000"
echo -e "  ${BLUE}🔌${NC} Gateway API:  http://localhost:8000"
echo -e "  ${BLUE}💬${NC} Chat:         http://localhost:8001"
echo -e "  ${BLUE}🔍${NC} Search:       http://localhost:8002"
echo -e "  ${BLUE}📄${NC} Document:     http://localhost:8003"
echo -e "  ${BLUE}🗄️  Redis:        localhost:6379"
echo -e "  ${BLUE}☁️  Azurite:       http://localhost:10000"

echo -e "\n${BLUE}Commands:${NC}"
echo -e "  ${BLUE}./dev-start.sh${NC}     - Start all services"
echo -e "  ${BLUE}./dev-stop.sh${NC}      - Stop all services"
echo -e "  ${BLUE}./dev-restart.sh${NC}   - Restart all services"
echo -e "  ${BLUE}./dev-logs.sh${NC}      - View service logs"
echo -e "\n"

