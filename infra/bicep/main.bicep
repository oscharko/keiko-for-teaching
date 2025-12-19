// ============================================================================
// Keiko for Teaching - Azure Infrastructure Deployment
// ============================================================================
// Deploys the complete keiko-for-teaching application to Azure Container Apps.
//
// Prerequisites:
// - Existing Resource Group: rg-keiko-for-teaching
// - Existing Azure AI Search: gptkb-vyuvvvwlwg5jo
// ============================================================================

targetScope = 'resourceGroup'

// ============================================================================
// Parameters
// ============================================================================

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for resources - defaults to eastus to match AI Search')
param location string = 'eastus'

@description('Project name used for resource naming')
param projectName string = 'keikoteach'

@description('Existing Azure AI Search service name')
param existingSearchServiceName string = 'gptkb-vyuvvvwlwg5jo'

@description('Container image tag to deploy')
param imageTag string = 'latest'

@description('Azure AD B2C tenant name (optional)')
param azureAdB2cTenantName string = ''

@description('Azure AD B2C client ID (optional)')
param azureAdB2cClientId string = ''

@description('Microsoft Foundry endpoint (optional)')
param foundryEndpoint string = ''

@description('Microsoft Foundry project name (optional)')
param foundryProjectName string = ''

// ============================================================================
// Variables
// ============================================================================

// Ensure unique names by using a short hash
var uniqueSuffix = uniqueString(resourceGroup().id)
var shortSuffix = take(uniqueSuffix, 6)
var resourceSuffix = '${projectName}${environment}'

var tags = {
  project: 'keiko-for-teaching'
  environment: environment
  managedBy: 'bicep'
}

// Resource naming following Azure conventions
var names = {
  logAnalytics: 'log-${resourceSuffix}'
  appInsights: 'appi-${resourceSuffix}'
  containerRegistry: 'acr${projectName}${shortSuffix}'
  containerAppsEnv: 'cae-${resourceSuffix}'
  keyVault: 'kv-${projectName}-${shortSuffix}'
  storageAccount: 'st${projectName}${shortSuffix}'
  redis: 'redis-${resourceSuffix}'
  managedIdentity: 'id-${resourceSuffix}'
}

// ============================================================================
// Modules - Core Infrastructure
// ============================================================================

// Log Analytics Workspace for centralized logging
module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics-deployment'
  params: {
    name: names.logAnalytics
    location: location
    tags: tags
    retentionInDays: environment == 'prod' ? 90 : 30
  }
}

// Application Insights for monitoring and telemetry
module appInsights 'modules/app-insights.bicep' = {
  name: 'app-insights-deployment'
  params: {
    name: names.appInsights
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
  }
}

// User-Assigned Managed Identity for service authentication
module managedIdentity 'modules/managed-identity.bicep' = {
  name: 'managed-identity-deployment'
  params: {
    name: names.managedIdentity
    location: location
    tags: tags
  }
}

// Azure Container Registry for Docker images
module containerRegistry 'modules/container-registry.bicep' = {
  name: 'container-registry-deployment'
  params: {
    name: names.containerRegistry
    location: location
    tags: tags
    sku: environment == 'prod' ? 'Premium' : 'Basic'
  }
}

// Azure Key Vault for secrets management
module keyVault 'modules/key-vault.bicep' = {
  name: 'key-vault-deployment'
  params: {
    name: names.keyVault
    location: location
    tags: tags
    managedIdentityPrincipalId: managedIdentity.outputs.principalId
    enablePurgeProtection: environment == 'prod'
  }
}

// Azure Storage Account for documents
module storageAccount 'modules/storage-account.bicep' = {
  name: 'storage-account-deployment'
  params: {
    name: names.storageAccount
    location: location
    tags: tags
    managedIdentityPrincipalId: managedIdentity.outputs.principalId
  }
}

// Azure Cache for Redis
module redisCache 'modules/redis-cache.bicep' = {
  name: 'redis-deployment'
  params: {
    name: names.redis
    location: location
    tags: tags
    sku: environment == 'prod' ? 'Standard' : 'Basic'
    capacity: environment == 'prod' ? 1 : 0
  }
}

