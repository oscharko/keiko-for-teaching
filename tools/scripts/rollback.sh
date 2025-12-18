#!/bin/bash
# Rollback script for Keiko services
# Usage: ./rollback.sh <service-name> <target-version> [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME=$1
TARGET_VERSION=$2
ENVIRONMENT=${3:-production}
NAMESPACE="keiko-${ENVIRONMENT}"

# Validate inputs
if [ -z "$SERVICE_NAME" ] || [ -z "$TARGET_VERSION" ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 <service-name> <target-version> [environment]"
    echo "Example: $0 chat-service v1.2.0 production"
    exit 1
fi

echo -e "${YELLOW}=== Keiko Rollback Script ===${NC}"
echo "Service: $SERVICE_NAME"
echo "Target Version: $TARGET_VERSION"
echo "Environment: $ENVIRONMENT"
echo "Namespace: $NAMESPACE"
echo ""

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}Error: kubectl is not installed${NC}"
        exit 1
    fi
}

# Function to check if the deployment exists
check_deployment() {
    if ! kubectl get deployment "$SERVICE_NAME" -n "$NAMESPACE" &> /dev/null; then
        echo -e "${RED}Error: Deployment $SERVICE_NAME not found in namespace $NAMESPACE${NC}"
        exit 1
    fi
}

# Function to get current version
get_current_version() {
    kubectl get deployment "$SERVICE_NAME" -n "$NAMESPACE" \
        -o jsonpath='{.spec.template.spec.containers[0].image}' | \
        awk -F: '{print $2}'
}

# Function to create backup of current deployment
backup_deployment() {
    local backup_file="backup-${SERVICE_NAME}-$(date +%Y%m%d-%H%M%S).yaml"
    echo -e "${YELLOW}Creating backup of current deployment...${NC}"
    kubectl get deployment "$SERVICE_NAME" -n "$NAMESPACE" -o yaml > "$backup_file"
    echo -e "${GREEN}Backup saved to: $backup_file${NC}"
}

# Function to perform rollback
perform_rollback() {
    echo -e "${YELLOW}Rolling back $SERVICE_NAME to version $TARGET_VERSION...${NC}"
    
    # Update the image tag
    kubectl set image deployment/"$SERVICE_NAME" \
        "$SERVICE_NAME"="keikoregistry.azurecr.io/$SERVICE_NAME:$TARGET_VERSION" \
        -n "$NAMESPACE"
    
    # Wait for rollout to complete
    echo -e "${YELLOW}Waiting for rollout to complete...${NC}"
    kubectl rollout status deployment/"$SERVICE_NAME" -n "$NAMESPACE" --timeout=5m
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Rollback completed successfully!${NC}"
    else
        echo -e "${RED}Rollback failed!${NC}"
        exit 1
    fi
}

# Function to verify rollback
verify_rollback() {
    echo -e "${YELLOW}Verifying rollback...${NC}"
    
    # Check if pods are running
    local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$SERVICE_NAME" \
        -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | \
        grep -o "True" | wc -l)
    
    local total_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$SERVICE_NAME" \
        --no-headers | wc -l)
    
    echo "Ready pods: $ready_pods/$total_pods"
    
    if [ "$ready_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
        echo -e "${GREEN}All pods are ready${NC}"
    else
        echo -e "${RED}Warning: Not all pods are ready${NC}"
    fi
    
    # Check current version
    local current_version=$(get_current_version)
    echo "Current version: $current_version"
    
    if [ "$current_version" == "$TARGET_VERSION" ]; then
        echo -e "${GREEN}Version verified successfully${NC}"
    else
        echo -e "${RED}Warning: Version mismatch${NC}"
    fi
}

# Function to run health checks
run_health_checks() {
    echo -e "${YELLOW}Running health checks...${NC}"
    
    # Get service endpoint
    local service_url=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" \
        -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    
    if [ -z "$service_url" ]; then
        echo -e "${YELLOW}Service endpoint not available (might be ClusterIP)${NC}"
        return
    fi
    
    # Check health endpoint
    local health_status=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://$service_url/health" || echo "000")
    
    if [ "$health_status" == "200" ]; then
        echo -e "${GREEN}Health check passed${NC}"
    else
        echo -e "${RED}Health check failed (status: $health_status)${NC}"
    fi
}

# Main execution
main() {
    check_kubectl
    check_deployment
    
    # Get and display current version
    CURRENT_VERSION=$(get_current_version)
    echo -e "${YELLOW}Current version: $CURRENT_VERSION${NC}"
    
    # Confirm rollback
    echo -e "${YELLOW}Are you sure you want to rollback from $CURRENT_VERSION to $TARGET_VERSION? (yes/no)${NC}"
    read -r confirmation
    
    if [ "$confirmation" != "yes" ]; then
        echo -e "${RED}Rollback cancelled${NC}"
        exit 0
    fi
    
    # Execute rollback
    backup_deployment
    perform_rollback
    verify_rollback
    run_health_checks
    
    echo -e "${GREEN}=== Rollback completed ===${NC}"
}

# Run main function
main

