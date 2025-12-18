@description('User Assigned Managed Identity Name')
param identityName string

@description('Location')
param location string = resourceGroup().location

@description('Tags')
param tags object = {}

// Create User Assigned Managed Identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: tags
}

// Output the identity details
output identityId string = managedIdentity.id
output principalId string = managedIdentity.properties.principalId
output clientId string = managedIdentity.properties.clientId
output identityName string = managedIdentity.name