// Note: The existing Azure AI Search service (existingSearchServiceName) is referenced
// by name in the role assignments and search service configuration.

// Key Vault Secrets - Create secrets after Redis is deployed
module keyVaultSecrets 'modules/key-vault-secrets.bicep' = {
  name: 'key-vault-secrets-deployment'
  params: {
    keyVaultName: keyVault.outputs.name
    redisCacheName: redisCache.outputs.name
  }
}

// ============================================================================
// Modules - Container Apps Environment
// ============================================================================

// Container Apps Environment
module containerAppsEnv 'modules/container-apps-env.bicep' = {
  name: 'container-apps-env-deployment'
  params: {
    name: names.containerAppsEnv
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
    appInsightsConnectionString: appInsights.outputs.connectionString
  }
}

// ============================================================================
// Modules - Container Apps (Microservices)
// ============================================================================

// Frontend (Next.js)
module frontendApp 'modules/container-app.bicep' = {
  name: 'frontend-app-deployment'
  params: {
    name: 'ca-frontend-${environment}'
    location: location
    tags: tags
    containerAppsEnvId: containerAppsEnv.outputs.environmentId
    containerRegistryName: containerRegistry.outputs.name
    managedIdentityId: managedIdentity.outputs.identityId
    imageName: 'frontend'
    imageTag: imageTag
    targetPort: 3000
    isExternal: true
    cpu: '0.5'
    memory: '1Gi'
    minReplicas: environment == 'prod' ? 2 : 1
    maxReplicas: environment == 'prod' ? 10 : 3
    envVars: [
      { name: 'NEXT_PUBLIC_API_URL', value: 'https://ca-gateway-${environment}.${containerAppsEnv.outputs.defaultDomain}' }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.outputs.connectionString }
    ]
  }
}

// Gateway BFF (FastAPI)
module gatewayApp 'modules/container-app.bicep' = {
  name: 'gateway-app-deployment'
  params: {
    name: 'ca-gateway-${environment}'
    location: location
    tags: tags
    containerAppsEnvId: containerAppsEnv.outputs.environmentId
    containerRegistryName: containerRegistry.outputs.name
    managedIdentityId: managedIdentity.outputs.identityId
    imageName: 'gateway-bff'
    imageTag: imageTag
    targetPort: 8000
    isExternal: true
    cpu: '0.5'
    memory: '1Gi'
    minReplicas: environment == 'prod' ? 2 : 1
    maxReplicas: environment == 'prod' ? 10 : 3
    envVars: [
      { name: 'CHAT_SERVICE_URL', value: 'http://ca-chat-${environment}' }
      { name: 'SEARCH_SERVICE_URL', value: 'http://ca-search-${environment}' }
      { name: 'DOCUMENT_SERVICE_URL', value: 'http://ca-document-${environment}' }
      { name: 'AUTH_SERVICE_URL', value: 'http://ca-auth-${environment}' }
      { name: 'USER_SERVICE_URL', value: 'http://ca-user-${environment}' }
      { name: 'REDIS_URL', value: 'rediss://${redisCache.outputs.hostname}:${redisCache.outputs.sslPort}' }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.outputs.connectionString }
      { name: 'AZURE_CLIENT_ID', value: managedIdentity.outputs.clientId }
    ]
    secrets: [
      { name: 'redis-password', keyVaultSecretUri: '${keyVault.outputs.vaultUri}secrets/redis-password' }
    ]
  }
}

// Chat Service (FastAPI)
module chatApp 'modules/container-app.bicep' = {
  name: 'chat-app-deployment'
  params: {
    name: 'ca-chat-${environment}'
    location: location
    tags: tags
    containerAppsEnvId: containerAppsEnv.outputs.environmentId
    containerRegistryName: containerRegistry.outputs.name
    managedIdentityId: managedIdentity.outputs.identityId
    imageName: 'chat-service'
    imageTag: imageTag
    targetPort: 8001
    isExternal: false
    cpu: '1'
    memory: '2Gi'
    minReplicas: environment == 'prod' ? 2 : 1
    maxReplicas: environment == 'prod' ? 10 : 3
    envVars: [
      { name: 'FOUNDRY_ENDPOINT', value: foundryEndpoint }
      { name: 'FOUNDRY_PROJECT_NAME', value: foundryProjectName }
      { name: 'SEARCH_SERVICE_URL', value: 'http://ca-search-${environment}' }
      { name: 'REDIS_URL', value: 'rediss://${redisCache.outputs.hostname}:${redisCache.outputs.sslPort}' }
      { name: 'AZURE_CLIENT_ID', value: managedIdentity.outputs.clientId }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.outputs.connectionString }
    ]
    secrets: [
      { name: 'redis-password', keyVaultSecretUri: '${keyVault.outputs.vaultUri}secrets/redis-password' }
    ]
  }
}

