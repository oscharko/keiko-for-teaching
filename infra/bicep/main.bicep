targetScope = 'subscription'

@description('Environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region')
param location string = 'westeurope'

@description('Project name')
param projectName string = 'keiko'

var resourceGroupName = 'rg-${projectName}-${environment}'
var tags = {
  project: projectName
  environment: environment
  managedBy: 'bicep'
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module aks 'modules/aks.bicep' = {
  scope: rg
  name: 'aks-deployment'
  params: {
    clusterName: 'aks-${projectName}-${environment}'
    location: location
    tags: tags
  }
}

module acr 'modules/acr.bicep' = {
  scope: rg
  name: 'acr-deployment'
  params: {
    acrName: 'acr${projectName}${environment}'
    location: location
    tags: tags
  }
}

// Microsoft Foundry AI Hub and Project
module foundry 'modules/foundry.bicep' = {
  scope: rg
  name: 'foundry-deployment'
  params: {
    hubName: 'aihub-${projectName}-${environment}'
    projectName: 'aiproj-${projectName}-${environment}'
    location: location
    tags: tags
    storageAccountName: 'st${projectName}${environment}ai'
    keyVaultName: 'kv-${projectName}-${environment}'
    appInsightsName: 'appi-${projectName}-${environment}'
    containerRegistryName: 'acr${projectName}${environment}ai'
    enableAgentService: true
    enableFoundryIQ: true
  }
  dependsOn: [
    keyVault
  ]
}

module search 'modules/search.bicep' = {
  scope: rg
  name: 'search-deployment'
  params: {
    searchName: 'srch-${projectName}-${environment}'
    location: location
    tags: tags
  }
}

module redis 'modules/redis.bicep' = {
  scope: rg
  name: 'redis-deployment'
  params: {
    redisName: 'redis-${projectName}-${environment}'
    location: location
    tags: tags
  }
}

module identity 'modules/identity.bicep' = {
  scope: rg
  name: 'identity-deployment'
  params: {
    identityName: 'id-${projectName}-${environment}'
    location: location
    tags: tags
  }
}

module apim 'modules/apim.bicep' = {
  scope: rg
  name: 'apim-deployment'
  params: {
    apimName: 'apim-${projectName}-${environment}'
    location: location
    tags: tags
    publisherEmail: 'admin@keiko.local'
    publisherName: 'Keiko'
    skuName: environment == 'prod' ? 'Standard' : 'Developer'
  }
}

module keyVault 'modules/keyvault.bicep' = {
  scope: rg
  name: 'keyvault-deployment'
  params: {
    keyVaultName: 'kv-${projectName}-${environment}'
    location: location
    tags: tags
    skuName: environment == 'prod' ? 'premium' : 'standard'
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: environment == 'prod' ? true : false
    enableRbacAuthorization: true
    publicNetworkAccess: environment == 'prod' ? 'Disabled' : 'Enabled'
    aksManagedIdentityPrincipalId: identity.outputs.principalId
    additionalPrincipalIds: []
  }
  dependsOn: [
    identity
  ]
}

module roleAssignments 'modules/role-assignments.bicep' = {
  scope: rg
  name: 'role-assignments-deployment'
  params: {
    principalId: identity.outputs.principalId
    foundryProjectId: foundry.outputs.aiProjectId
    searchId: search.outputs.searchId
    acrId: acr.outputs.acrId
    redisId: redis.outputs.redisId
  }
  dependsOn: [
    identity
    foundry
    search
    acr
    redis
  ]
}

output aksClusterName string = aks.outputs.clusterName
output acrLoginServer string = acr.outputs.loginServer
output foundryEndpoint string = foundry.outputs.foundryEndpoint
output foundryAiHubName string = foundry.outputs.aiHubName
output foundryAiProjectName string = foundry.outputs.aiProjectName
output foundryAiServicesEndpoint string = foundry.outputs.aiServicesEndpoint
output foundryAgentServiceEndpoint string = foundry.outputs.agentServiceEndpoint
output searchEndpoint string = search.outputs.endpoint
output redisHostname string = redis.outputs.hostname
output managedIdentityClientId string = identity.outputs.clientId
output apimGatewayUrl string = apim.outputs.apimGatewayUrl
output keyVaultName string = keyVault.outputs.keyVaultName
output keyVaultUri string = keyVault.outputs.keyVaultUri

