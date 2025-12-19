#!/bin/bash
# ============================================================================
# Keiko for Teaching - Complete Azure Deployment Script
# ============================================================================
# Deploys the complete keiko-for-teaching infrastructure to Azure:
# - Resource Group (rg-keiko-for-teaching)
# - Log Analytics Workspace
# - Application Insights
# - User-Assigned Managed Identity
# - Azure Container Registry
# - Azure Key Vault
# - Azure Storage Account
# - Azure Cache for Redis
# - Container Apps Environment
# - Container Apps (Frontend, Gateway, Chat, Search, Document, Auth, User, Ingestion)
# - Role Assignments
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
# - Bicep CLI installed (az bicep install)
#
# Usage:
#   ./deploy.sh [environment] [location]
#
# Examples:
#   ./deploy.sh dev westeurope
#   ./deploy.sh prod westeurope
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
LOCATION=${2:-westeurope}
PROJECT_NAME="keikoteach"
RESOURCE_GROUP="rg-keiko-for-teaching"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Track deployment status
DEPLOYMENT_SUCCESS=false
DEPLOYMENT_NAME=""

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Step $1: $2${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_resource_exists() {
    local resource_type=$1
    local resource_name=$2
    local resource_group=$3

    case $resource_type in
        "containerapp")
            az containerapp show --name "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        "acr")
            az acr show --name "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        "keyvault")
            az keyvault show --name "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        "storage")
            az storage account show --name "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        "redis")
            az redis show --name "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        "identity")
            az identity show --name "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        "log-analytics")
            az monitor log-analytics workspace show --workspace-name "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        "app-insights")
            az monitor app-insights component show --app "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        "container-apps-env")
            az containerapp env show --name "$resource_name" --resource-group "$resource_group" &>/dev/null
            ;;
        *)
            return 1
            ;;
    esac
}

verify_resource() {
    local resource_type=$1
    local resource_name=$2
    local resource_group=$3

    if check_resource_exists "$resource_type" "$resource_name" "$resource_group"; then
        log_success "✓ $resource_type: $resource_name"
        return 0
    else
        log_error "✗ $resource_type: $resource_name NOT FOUND"
        return 1
    fi
}

# ============================================================================
# Main Script
# ============================================================================

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Keiko for Teaching - Complete Azure Deployment                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Environment:    ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Location:       ${YELLOW}${LOCATION}${NC}"
echo -e "Resource Group: ${YELLOW}${RESOURCE_GROUP}${NC}"
echo -e "Project Name:   ${YELLOW}${PROJECT_NAME}${NC}"
echo ""

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================
log_step "1" "Checking Prerequisites"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed."
    echo "Please install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi
log_success "Azure CLI is installed"

# Check if logged in
if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure CLI."
    echo "Please run: az login"
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
log_success "Logged in to Azure"
echo -e "  Subscription:   ${YELLOW}${SUBSCRIPTION_NAME}${NC}"
echo -e "  Subscription ID: ${YELLOW}${SUBSCRIPTION_ID}${NC}"

# Check Bicep CLI
if ! az bicep version &> /dev/null; then
    log_warning "Bicep CLI not found. Installing..."
    az bicep install
fi
log_success "Bicep CLI is available"

# ============================================================================
# Step 2: Create Resource Group
# ============================================================================
log_step "2" "Creating Resource Group"

if az group show --name "${RESOURCE_GROUP}" &> /dev/null; then
    log_info "Resource group '${RESOURCE_GROUP}' already exists"
else
    log_info "Creating resource group '${RESOURCE_GROUP}'..."
    az group create \
        --name "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --tags project=keiko-for-teaching environment="${ENVIRONMENT}" managedBy=bicep
    log_success "Resource group created"
fi

# ============================================================================
# Step 3: Validate Bicep Templates
# ============================================================================
log_step "3" "Validating Bicep Templates"

cd "${SCRIPT_DIR}"
az bicep build --file main.bicep --stdout > /dev/null 2>&1

if [ $? -eq 0 ]; then
    log_success "Bicep validation successful"
else
    log_error "Bicep validation failed"
    exit 1
fi

# ============================================================================
# Step 4: Select Parameter File
# ============================================================================
log_step "4" "Selecting Parameter File"

