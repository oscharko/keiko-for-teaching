#!/bin/bash
# ============================================================================
# Keiko for Teaching - Complete Azure Cleanup Script
# ============================================================================
# Deletes ALL resources created by deploy.sh:
# - All Container Apps
# - Container Apps Environment
# - Azure Cache for Redis
# - Azure Storage Account
# - Azure Key Vault
# - Azure Container Registry
# - User-Assigned Managed Identity
# - Application Insights
# - Log Analytics Workspace
# - Resource Group (optional)
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
#
# Usage:
#   ./clean.sh [environment] [--delete-rg]
#
# Examples:
#   ./clean.sh dev              # Delete all resources but keep resource group
#   ./clean.sh dev --delete-rg  # Delete everything including resource group
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
DELETE_RESOURCE_GROUP=false
RESOURCE_GROUP="rg-keiko-for-teaching"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
for arg in "$@"; do
    case $arg in
        --delete-rg)
            DELETE_RESOURCE_GROUP=true
            shift
            ;;
    esac
done

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

delete_resource() {
    local resource_type=$1
    local resource_name=$2
    local resource_group=$3

    if [ -z "$resource_name" ]; then
        log_warning "No $resource_type found to delete"
        return 0
    fi

    log_info "Deleting $resource_type: $resource_name..."

    case $resource_type in
        "containerapp")
            az containerapp delete --name "$resource_name" --resource-group "$resource_group" --yes 2>/dev/null && \
                log_success "Deleted Container App: $resource_name" || \
                log_warning "Failed to delete Container App: $resource_name (may not exist)"
            ;;
        "container-apps-env")
            az containerapp env delete --name "$resource_name" --resource-group "$resource_group" --yes 2>/dev/null && \
                log_success "Deleted Container Apps Environment: $resource_name" || \
                log_warning "Failed to delete Container Apps Environment: $resource_name"
            ;;
        "acr")
            az acr delete --name "$resource_name" --resource-group "$resource_group" --yes 2>/dev/null && \
                log_success "Deleted Container Registry: $resource_name" || \
                log_warning "Failed to delete Container Registry: $resource_name"
            ;;
        "keyvault")
            az keyvault delete --name "$resource_name" --resource-group "$resource_group" 2>/dev/null && \
                log_success "Deleted Key Vault: $resource_name" || \
                log_warning "Failed to delete Key Vault: $resource_name"
            # Purge soft-deleted Key Vault
            log_info "Purging soft-deleted Key Vault: $resource_name..."
            az keyvault purge --name "$resource_name" 2>/dev/null && \
                log_success "Purged Key Vault: $resource_name" || \
                log_warning "Failed to purge Key Vault: $resource_name (may not be soft-deleted)"
            ;;
        "storage")
            az storage account delete --name "$resource_name" --resource-group "$resource_group" --yes 2>/dev/null && \
                log_success "Deleted Storage Account: $resource_name" || \
                log_warning "Failed to delete Storage Account: $resource_name"
            ;;
        "redis")
            az redis delete --name "$resource_name" --resource-group "$resource_group" --yes 2>/dev/null && \
                log_success "Deleted Redis Cache: $resource_name" || \
                log_warning "Failed to delete Redis Cache: $resource_name"
            ;;
        "identity")
            az identity delete --name "$resource_name" --resource-group "$resource_group" 2>/dev/null && \
                log_success "Deleted Managed Identity: $resource_name" || \
                log_warning "Failed to delete Managed Identity: $resource_name"
            ;;
        "log-analytics")
            az monitor log-analytics workspace delete --workspace-name "$resource_name" --resource-group "$resource_group" --yes --force 2>/dev/null && \
                log_success "Deleted Log Analytics Workspace: $resource_name" || \
                log_warning "Failed to delete Log Analytics Workspace: $resource_name"
            ;;
        "app-insights")
            az monitor app-insights component delete --app "$resource_name" --resource-group "$resource_group" 2>/dev/null && \
                log_success "Deleted Application Insights: $resource_name" || \
                log_warning "Failed to delete Application Insights: $resource_name"
            ;;
        *)
            log_error "Unknown resource type: $resource_type"
            return 1
            ;;
    esac
}

# ============================================================================
# Main Script
# ============================================================================

echo -e "${RED}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║           Keiko for Teaching - Complete Azure Cleanup                      ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Environment:         ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Resource Group:      ${YELLOW}${RESOURCE_GROUP}${NC}"
echo -e "Delete Resource Group: ${YELLOW}${DELETE_RESOURCE_GROUP}${NC}"
echo ""

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================
log_step "1" "Checking Prerequisites"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed."
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
echo -e "  Subscription: ${YELLOW}${SUBSCRIPTION_NAME}${NC}"

