#!/bin/bash

# ============================================================================
# Keiko for Teaching - Local Development Startup Script
# ============================================================================
# This script starts the complete application stack for local development:
# - Docker Compose services (Redis, Azurite, etc.)
# - Python backend services (FastAPI)
# - Node.js frontend (Next.js)
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env.local"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"
LOG_DIR="${PROJECT_ROOT}/.dev-logs"
PIDS_FILE="${LOG_DIR}/pids.txt"

# Load environment variables early (needed for cleanup function)
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# Cleanup Function
# ============================================================================

cleanup() {
    print_header "Shutting Down Services"
    
    if [ -f "$PIDS_FILE" ]; then
        while IFS= read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                print_info "Stopping process $pid..."
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PIDS_FILE"
        rm "$PIDS_FILE"
    fi
    
    print_info "Stopping Docker Compose services..."
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.dev.yml --env-file "$ENV_FILE" down 2>/dev/null || true
    
    print_success "All services stopped"
}

trap cleanup EXIT INT TERM

# ============================================================================
# Validation
# ============================================================================

print_header "Keiko for Teaching - Development Environment"

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_success "Docker found"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi
print_success "Docker Compose found"

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
fi
print_success "Node.js found ($(node --version))"

if ! command -v pnpm &> /dev/null; then
    print_warning "pnpm is not installed, installing..."
    npm install -g pnpm
fi
print_success "pnpm found ($(pnpm --version))"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi
print_success "Python 3 found ($(python3 --version))"

# ============================================================================
# Environment Setup
# ============================================================================

print_header "Setting Up Environment"

if [ ! -f "$ENV_FILE" ]; then
    print_warning ".env.local not found"
    print_info "Creating .env.local from .env.example..."
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    print_warning "Please edit .env.local with your actual values!"
    print_info "Required values for local development:"
    print_info "  - FOUNDRY_ENDPOINT, FOUNDRY_API_KEY (or AZURE_OPENAI_*)"
    print_info "  - AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY"
    print_info "  - AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY"
fi

print_success "Environment variables loaded"

# Create log directory
mkdir -p "$LOG_DIR"
> "$PIDS_FILE"

# ============================================================================
# Install Dependencies
# ============================================================================

print_header "Installing Dependencies"

print_info "Installing Node.js dependencies..."
cd "$PROJECT_ROOT"
pnpm install --frozen-lockfile 2>&1 | tail -5
print_success "Node.js dependencies installed"

# ============================================================================
# Start Docker Compose Services
# ============================================================================

print_header "Starting Docker Compose Services"

print_info "Starting Redis, Azurite, and other services..."
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.dev.yml --env-file "$ENV_FILE" up -d 2>&1 | grep -E "Creating|Starting|Done" || true

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose -f docker-compose.dev.yml --env-file "$ENV_FILE" ps | grep -q "redis.*Up"; then
    print_success "Redis is running"
else
    print_error "Redis failed to start"
    docker-compose -f docker-compose.dev.yml --env-file "$ENV_FILE" logs redis
    exit 1
fi

print_success "Docker Compose services started"

# ============================================================================
# Start Backend Services (via Docker Compose)
# ============================================================================

print_header "Starting Backend Services"

print_info "Building and starting backend services with Docker Compose..."
cd "$PROJECT_ROOT"
docker-compose --env-file "$ENV_FILE" up -d gateway chat search document ingestion 2>&1 | grep -E "Creating|Starting|Done" || true

# Wait for services to be ready
print_info "Waiting for backend services to be ready..."
sleep 15

# Check if services are running
for service in gateway chat search document ingestion; do
    if docker-compose ps "$service" 2>/dev/null | grep -q "Up"; then
        print_success "$service service is running"
    else
        print_error "$service service failed to start"
        docker-compose logs "$service" 2>&1 | tail -20
    fi
done

# ============================================================================
# Start Frontend (via Docker Compose)
# ============================================================================

print_header "Starting Frontend"

print_info "Building and starting frontend with Docker Compose..."
cd "$PROJECT_ROOT"
docker-compose --env-file "$ENV_FILE" up -d frontend 2>&1 | grep -E "Creating|Starting|Done" || true

# Wait for frontend to be ready
print_info "Waiting for frontend to be ready..."
sleep 10

# Check if frontend is running
if docker-compose ps frontend 2>/dev/null | grep -q "Up"; then
    print_success "Frontend is running"
else
    print_error "Frontend failed to start"
    docker-compose logs frontend 2>&1 | tail -20
fi

# ============================================================================
# Display Summary
# ============================================================================

print_header "Development Environment Ready"

echo -e "${GREEN}Services running:${NC}"
echo -e "  ${GREEN}✅${NC} Redis              http://localhost:6379"
echo -e "  ${GREEN}✅${NC} Azurite            http://localhost:10000"
echo -e "  ${GREEN}✅${NC} Gateway BFF        http://localhost:8000"
echo -e "  ${GREEN}✅${NC} Chat Service       http://localhost:8001"
echo -e "  ${GREEN}✅${NC} Search Service     http://localhost:8002"
echo -e "  ${GREEN}✅${NC} Document Service   http://localhost:8003"
echo -e "  ${GREEN}✅${NC} Frontend           http://localhost:3000"

echo -e "\n${BLUE}Docker Compose:${NC}"
echo -e "  ${BLUE}🐳${NC} View services: docker-compose ps"
echo -e "  ${BLUE}🐳${NC} View logs:     docker-compose logs -f [service]"
echo -e "  ${BLUE}🐳${NC} Stop services: docker-compose down"

echo -e "\n${BLUE}Commands:${NC}"
echo -e "  ${BLUE}🔨${NC} Build:  pnpm build"
echo -e "  ${BLUE}🧪${NC} Test:   pnpm test"
echo -e "  ${BLUE}📝${NC} Lint:   pnpm lint"
echo -e "  ${BLUE}🛑${NC} Stop:   ./dev-stop.sh"

echo -e "\n${YELLOW}Note:${NC} All services are running in Docker containers\n"

# Keep the script running
wait

