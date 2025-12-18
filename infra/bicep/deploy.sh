#!/bin/bash
# Deploy Microsoft Foundry Infrastructure with Bicep
# This script deploys the complete Keiko infrastructure including:
# - Microsoft Foundry AI Hub and Project
# - Azure AI Services with model deployments
# - AKS cluster
# - Azure Container Registry
# - Azure AI Search
# - Redis Cache
# - Key Vault
# - API Management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
LOCATION=${2:-westeurope}
PROJECT_NAME="keiko"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Microsoft Foundry Infrastructure Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Location: ${YELLOW}${LOCATION}${NC}"
echo -e "Project: ${YELLOW}${PROJECT_NAME}${NC}"
echo -e "Subscription: ${YELLOW}${SUBSCRIPTION_ID}${NC}"
echo ""

# Confirm deployment
read -p "Do you want to proceed with the deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}Deployment cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Validating Bicep templates...${NC}"
az bicep build --file main.bicep

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Bicep validation successful${NC}"
else
    echo -e "${RED}✗ Bicep validation failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 2: Creating deployment...${NC}"
DEPLOYMENT_NAME="keiko-foundry-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

az deployment sub create \
    --name "${DEPLOYMENT_NAME}" \
    --location "${LOCATION}" \
    --template-file main.bicep \
    --parameters environment="${ENVIRONMENT}" \
                 location="${LOCATION}" \
                 projectName="${PROJECT_NAME}" \
    --verbose

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    # Get outputs
    echo -e "${GREEN}Deployment Outputs:${NC}"
    echo ""
    
    AKS_CLUSTER=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.aksClusterName.value -o tsv)
    ACR_LOGIN_SERVER=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.acrLoginServer.value -o tsv)
    FOUNDRY_ENDPOINT=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.foundryEndpoint.value -o tsv)
    FOUNDRY_AI_HUB=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.foundryAiHubName.value -o tsv)
    FOUNDRY_AI_PROJECT=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.foundryAiProjectName.value -o tsv)
    FOUNDRY_AI_SERVICES=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.foundryAiServicesEndpoint.value -o tsv)
    SEARCH_ENDPOINT=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.searchEndpoint.value -o tsv)
    REDIS_HOSTNAME=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.redisHostname.value -o tsv)
    MANAGED_IDENTITY_CLIENT_ID=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.managedIdentityClientId.value -o tsv)
    APIM_GATEWAY_URL=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.apimGatewayUrl.value -o tsv)
    KEY_VAULT_NAME=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.keyVaultName.value -o tsv)
    KEY_VAULT_URI=$(az deployment sub show --name "${DEPLOYMENT_NAME}" --query properties.outputs.keyVaultUri.value -o tsv)
    
    echo -e "AKS Cluster: ${YELLOW}${AKS_CLUSTER}${NC}"
    echo -e "ACR Login Server: ${YELLOW}${ACR_LOGIN_SERVER}${NC}"
    echo -e "Foundry Endpoint: ${YELLOW}${FOUNDRY_ENDPOINT}${NC}"
    echo -e "Foundry AI Hub: ${YELLOW}${FOUNDRY_AI_HUB}${NC}"
    echo -e "Foundry AI Project: ${YELLOW}${FOUNDRY_AI_PROJECT}${NC}"
    echo -e "Foundry AI Services: ${YELLOW}${FOUNDRY_AI_SERVICES}${NC}"
    echo -e "Search Endpoint: ${YELLOW}${SEARCH_ENDPOINT}${NC}"
    echo -e "Redis Hostname: ${YELLOW}${REDIS_HOSTNAME}${NC}"
    echo -e "Managed Identity Client ID: ${YELLOW}${MANAGED_IDENTITY_CLIENT_ID}${NC}"
    echo -e "API Management Gateway: ${YELLOW}${APIM_GATEWAY_URL}${NC}"
    echo -e "Key Vault Name: ${YELLOW}${KEY_VAULT_NAME}${NC}"
    echo -e "Key Vault URI: ${YELLOW}${KEY_VAULT_URI}${NC}"
    echo ""
    
    # Save outputs to file
    OUTPUT_FILE="deployment-outputs-${ENVIRONMENT}.env"
    cat > "${OUTPUT_FILE}" <<EOF
# Microsoft Foundry Infrastructure Outputs
# Generated: $(date)
# Deployment: ${DEPLOYMENT_NAME}

# Azure Subscription
AZURE_SUBSCRIPTION_ID=${SUBSCRIPTION_ID}
AZURE_RESOURCE_GROUP=rg-${PROJECT_NAME}-${ENVIRONMENT}

# AKS
AKS_CLUSTER_NAME=${AKS_CLUSTER}

# ACR
ACR_LOGIN_SERVER=${ACR_LOGIN_SERVER}

# Microsoft Foundry
FOUNDRY_ENDPOINT=${FOUNDRY_ENDPOINT}
FOUNDRY_AI_HUB_NAME=${FOUNDRY_AI_HUB}
FOUNDRY_PROJECT_NAME=${FOUNDRY_AI_PROJECT}
FOUNDRY_AI_SERVICES_ENDPOINT=${FOUNDRY_AI_SERVICES}

# Azure AI Search
AZURE_SEARCH_ENDPOINT=${SEARCH_ENDPOINT}

# Redis
REDIS_HOSTNAME=${REDIS_HOSTNAME}

# Managed Identity
AZURE_CLIENT_ID=${MANAGED_IDENTITY_CLIENT_ID}

# API Management
APIM_GATEWAY_URL=${APIM_GATEWAY_URL}

# Key Vault
KEY_VAULT_NAME=${KEY_VAULT_NAME}
KEY_VAULT_URI=${KEY_VAULT_URI}
EOF
    
    echo -e "${GREEN}✓ Outputs saved to: ${OUTPUT_FILE}${NC}"
    echo ""

    # Next steps
    echo -e "${GREEN}Next Steps:${NC}"
    echo ""
    echo "1. Configure AKS credentials:"
    echo -e "   ${YELLOW}az aks get-credentials --resource-group rg-${PROJECT_NAME}-${ENVIRONMENT} --name ${AKS_CLUSTER}${NC}"
    echo ""
    echo "2. Connect ACR to AKS:"
    echo -e "   ${YELLOW}az aks update --resource-group rg-${PROJECT_NAME}-${ENVIRONMENT} --name ${AKS_CLUSTER} --attach-acr ${ACR_LOGIN_SERVER}${NC}"
    echo ""
    echo "3. Deploy Kubernetes manifests:"
    echo -e "   ${YELLOW}kubectl apply -k ../kubernetes/base${NC}"
    echo ""
    echo "4. Update your .env file with the outputs from ${OUTPUT_FILE}"
    echo ""
    echo "5. Test Foundry connection:"
    echo -e "   ${YELLOW}curl -H \"Authorization: Bearer \$(az account get-access-token --resource https://ml.azure.com --query accessToken -o tsv)\" ${FOUNDRY_ENDPOINT}/health${NC}"
    echo ""

else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Deployment failed!${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Check the deployment logs for details:"
    echo -e "${YELLOW}az deployment sub show --name ${DEPLOYMENT_NAME}${NC}"
    exit 1
fi