// Search Service (FastAPI)
module searchApp 'modules/container-app.bicep' = {
  name: 'search-app-deployment'
  params: {
    name: 'ca-search-${environment}'
    location: location
    tags: tags
    containerAppsEnvId: containerAppsEnv.outputs.environmentId
    containerRegistryName: containerRegistry.outputs.name
    managedIdentityId: managedIdentity.outputs.identityId
    imageName: 'search-service'
    imageTag: imageTag
    targetPort: 8002
    isExternal: false
    cpu: '0.5'
    memory: '1Gi'
    minReplicas: environment == 'prod' ? 2 : 1
    maxReplicas: environment == 'prod' ? 5 : 2
    envVars: [
      { name: 'AZURE_SEARCH_ENDPOINT', value: 'https://${existingSearchServiceName}.search.windows.net' }
      { name: 'AZURE_SEARCH_INDEX_NAME', value: 'keiko-documents' }
      { name: 'REDIS_URL', value: 'rediss://${redisCache.outputs.hostname}:${redisCache.outputs.sslPort}' }
      { name: 'AZURE_CLIENT_ID', value: managedIdentity.outputs.clientId }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.outputs.connectionString }
    ]
    secrets: [
      { name: 'redis-password', keyVaultSecretUri: '${keyVault.outputs.vaultUri}secrets/redis-password' }
    ]
  }
}

// Document Service (FastAPI)
module documentApp 'modules/container-app.bicep' = {
  name: 'document-app-deployment'
  params: {
    name: 'ca-document-${environment}'
    location: location
    tags: tags
    containerAppsEnvId: containerAppsEnv.outputs.environmentId
    containerRegistryName: containerRegistry.outputs.name
    managedIdentityId: managedIdentity.outputs.identityId
    imageName: 'document-service'
    imageTag: imageTag
    targetPort: 8003
    isExternal: false
    cpu: '0.5'
    memory: '1Gi'
    minReplicas: 1
    maxReplicas: environment == 'prod' ? 5 : 2
    envVars: [
      { name: 'AZURE_STORAGE_ACCOUNT_NAME', value: storageAccount.outputs.name }
      { name: 'AZURE_STORAGE_CONTAINER_NAME', value: 'documents' }
      { name: 'INGESTION_SERVICE_URL', value: 'http://ca-ingestion-${environment}:50051' }
      { name: 'SEARCH_SERVICE_URL', value: 'http://ca-search-${environment}' }
      { name: 'REDIS_URL', value: 'rediss://${redisCache.outputs.hostname}:${redisCache.outputs.sslPort}' }
      { name: 'AZURE_CLIENT_ID', value: managedIdentity.outputs.clientId }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.outputs.connectionString }
    ]
    secrets: [
      { name: 'redis-password', keyVaultSecretUri: '${keyVault.outputs.vaultUri}secrets/redis-password' }
    ]
  }
}

