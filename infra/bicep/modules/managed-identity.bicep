// ============================================================================
// User-Assigned Managed Identity Module
// ============================================================================
// Provides a managed identity for Azure services to authenticate securely.

@description('Name of the Managed Identity')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags to apply to the resource')
param tags object = {}

// User-Assigned Managed Identity Resource
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

// ============================================================================
// Outputs
// ============================================================================

@description('Managed Identity resource ID')
output identityId string = managedIdentity.id

@description('Managed Identity principal ID (object ID)')
output principalId string = managedIdentity.properties.principalId

@description('Managed Identity client ID (application ID)')
output clientId string = managedIdentity.properties.clientId

@description('Managed Identity name')
output name string = managedIdentity.name

@description('Managed Identity tenant ID')
output tenantId string = managedIdentity.properties.tenantId

