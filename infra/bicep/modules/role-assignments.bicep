@description('Principal ID to assign roles to')
param principalId string

@description('Microsoft Foundry AI Project Resource ID')
param foundryProjectId string

@description('Azure AI Search Resource ID')
param searchId string

@description('Azure Container Registry Resource ID')
param acrId string

@description('Azure Redis Cache Resource ID')
param redisId string

// Built-in Azure Role Definition IDs
var azureMLDataScientistRole = 'f6c7c914-8db3-469d-8ca1-694a8f32e121' // Azure ML Data Scientist (for Foundry)
var cognitiveServicesUserRole = 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User (for AI Services)
var searchIndexDataContributorRole = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
var acrPullRole = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
var redisContributorRole = 'e0f68234-74aa-48ed-b826-c38b57376e17'

// Assign Azure ML Data Scientist role for Foundry AI Project
resource foundryRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryProjectId, principalId, azureMLDataScientistRole)
  scope: resourceId('Microsoft.MachineLearningServices/workspaces', split(foundryProjectId, '/')[8])
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureMLDataScientistRole)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// Assign Cognitive Services User role for AI Services (Foundry models)
resource aiServicesRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryProjectId, principalId, cognitiveServicesUserRole)
  scope: resourceId('Microsoft.MachineLearningServices/workspaces', split(foundryProjectId, '/')[8])
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserRole)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// Assign Search Index Data Contributor role for Azure AI Search
resource searchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchId, principalId, searchIndexDataContributorRole)
  scope: resourceId('Microsoft.Search/searchServices', split(searchId, '/')[8])
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataContributorRole)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// Assign ACR Pull role for Azure Container Registry
resource acrRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acrId, principalId, acrPullRole)
  scope: resourceId('Microsoft.ContainerRegistry/registries', split(acrId, '/')[8])
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRole)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// Assign Redis Contributor role for Azure Cache for Redis
resource redisRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(redisId, principalId, redisContributorRole)
  scope: resourceId('Microsoft.Cache/redis', split(redisId, '/')[8])
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', redisContributorRole)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

output foundryRoleAssignmentId string = foundryRoleAssignment.id
output aiServicesRoleAssignmentId string = aiServicesRoleAssignment.id
output searchRoleAssignmentId string = searchRoleAssignment.id
output acrRoleAssignmentId string = acrRoleAssignment.id
output redisRoleAssignmentId string = redisRoleAssignment.id

