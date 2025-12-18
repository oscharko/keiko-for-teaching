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

module openai 'modules/openai.bicep' = {
  scope: rg
  name: 'openai-deployment'
  params: {
    accountName: 'oai-${projectName}-${environment}'
    location: location
    tags: tags
  }
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

module roleAssignments 'modules/role-assignments.bicep' = {
  scope: rg
  name: 'role-assignments-deployment'
  params: {
    principalId: identity.outputs.principalId
    openaiId: openai.outputs.accountId
    searchId: search.outputs.searchId
    acrId: acr.outputs.acrId
    redisId: redis.outputs.redisId
  }
  dependsOn: [
    identity
    openai
    search
    acr
    redis
  ]
}

output aksClusterName string = aks.outputs.clusterName
output acrLoginServer string = acr.outputs.loginServer
output openaiEndpoint string = openai.outputs.endpoint
output searchEndpoint string = search.outputs.endpoint
output redisHostname string = redis.outputs.hostname
output managedIdentityClientId string = identity.outputs.clientId
output apimGatewayUrl string = apim.outputs.apimGatewayUrl

