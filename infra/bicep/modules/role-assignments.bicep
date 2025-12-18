@description('Principal ID to assign roles to')
param principalId string

@description('Azure OpenAI Resource ID')
param openaiId string

@description('Azure AI Search Resource ID')
param searchId string

@description('Azure Container Registry Resource ID')
param acrId string

@description('Azure Redis Cache Resource ID')
param redisId string

// Built-in Azure Role Definition IDs
var cognitiveServicesOpenAIUserRole = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
var searchIndexDataContributorRole = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
var acrPullRole = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
var redisContributorRole = 'e0f68234-74aa-48ed-b826-c38b57376e17'

// Assign Cognitive Services OpenAI User role for Azure OpenAI
resource openaiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openaiId, principalId, cognitiveServicesOpenAIUserRole)
  scope: resourceId('Microsoft.CognitiveServices/accounts', split(openaiId, '/')[8])
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRole)
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

output openaiRoleAssignmentId string = openaiRoleAssignment.id
output searchRoleAssignmentId string = searchRoleAssignment.id
output acrRoleAssignmentId string = acrRoleAssignment.id
output redisRoleAssignmentId string = redisRoleAssignment.id

