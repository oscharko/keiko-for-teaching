#!/bin/bash
# =============================================================================
# Keiko Teaching - Complete Build and Deployment Script
# Compatible with Bash 3.2+ (macOS default)
# =============================================================================

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-keiko-for-teaching}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FAILED=0
BUILT_IMAGES=""

# Logging
log_info() { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
log_success() { printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"; }
log_warning() { printf "${YELLOW}[WARNING]${NC} %s\n" "$1"; }
log_error() { printf "${RED}[ERROR]${NC} %s\n" "$1"; }
log_step() { printf "\n${CYAN}=== %s ===${NC}\n" "$1"; }

# Check prerequisites
check_prerequisites() {
    log_step "Checking Prerequisites"
    command -v az >/dev/null 2>&1 || { log_error "Azure CLI not found"; exit 1; }
    command -v docker >/dev/null 2>&1 || { log_error "Docker not found"; exit 1; }
    az account show >/dev/null 2>&1 || { log_error "Not logged into Azure"; exit 1; }
    docker info >/dev/null 2>&1 || { log_error "Docker not running"; exit 1; }
    log_success "All prerequisites met"
}

# Get ACR info and login
setup_acr() {
    log_step "Setting up ACR"
    ACR_NAME=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null)
    if [ -z "$ACR_NAME" ]; then log_error "No ACR found"; exit 1; fi
    ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
    log_info "ACR: $ACR_LOGIN_SERVER"
    az acr login --name "$ACR_NAME" || { log_error "ACR login failed"; exit 1; }
    log_success "Logged into ACR"
}

# Build and push a single image
# All Dockerfiles are designed to be built from the repository root
build_and_push() {
    local name="$1"
    local path="$2"
    local dockerfile="${PROJECT_ROOT}/${path}/Dockerfile"
    local tag="${ACR_LOGIN_SERVER}/${name}:latest"

    if [ ! -f "$dockerfile" ]; then
        log_warning "No Dockerfile for ${name}, skipping"
        return 0
    fi

    log_info "Building ${name}..."
    # All services are built from repository root to access shared code
    if docker build -t "$tag" -f "$dockerfile" "$PROJECT_ROOT"; then
        log_success "Built ${name}"
        BUILT_IMAGES="${BUILT_IMAGES} ${name}"

        log_info "Pushing ${name}..."
        if docker push "$tag"; then
            log_success "Pushed ${name}"
        else
            log_error "Push failed for ${name}"
            FAILED=$((FAILED + 1))
        fi
    else
        log_error "Build failed for ${name}"
        FAILED=$((FAILED + 1))
    fi
}

# Build all services
build_all() {
    log_step "Building and Pushing Docker Images"

    build_and_push "frontend" "apps/frontend"
    build_and_push "gateway-bff" "services/gateway-bff"
    build_and_push "chat-service" "services/chat-service"
    build_and_push "search-service" "services/search-service"
    build_and_push "document-service" "services/document-service"
    build_and_push "auth-service" "services/auth-service"
    build_and_push "user-service" "services/user-service"
    # Ingestion service (Rust) is temporarily disabled due to compilation issues
    # build_and_push "ingestion-service" "services/ingestion-service"
    log_warning "Skipping ingestion-service (Rust) - requires code fixes"
}

# Update Container Apps
update_apps() {
    log_step "Updating Container Apps"
    local apps
    apps=$(az containerapp list -g "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null)
    for app in $apps; do
        log_info "Updating ${app}..."
        if az containerapp update -n "$app" -g "$RESOURCE_GROUP" >/dev/null 2>&1; then
            log_success "Updated ${app}"
        else
            log_warning "Could not update ${app}"
        fi
    done
}

# Verify deployment
verify() {
    log_step "Verifying Deployment"
    az containerapp list -g "$RESOURCE_GROUP" \
        --query "[].{Name:name,State:properties.provisioningState,URL:properties.configuration.ingress.fqdn}" \
        -o table 2>/dev/null

    local frontend_url
    frontend_url=$(az containerapp list -g "$RESOURCE_GROUP" \
        --query "[?contains(name,'frontend')].properties.configuration.ingress.fqdn" -o tsv 2>/dev/null | head -1)
    if [ -n "$frontend_url" ]; then
        printf "\n${GREEN}Frontend URL: https://${frontend_url}${NC}\n"
    fi
}

# Print summary
summary() {
    log_step "Summary"
    printf "\n${CYAN}Built Images:${NC}${BUILT_IMAGES:-" none"}\n"
    if [ $FAILED -eq 0 ]; then
        log_success "Deployment completed successfully!"
    else
        log_error "Deployment completed with ${FAILED} error(s)"
    fi
}

# Main
main() {
    printf "${CYAN}╔══════════════════════════════════════════╗${NC}\n"
    printf "${CYAN}║  Keiko Teaching - Build & Deploy         ║${NC}\n"
    printf "${CYAN}╚══════════════════════════════════════════╝${NC}\n"
    log_info "Resource Group: $RESOURCE_GROUP"
    log_info "Project Root: $PROJECT_ROOT"

    check_prerequisites
    setup_acr
    build_all
    update_apps
    verify
    summary

    exit $FAILED
}

main "$@"