# Check if resource group exists
if ! az group show --name "${RESOURCE_GROUP}" &> /dev/null; then
    log_warning "Resource group '${RESOURCE_GROUP}' does not exist. Nothing to clean."
    exit 0
fi
log_success "Resource group exists"

# ============================================================================
# Step 2: Discover Resources
# ============================================================================
log_step "2" "Discovering Resources"

log_info "Scanning for resources in ${RESOURCE_GROUP}..."

# Container Apps
CONTAINER_APPS=$(az containerapp list --resource-group "${RESOURCE_GROUP}" --query "[].name" -o tsv 2>/dev/null || echo "")
CONTAINER_APPS_COUNT=$(echo "$CONTAINER_APPS" | grep -c . || echo "0")
log_info "Found ${CONTAINER_APPS_COUNT} Container Apps"

# Container Apps Environment
CAE_NAME=$(az containerapp env list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
[ -n "$CAE_NAME" ] && log_info "Found Container Apps Environment: $CAE_NAME"

# Redis Cache
REDIS_NAME=$(az redis list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
[ -n "$REDIS_NAME" ] && log_info "Found Redis Cache: $REDIS_NAME"

# Storage Account
STORAGE_NAME=$(az storage account list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
[ -n "$STORAGE_NAME" ] && log_info "Found Storage Account: $STORAGE_NAME"

# Key Vault
KV_NAME=$(az keyvault list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
[ -n "$KV_NAME" ] && log_info "Found Key Vault: $KV_NAME"

# Container Registry
ACR_NAME=$(az acr list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
[ -n "$ACR_NAME" ] && log_info "Found Container Registry: $ACR_NAME"

# Managed Identity
IDENTITY_NAME=$(az identity list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
[ -n "$IDENTITY_NAME" ] && log_info "Found Managed Identity: $IDENTITY_NAME"

# Application Insights
APP_INSIGHTS_NAME=$(az monitor app-insights component list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
[ -n "$APP_INSIGHTS_NAME" ] && log_info "Found Application Insights: $APP_INSIGHTS_NAME"

# Log Analytics
LOG_ANALYTICS_NAME=$(az monitor log-analytics workspace list --resource-group "${RESOURCE_GROUP}" --query "[0].name" -o tsv 2>/dev/null || echo "")
[ -n "$LOG_ANALYTICS_NAME" ] && log_info "Found Log Analytics Workspace: $LOG_ANALYTICS_NAME"

# ============================================================================
# Step 3: Confirm Deletion
# ============================================================================
log_step "3" "Deletion Confirmation"

echo ""
echo -e "${RED}WARNING: The following resources will be PERMANENTLY DELETED:${NC}"
echo ""
if [ -n "$CONTAINER_APPS" ]; then
    echo "  Container Apps:"
    echo "$CONTAINER_APPS" | while read -r app; do
        [ -n "$app" ] && echo "    • $app"
    done
fi
[ -n "$CAE_NAME" ] && echo "  • Container Apps Environment: $CAE_NAME"
[ -n "$REDIS_NAME" ] && echo "  • Redis Cache: $REDIS_NAME"
[ -n "$STORAGE_NAME" ] && echo "  • Storage Account: $STORAGE_NAME"
[ -n "$KV_NAME" ] && echo "  • Key Vault: $KV_NAME"
[ -n "$ACR_NAME" ] && echo "  • Container Registry: $ACR_NAME"
[ -n "$IDENTITY_NAME" ] && echo "  • Managed Identity: $IDENTITY_NAME"
[ -n "$APP_INSIGHTS_NAME" ] && echo "  • Application Insights: $APP_INSIGHTS_NAME"
[ -n "$LOG_ANALYTICS_NAME" ] && echo "  • Log Analytics Workspace: $LOG_ANALYTICS_NAME"
if [ "$DELETE_RESOURCE_GROUP" = true ]; then
    echo ""
    echo -e "  ${RED}• Resource Group: ${RESOURCE_GROUP}${NC}"
fi
echo ""

read -p "Are you ABSOLUTELY SURE you want to delete these resources? (type 'DELETE' to confirm): " CONFIRM
if [ "$CONFIRM" != "DELETE" ]; then
    log_warning "Cleanup cancelled by user."
    exit 0
fi

# ============================================================================
# Step 4: Delete Container Apps
# ============================================================================
log_step "4" "Deleting Container Apps"

if [ -n "$CONTAINER_APPS" ]; then
    echo "$CONTAINER_APPS" | while read -r app; do
        [ -n "$app" ] && delete_resource "containerapp" "$app" "${RESOURCE_GROUP}"
    done
else
    log_info "No Container Apps to delete"
fi

# ============================================================================
# Step 5: Delete Container Apps Environment
# ============================================================================
log_step "5" "Deleting Container Apps Environment"

delete_resource "container-apps-env" "$CAE_NAME" "${RESOURCE_GROUP}"

# ============================================================================
# Step 6: Delete Redis Cache
# ============================================================================
log_step "6" "Deleting Redis Cache"

delete_resource "redis" "$REDIS_NAME" "${RESOURCE_GROUP}"

# ============================================================================
# Step 7: Delete Storage Account
# ============================================================================
log_step "7" "Deleting Storage Account"

delete_resource "storage" "$STORAGE_NAME" "${RESOURCE_GROUP}"

# ============================================================================
# Step 8: Delete Key Vault
# ============================================================================
log_step "8" "Deleting Key Vault"

delete_resource "keyvault" "$KV_NAME" "${RESOURCE_GROUP}"

# ============================================================================
# Step 9: Delete Container Registry
# ============================================================================
log_step "9" "Deleting Container Registry"

delete_resource "acr" "$ACR_NAME" "${RESOURCE_GROUP}"

# ============================================================================
# Step 10: Delete Managed Identity
# ============================================================================
log_step "10" "Deleting Managed Identity"

delete_resource "identity" "$IDENTITY_NAME" "${RESOURCE_GROUP}"

# ============================================================================
# Step 11: Delete Application Insights
# ============================================================================
log_step "11" "Deleting Application Insights"

delete_resource "app-insights" "$APP_INSIGHTS_NAME" "${RESOURCE_GROUP}"

# ============================================================================
# Step 12: Delete Log Analytics Workspace
# ============================================================================
log_step "12" "Deleting Log Analytics Workspace"

delete_resource "log-analytics" "$LOG_ANALYTICS_NAME" "${RESOURCE_GROUP}"

# ============================================================================
# Step 13: Delete Resource Group (Optional)
# ============================================================================
if [ "$DELETE_RESOURCE_GROUP" = true ]; then
    log_step "13" "Deleting Resource Group"

    log_info "Deleting resource group: ${RESOURCE_GROUP}..."
    az group delete --name "${RESOURCE_GROUP}" --yes --no-wait 2>/dev/null && \
        log_success "Resource group deletion initiated (running in background)" || \
        log_warning "Failed to delete resource group"
else
    log_step "13" "Skipping Resource Group Deletion"
    log_info "Resource group '${RESOURCE_GROUP}' was preserved."
    log_info "To delete it, run: ./clean.sh ${ENVIRONMENT} --delete-rg"
fi

# ============================================================================
# Step 14: Verify Cleanup
# ============================================================================
log_step "14" "Verifying Cleanup"

log_info "Checking remaining resources..."

REMAINING_RESOURCES=$(az resource list --resource-group "${RESOURCE_GROUP}" --query "length(@)" -o tsv 2>/dev/null || echo "0")

if [ "$REMAINING_RESOURCES" = "0" ] || [ -z "$REMAINING_RESOURCES" ]; then
    log_success "All resources have been deleted from ${RESOURCE_GROUP}"
else
    log_warning "${REMAINING_RESOURCES} resources still remain in ${RESOURCE_GROUP}"
    log_info "Remaining resources:"
    az resource list --resource-group "${RESOURCE_GROUP}" --query "[].{Name:name, Type:type}" -o table 2>/dev/null
fi

# ============================================================================
# Step 15: Cleanup Local Files
# ============================================================================
log_step "15" "Cleaning Up Local Files"

OUTPUT_FILE="${SCRIPT_DIR}/deployment-outputs-${ENVIRONMENT}.env"
if [ -f "${OUTPUT_FILE}" ]; then
    rm -f "${OUTPUT_FILE}"
    log_success "Deleted local output file: ${OUTPUT_FILE}"
else
    log_info "No local output file to delete"
fi

# ============================================================================
# Final Summary
# ============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Cleanup Completed Successfully!                                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Cleanup Summary:${NC}"
echo -e "  Resource Group:   ${YELLOW}${RESOURCE_GROUP}${NC}"
echo -e "  Environment:      ${YELLOW}${ENVIRONMENT}${NC}"
if [ "$DELETE_RESOURCE_GROUP" = true ]; then
    echo -e "  Resource Group:   ${RED}DELETED${NC}"
else
    echo -e "  Resource Group:   ${GREEN}PRESERVED${NC}"
fi
echo ""

log_success "All resources created by deploy.sh have been cleaned up!"
exit 0