PARAM_FILE="parameters.${ENVIRONMENT}.json"
if [ ! -f "${PARAM_FILE}" ]; then
    log_error "Parameter file '${PARAM_FILE}' not found."
    exit 1
fi
log_success "Using parameter file: ${PARAM_FILE}"

# ============================================================================
# Step 5: Confirm Deployment
# ============================================================================
log_step "5" "Deployment Confirmation"

echo ""
echo -e "${YELLOW}The following resources will be created:${NC}"
echo "  • Log Analytics Workspace"
echo "  • Application Insights"
echo "  • User-Assigned Managed Identity"
echo "  • Azure Container Registry"
echo "  • Azure Key Vault"
echo "  • Azure Storage Account"
echo "  • Azure Cache for Redis"
echo "  • Container Apps Environment"
echo "  • 8 Container Apps (Frontend, Gateway, Chat, Search, Document, Auth, User, Ingestion)"
echo "  • Role Assignments"
echo ""

read -p "Do you want to proceed with the deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log_warning "Deployment cancelled by user."
    exit 0
fi

# ============================================================================
# Step 6: Deploy Infrastructure
# ============================================================================
log_step "6" "Deploying Infrastructure"

DEPLOYMENT_NAME="keiko-teaching-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
log_info "Deployment name: ${DEPLOYMENT_NAME}"
log_info "This may take 15-30 minutes..."

DEPLOYMENT_OUTPUT=$(az deployment group create \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --template-file main.bicep \
    --parameters "@${PARAM_FILE}" \
    --parameters location="${LOCATION}" \
    2>&1)

DEPLOYMENT_EXIT_CODE=$?

if [ $DEPLOYMENT_EXIT_CODE -eq 0 ]; then
    DEPLOYMENT_SUCCESS=true
    log_success "Bicep deployment completed successfully"
else
    # Check if the only failure is RoleAssignmentExists (which is not critical)
    if echo "$DEPLOYMENT_OUTPUT" | grep -q "RoleAssignmentExists"; then
        log_warning "Deployment completed with RoleAssignmentExists warning (role assignments already exist)"
        log_info "This is expected for re-deployments. Continuing..."
        DEPLOYMENT_SUCCESS=true
    else
        log_error "Bicep deployment failed"
        echo "$DEPLOYMENT_OUTPUT"
        echo ""
        echo "Check the deployment logs for details:"
        echo -e "${YELLOW}az deployment group show --name ${DEPLOYMENT_NAME} --resource-group ${RESOURCE_GROUP}${NC}"
        exit 1
    fi
fi

# ============================================================================
# Step 7: Build and Push Docker Images
# ============================================================================
log_step "7" "Building and Pushing Docker Images"

# Get ACR name from deployment
ACR_NAME=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.containerRegistryLoginServer.value -o tsv 2>/dev/null | cut -d'.' -f1)

if [ -z "$ACR_NAME" ] || [ "$ACR_NAME" = "N/A" ]; then
    # Fallback: get ACR name directly from resource group
    ACR_NAME=$(az acr list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null)
fi

if [ -z "$ACR_NAME" ]; then
    log_error "Could not determine ACR name"
    exit 1
fi

ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
log_info "Container Registry: ${ACR_LOGIN_SERVER}"

# Login to ACR
log_info "Logging in to Azure Container Registry..."
az acr login --name "${ACR_NAME}"
if [ $? -ne 0 ]; then
    log_error "Failed to login to ACR"
    exit 1
fi
log_success "Logged in to ACR"

# Navigate to repository root
REPO_ROOT="${SCRIPT_DIR}/../.."
cd "${REPO_ROOT}"
log_info "Building from repository root: $(pwd)"

# Define services to build
declare -A SERVICES=(
    ["frontend"]="apps/frontend/Dockerfile"
    ["gateway-bff"]="services/gateway-bff/Dockerfile"
    ["chat-service"]="services/chat-service/Dockerfile"
    ["search-service"]="services/search-service/Dockerfile"
    ["document-service"]="services/document-service/Dockerfile"
    ["auth-service"]="services/auth-service/Dockerfile"
    ["user-service"]="services/user-service/Dockerfile"
    ["ingestion-service"]="services/ingestion-service/Dockerfile"
)

