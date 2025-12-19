#!/bin/bash

# ============================================================================
# Keiko for Teaching - View Development Logs
# ============================================================================

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_ROOT}/.dev-logs"

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if logs directory exists
if [ ! -d "$LOG_DIR" ]; then
    print_header "No Logs Found"
    echo -e "${YELLOW}Log directory does not exist. Start services first with: ./dev-start.sh${NC}\n"
    exit 1
fi

# Show available logs
print_header "Available Logs"

if [ -z "$1" ]; then
    # Show all logs
    echo -e "${GREEN}Services:${NC}"
    ls -lh "$LOG_DIR"/*.log 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' || echo "  No logs found"
    
    echo -e "\n${BLUE}Usage:${NC}"
    echo -e "  ${BLUE}./dev-logs.sh${NC}                    # Show this help"
    echo -e "  ${BLUE}./dev-logs.sh all${NC}                # Tail all logs"
    echo -e "  ${BLUE}./dev-logs.sh frontend${NC}           # Tail frontend logs"
    echo -e "  ${BLUE}./dev-logs.sh gateway${NC}            # Tail gateway logs"
    echo -e "  ${BLUE}./dev-logs.sh chat${NC}               # Tail chat service logs"
    echo -e "  ${BLUE}./dev-logs.sh search${NC}             # Tail search service logs"
    echo -e "  ${BLUE}./dev-logs.sh document${NC}           # Tail document service logs"
    echo -e "\n"
else
    case "$1" in
        all)
            print_header "Tailing All Logs"
            tail -f "$LOG_DIR"/*.log 2>/dev/null
            ;;
        frontend)
            print_header "Frontend Logs"
            tail -f "$LOG_DIR"/frontend.log 2>/dev/null || echo "Frontend log not found"
            ;;
        gateway)
            print_header "Gateway BFF Logs"
            tail -f "$LOG_DIR"/gateway-bff.log 2>/dev/null || echo "Gateway log not found"
            ;;
        chat)
            print_header "Chat Service Logs"
            tail -f "$LOG_DIR"/chat-service.log 2>/dev/null || echo "Chat service log not found"
            ;;
        search)
            print_header "Search Service Logs"
            tail -f "$LOG_DIR"/search-service.log 2>/dev/null || echo "Search service log not found"
            ;;
        document)
            print_header "Document Service Logs"
            tail -f "$LOG_DIR"/document-service.log 2>/dev/null || echo "Document service log not found"
            ;;
        *)
            echo -e "${YELLOW}Unknown service: $1${NC}"
            echo -e "Available services: all, frontend, gateway, chat, search, document\n"
            exit 1
            ;;
    esac
fi