// Auth Service (FastAPI)
module authApp 'modules/container-app.bicep' = {
  name: 'auth-app-deployment'
  params: {
    name: 'ca-auth-${environment}'
    location: location
    tags: tags
    containerAppsEnvId: containerAppsEnv.outputs.environmentId
    containerRegistryName: containerRegistry.outputs.name
    managedIdentityId: managedIdentity.outputs.identityId
    imageName: 'auth-service'
    imageTag: imageTag
    targetPort: 8004
    isExternal: false
    cpu: '0.25'
    memory: '0.5Gi'
    minReplicas: 1
    maxReplicas: environment == 'prod' ? 5 : 2
    envVars: [
      { name: 'AZURE_AD_B2C_TENANT_NAME', value: azureAdB2cTenantName }
      { name: 'AZURE_AD_B2C_CLIENT_ID', value: azureAdB2cClientId }
      { name: 'REDIS_URL', value: 'rediss://${redisCache.outputs.hostname}:${redisCache.outputs.sslPort}' }
      { name: 'AZURE_CLIENT_ID', value: managedIdentity.outputs.clientId }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.outputs.connectionString }
    ]
    secrets: [
      { name: 'redis-password', keyVaultSecretUri: '${keyVault.outputs.vaultUri}secrets/redis-password' }
      // Note: Using beta_auth_users.txt for dev environment, no Azure AD B2C needed
    ]
  }
}

// User Service (FastAPI)
module userApp 'modules/container-app.bicep' = {
  name: 'user-app-deployment'
  params: {
    name: 'ca-user-${environment}'
    location: location
    tags: tags
    containerAppsEnvId: containerAppsEnv.outputs.environmentId
    containerRegistryName: containerRegistry.outputs.name
    managedIdentityId: managedIdentity.outputs.identityId
    imageName: 'user-service'
    imageTag: imageTag
    targetPort: 8005
    isExternal: false
    cpu: '0.25'
    memory: '0.5Gi'
    minReplicas: 1
    maxReplicas: environment == 'prod' ? 5 : 2
    envVars: [
      { name: 'REDIS_URL', value: 'rediss://${redisCache.outputs.hostname}:${redisCache.outputs.sslPort}' }
      { name: 'AZURE_CLIENT_ID', value: managedIdentity.outputs.clientId }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.outputs.connectionString }
    ]
    secrets: [
      { name: 'redis-password', keyVaultSecretUri: '${keyVault.outputs.vaultUri}secrets/redis-password' }
    ]
  }
}

// Ingestion Service (Rust gRPC)
module ingestionApp 'modules/container-app.bicep' = {
  name: 'ingestion-app-deployment'
  params: {
    name: 'ca-ingestion-${environment}'
    location: location
    tags: tags
    containerAppsEnvId: containerAppsEnv.outputs.environmentId
    containerRegistryName: containerRegistry.outputs.name
    managedIdentityId: managedIdentity.outputs.identityId
    imageName: 'ingestion-service'
    imageTag: imageTag
    targetPort: 50051
    isExternal: false
    cpu: '1'
    memory: '2Gi'
    minReplicas: 1
    maxReplicas: environment == 'prod' ? 5 : 2
    transportProtocol: 'http2'
    envVars: [
      { name: 'AZURE_CLIENT_ID', value: managedIdentity.outputs.clientId }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.outputs.connectionString }
    ]
    secrets: [
      // Note: Document Intelligence not needed for dev environment
    ]
  }
}

// ============================================================================
// Modules - Role Assignments
// ============================================================================

module roleAssignments 'modules/role-assignments.bicep' = {
  name: 'role-assignments-deployment'
  params: {
    principalId: managedIdentity.outputs.principalId
    storageAccountName: storageAccount.outputs.name
    keyVaultName: keyVault.outputs.name
    containerRegistryName: containerRegistry.outputs.name
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Frontend application URL')
output frontendUrl string = 'https://${frontendApp.outputs.fqdn}'

@description('Gateway API URL')
output gatewayUrl string = 'https://${gatewayApp.outputs.fqdn}'

@description('Container Registry login server')
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer

@description('Key Vault URI')
output keyVaultUri string = keyVault.outputs.vaultUri

@description('Storage Account name')
output storageAccountName string = storageAccount.outputs.name

@description('Redis hostname')
output redisHostname string = redisCache.outputs.hostname

@description('Application Insights connection string')
output appInsightsConnectionString string = appInsights.outputs.connectionString

@description('Managed Identity client ID')
output managedIdentityClientId string = managedIdentity.outputs.clientId

@description('Container Apps Environment default domain')
output containerAppsDefaultDomain string = containerAppsEnv.outputs.defaultDomain

@description('Log Analytics Workspace ID')
output logAnalyticsWorkspaceId string = logAnalytics.outputs.workspaceId