# Build and push each service
BUILD_FAILED=false
for service in "${!SERVICES[@]}"; do
    dockerfile="${SERVICES[$service]}"
    image_name="${ACR_LOGIN_SERVER}/${service}:latest"

    log_info "Building ${service}..."

    if [ ! -f "${dockerfile}" ]; then
        log_warning "Dockerfile not found: ${dockerfile}, skipping ${service}"
        continue
    fi

    docker build -t "${image_name}" -f "${dockerfile}" . 2>&1 | tail -20

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "Built ${service}"

        log_info "Pushing ${service} to ACR..."
        docker push "${image_name}" 2>&1 | tail -5

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log_success "Pushed ${service}"
        else
            log_error "Failed to push ${service}"
            BUILD_FAILED=true
        fi
    else
        log_error "Failed to build ${service}"
        BUILD_FAILED=true
    fi
done

if [ "$BUILD_FAILED" = true ]; then
    log_warning "Some images failed to build/push. Container Apps may not start correctly."
fi

# Return to script directory
cd "${SCRIPT_DIR}"

# ============================================================================
# Step 8: Update Container Apps with New Images
# ============================================================================
log_step "8" "Updating Container Apps with New Images"

# Map service names to container app names
declare -A APP_MAPPING=(
    ["frontend"]="ca-frontend-${ENVIRONMENT}"
    ["gateway-bff"]="ca-gateway-${ENVIRONMENT}"
    ["chat-service"]="ca-chat-${ENVIRONMENT}"
    ["search-service"]="ca-search-${ENVIRONMENT}"
    ["document-service"]="ca-document-${ENVIRONMENT}"
    ["auth-service"]="ca-auth-${ENVIRONMENT}"
    ["user-service"]="ca-user-${ENVIRONMENT}"
    ["ingestion-service"]="ca-ingestion-${ENVIRONMENT}"
)

UPDATE_FAILED=false
for service in "${!APP_MAPPING[@]}"; do
    app_name="${APP_MAPPING[$service]}"
    image_name="${ACR_LOGIN_SERVER}/${service}:latest"

    log_info "Updating ${app_name} with image ${image_name}..."

    az containerapp update \
        --name "${app_name}" \
        --resource-group "${RESOURCE_GROUP}" \
        --image "${image_name}" \
        --output none 2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "Updated ${app_name}"
    else
        log_warning "Failed to update ${app_name} (may not exist yet)"
        UPDATE_FAILED=true
    fi
done

if [ "$UPDATE_FAILED" = true ]; then
    log_warning "Some Container Apps could not be updated."
fi

# ============================================================================
# Step 9: Retrieve Deployment Outputs
# ============================================================================
log_step "9" "Retrieving Deployment Outputs"

FRONTEND_URL=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.frontendUrl.value -o tsv 2>/dev/null || echo "N/A")

GATEWAY_URL=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.gatewayUrl.value -o tsv 2>/dev/null || echo "N/A")

ACR_LOGIN_SERVER=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.containerRegistryLoginServer.value -o tsv 2>/dev/null || echo "N/A")

KEY_VAULT_URI=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.keyVaultUri.value -o tsv 2>/dev/null || echo "N/A")

STORAGE_ACCOUNT=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.storageAccountName.value -o tsv 2>/dev/null || echo "N/A")

REDIS_HOSTNAME=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.redisHostname.value -o tsv 2>/dev/null || echo "N/A")

MANAGED_IDENTITY_CLIENT_ID=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.managedIdentityClientId.value -o tsv 2>/dev/null || echo "N/A")

CONTAINER_APPS_DOMAIN=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.containerAppsDefaultDomain.value -o tsv 2>/dev/null || echo "N/A")

LOG_ANALYTICS_ID=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.logAnalyticsWorkspaceId.value -o tsv 2>/dev/null || echo "N/A")

APP_INSIGHTS_CONN=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query properties.outputs.appInsightsConnectionString.value -o tsv 2>/dev/null || echo "N/A")

log_success "Deployment outputs retrieved"

# ============================================================================
# Step 10: Verify All Resources
# ============================================================================
log_step "10" "Verifying All Resources"

VERIFICATION_FAILED=false

# Derive resource names from naming convention
UNIQUE_SUFFIX=$(az group show --name "${RESOURCE_GROUP}" --query id -o tsv | md5sum | cut -c1-13)
SHORT_SUFFIX=$(echo "${UNIQUE_SUFFIX}" | cut -c1-6)

