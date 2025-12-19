#!/bin/bash

# Start all Python services locally with proper PYTHONPATH
# Usage: ./scripts/start-services-local.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES_PATH="$REPO_ROOT/services"
export PYTHONPATH="$SERVICES_PATH"

# Redis configuration
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_PASSWORD=""

# Service URLs
export CHAT_SERVICE_URL="http://localhost:8001"
export SEARCH_SERVICE_URL="http://localhost:8002"
export DOCUMENT_SERVICE_URL="http://localhost:8003"
export AUTH_SERVICE_URL="http://localhost:8004"
export USER_SERVICE_URL="http://localhost:8005"

echo "=== Starting all Python services locally ==="
echo "PYTHONPATH: $PYTHONPATH"
echo ""

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local service_path="$SERVICES_PATH/$service_name"
    
    echo "Starting $service_name on port $port..."
    cd "$service_path"
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port $port --reload &
    echo "✅ $service_name started (PID: $!)"
}

# Start all services
start_service "gateway-bff" 8000
start_service "chat-service" 8001
start_service "search-service" 8002
start_service "document-service" 8003
start_service "auth-service" 8004
start_service "user-service" 8005

echo ""
echo "=== All services started ==="
echo "Gateway BFF: http://localhost:8000/docs"
echo "Chat Service: http://localhost:8001/docs"
echo "Search Service: http://localhost:8002/docs"
echo "Document Service: http://localhost:8003/docs"
echo "Auth Service: http://localhost:8004/docs"
echo "User Service: http://localhost:8005/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for all background processes
wait

