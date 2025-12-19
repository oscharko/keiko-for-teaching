// ============================================================================
// Role Assignments Module for Keiko Teaching
// ============================================================================
// Assigns RBAC roles to the managed identity for accessing Azure resources.

@description('Principal ID of the managed identity')
param principalId string

@description('Storage Account name')
param storageAccountName string

@description('Key Vault name')
param keyVaultName string

@description('Container Registry name')
param containerRegistryName string

// Note: Azure AI Search role assignments are handled separately
// since the search service is in a different resource group

// Built-in Azure Role Definition IDs
var roles = {
  // Storage Blob Data Contributor
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  // Key Vault Secrets User
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  // AcrPull
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  // AcrPush
  acrPush: '8311e382-0749-4cb8-b61a-304f252e45ec'
}

// Reference existing resources
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: containerRegistryName
}

// ============================================================================
// Role Assignments
// ============================================================================

// Storage Blob Data Contributor for Storage Account
resource storageBlobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, principalId, roles.storageBlobDataContributor)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roles.storageBlobDataContributor
    )
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// Key Vault Secrets User for Key Vault
resource keyVaultSecretsRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, principalId, roles.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roles.keyVaultSecretsUser
    )
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// AcrPull for Container Registry
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, principalId, roles.acrPull)
  scope: containerRegistry
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roles.acrPull
    )
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Storage role assignment ID')
output storageRoleId string = storageBlobRole.id

@description('Key Vault role assignment ID')
output keyVaultRoleId string = keyVaultSecretsRole.id

@description('ACR role assignment ID')
output acrRoleId string = acrPullRole.id