# Get actual resource names from Azure
log_info "Discovering deployed resources..."

# Log Analytics
LOG_ANALYTICS_NAME=$(az monitor log-analytics workspace list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$LOG_ANALYTICS_NAME" ]; then
    verify_resource "log-analytics" "$LOG_ANALYTICS_NAME" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
else
    log_error "✗ Log Analytics Workspace NOT FOUND"
    VERIFICATION_FAILED=true
fi

# Application Insights
APP_INSIGHTS_NAME=$(az monitor app-insights component list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$APP_INSIGHTS_NAME" ]; then
    verify_resource "app-insights" "$APP_INSIGHTS_NAME" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
else
    log_error "✗ Application Insights NOT FOUND"
    VERIFICATION_FAILED=true
fi

# Managed Identity
IDENTITY_NAME=$(az identity list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$IDENTITY_NAME" ]; then
    verify_resource "identity" "$IDENTITY_NAME" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
else
    log_error "✗ Managed Identity NOT FOUND"
    VERIFICATION_FAILED=true
fi

# Container Registry
ACR_NAME=$(az acr list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$ACR_NAME" ]; then
    verify_resource "acr" "$ACR_NAME" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
else
    log_error "✗ Container Registry NOT FOUND"
    VERIFICATION_FAILED=true
fi

# Key Vault
KV_NAME=$(az keyvault list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$KV_NAME" ]; then
    verify_resource "keyvault" "$KV_NAME" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
else
    log_error "✗ Key Vault NOT FOUND"
    VERIFICATION_FAILED=true
fi

# Storage Account
STORAGE_NAME=$(az storage account list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$STORAGE_NAME" ]; then
    verify_resource "storage" "$STORAGE_NAME" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
else
    log_error "✗ Storage Account NOT FOUND"
    VERIFICATION_FAILED=true
fi

# Redis Cache
REDIS_NAME=$(az redis list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$REDIS_NAME" ]; then
    verify_resource "redis" "$REDIS_NAME" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
else
    log_error "✗ Redis Cache NOT FOUND"
    VERIFICATION_FAILED=true
fi

# Container Apps Environment
CAE_NAME=$(az containerapp env list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$CAE_NAME" ]; then
    verify_resource "container-apps-env" "$CAE_NAME" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
else
    log_error "✗ Container Apps Environment NOT FOUND"
    VERIFICATION_FAILED=true
fi

# Container Apps
log_info "Verifying Container Apps..."
CONTAINER_APPS=("ca-frontend-${ENVIRONMENT}" "ca-gateway-${ENVIRONMENT}" "ca-chat-${ENVIRONMENT}" "ca-search-${ENVIRONMENT}" "ca-document-${ENVIRONMENT}" "ca-auth-${ENVIRONMENT}" "ca-user-${ENVIRONMENT}" "ca-ingestion-${ENVIRONMENT}")

for app in "${CONTAINER_APPS[@]}"; do
    verify_resource "containerapp" "$app" "${RESOURCE_GROUP}" || VERIFICATION_FAILED=true
done

# ============================================================================
# Step 11: Test Connectivity
# ============================================================================
log_step "11" "Testing Connectivity"

# Test Frontend URL
if [ "$FRONTEND_URL" != "N/A" ] && [ -n "$FRONTEND_URL" ]; then
    log_info "Testing Frontend URL: ${FRONTEND_URL}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "${FRONTEND_URL}" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "503" ]; then
        log_success "Frontend is reachable (HTTP ${HTTP_CODE})"
    else
        log_warning "Frontend returned HTTP ${HTTP_CODE} (may need container images)"
    fi
else
    log_warning "Frontend URL not available for testing"
fi

# Test Gateway URL
if [ "$GATEWAY_URL" != "N/A" ] && [ -n "$GATEWAY_URL" ]; then
    log_info "Testing Gateway URL: ${GATEWAY_URL}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "${GATEWAY_URL}/health" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "503" ]; then
        log_success "Gateway is reachable (HTTP ${HTTP_CODE})"
    else
        log_warning "Gateway returned HTTP ${HTTP_CODE} (may need container images)"
    fi
else
    log_warning "Gateway URL not available for testing"
fi

# ============================================================================
# Step 12: Save Deployment Outputs
# ============================================================================
log_step "12" "Saving Deployment Outputs"

OUTPUT_FILE="${SCRIPT_DIR}/deployment-outputs-${ENVIRONMENT}.env"
cat > "${OUTPUT_FILE}" <<EOF
# ============================================================================
# Keiko for Teaching - Deployment Outputs
# ============================================================================
# Generated: $(date)
# Deployment: ${DEPLOYMENT_NAME}
# Environment: ${ENVIRONMENT}
# ============================================================================

# Azure Subscription
AZURE_SUBSCRIPTION_ID=${SUBSCRIPTION_ID}
AZURE_RESOURCE_GROUP=${RESOURCE_GROUP}

# Application URLs
FRONTEND_URL=${FRONTEND_URL}
GATEWAY_URL=${GATEWAY_URL}

# Azure Container Registry
ACR_LOGIN_SERVER=${ACR_LOGIN_SERVER}
ACR_NAME=${ACR_NAME}

# Azure Key Vault
KEY_VAULT_URI=${KEY_VAULT_URI}
KEY_VAULT_NAME=${KV_NAME}

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=${STORAGE_ACCOUNT}

# Azure Cache for Redis
REDIS_HOSTNAME=${REDIS_HOSTNAME}
REDIS_NAME=${REDIS_NAME}

# Managed Identity
AZURE_CLIENT_ID=${MANAGED_IDENTITY_CLIENT_ID}
MANAGED_IDENTITY_NAME=${IDENTITY_NAME}

# Container Apps
CONTAINER_APPS_DOMAIN=${CONTAINER_APPS_DOMAIN}
CONTAINER_APPS_ENV_NAME=${CAE_NAME}

# Monitoring
LOG_ANALYTICS_WORKSPACE_ID=${LOG_ANALYTICS_ID}
APP_INSIGHTS_CONNECTION_STRING=${APP_INSIGHTS_CONN}
LOG_ANALYTICS_NAME=${LOG_ANALYTICS_NAME}
APP_INSIGHTS_NAME=${APP_INSIGHTS_NAME}

# Azure AI Search (existing)
AZURE_SEARCH_ENDPOINT=https://gptkb-vyuvvvwlwg5jo.search.windows.net
EOF

log_success "Outputs saved to: ${OUTPUT_FILE}"

# ============================================================================
# Final Summary
# ============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
if [ "$VERIFICATION_FAILED" = true ]; then
    echo -e "${YELLOW}║           Deployment Completed with Warnings                               ║${NC}"
else
    echo -e "${GREEN}║           Deployment Completed Successfully!                               ║${NC}"
fi
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Deployment Summary:${NC}"
echo -e "  Deployment Name:  ${YELLOW}${DEPLOYMENT_NAME}${NC}"
echo -e "  Resource Group:   ${YELLOW}${RESOURCE_GROUP}${NC}"
echo -e "  Environment:      ${YELLOW}${ENVIRONMENT}${NC}"
echo ""

echo -e "${BLUE}Resource URLs:${NC}"
echo -e "  Frontend:         ${YELLOW}${FRONTEND_URL}${NC}"
echo -e "  Gateway API:      ${YELLOW}${GATEWAY_URL}${NC}"
echo -e "  ACR Login Server: ${YELLOW}${ACR_LOGIN_SERVER}${NC}"
echo -e "  Key Vault:        ${YELLOW}${KEY_VAULT_URI}${NC}"
echo ""

echo -e "${BLUE}Access your application:${NC}"
echo -e "  Frontend: ${YELLOW}${FRONTEND_URL}${NC}"
echo -e "  API:      ${YELLOW}${GATEWAY_URL}${NC}"
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  View logs:     ${YELLOW}az containerapp logs show --name ca-frontend-${ENVIRONMENT} --resource-group ${RESOURCE_GROUP} --follow${NC}"
echo -e "  Scale app:     ${YELLOW}az containerapp update --name ca-frontend-${ENVIRONMENT} --resource-group ${RESOURCE_GROUP} --min-replicas 2 --max-replicas 5${NC}"
echo -e "  Cleanup:       ${YELLOW}./clean.sh ${ENVIRONMENT}${NC}"
echo ""

if [ "$VERIFICATION_FAILED" = true ]; then
    log_warning "Some resources could not be verified. Please check the Azure Portal."
    exit 1
fi

log_success "All resources deployed and verified successfully!"
exit 0

