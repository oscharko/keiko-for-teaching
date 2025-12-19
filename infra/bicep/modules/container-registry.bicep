// ============================================================================
// Azure Container Registry Module
// ============================================================================
// Provides a private Docker registry for container images.

@description('Name of the Container Registry (must be globally unique)')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags to apply to the resource')
param tags object = {}

@description('SKU for the Container Registry')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

@description('Enable admin user for the registry')
param adminUserEnabled bool = false

@description('Enable public network access')
param publicNetworkAccess string = 'Enabled'

// Azure Container Registry Resource
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: adminUserEnabled
    publicNetworkAccess: publicNetworkAccess
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 7
        status: sku == 'Premium' ? 'enabled' : 'disabled'
      }
    }
    encryption: {
      status: 'disabled'
    }
    dataEndpointEnabled: false
    networkRuleBypassOptions: 'AzureServices'
    zoneRedundancy: sku == 'Premium' ? 'Enabled' : 'Disabled'
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Container Registry resource ID')
output registryId string = containerRegistry.id

@description('Container Registry name')
output name string = containerRegistry.name

@description('Container Registry login server')
output loginServer string = containerRegistry.properties.loginServer

