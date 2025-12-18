// Azure Key Vault Module for Keiko for Teaching
// Provides secure secrets management with RBAC and network security

@description('Name of the Key Vault')
param keyVaultName string

@description('Location for the Key Vault')
param location string = resourceGroup().location

@description('SKU name for the Key Vault')
@allowed([
  'standard'
  'premium'
])
param skuName string = 'standard'

@description('Tenant ID for Azure AD')
param tenantId string = subscription().tenantId

@description('Enable soft delete')
param enableSoftDelete bool = true

@description('Soft delete retention in days')
@minValue(7)
@maxValue(90)
param softDeleteRetentionInDays int = 90

@description('Enable purge protection')
param enablePurgeProtection bool = true

@description('Enable RBAC authorization')
param enableRbacAuthorization bool = true

@description('Enable public network access')
param publicNetworkAccess string = 'Disabled'

@description('Allowed IP addresses for firewall')
param allowedIpAddresses array = []

@description('Virtual Network Subnet IDs for service endpoints')
param subnetIds array = []

@description('Managed Identity Principal ID for AKS')
param aksManagedIdentityPrincipalId string

@description('Additional principal IDs that need access')
param additionalPrincipalIds array = []

@description('Tags for the Key Vault')
param tags object = {}

// Key Vault Resource
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: skuName
    }
    enableSoftDelete: enableSoftDelete
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enablePurgeProtection: enablePurgeProtection
    enableRbacAuthorization: enableRbacAuthorization
    publicNetworkAccess: publicNetworkAccess
    
    // Network ACLs
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: publicNetworkAccess == 'Enabled' ? 'Allow' : 'Deny'
      ipRules: [for ip in allowedIpAddresses: {
        value: ip
      }]
      virtualNetworkRules: [for subnetId in subnetIds: {
        id: subnetId
        ignoreMissingVnetServiceEndpoint: false
      }]
    }

    // Access policies (only used if RBAC is disabled)
    accessPolicies: []
  }
}

// RBAC Role Assignments
// Key Vault Secrets Officer role for AKS Managed Identity
resource aksSecretsOfficerRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableRbacAuthorization) {
  name: guid(keyVault.id, aksManagedIdentityPrincipalId, 'Key Vault Secrets Officer')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7') // Key Vault Secrets Officer
    principalId: aksManagedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Key Vault Secrets User role for additional principals
resource additionalSecretsUserRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (principalId, i) in additionalPrincipalIds: if (enableRbacAuthorization) {
  name: guid(keyVault.id, principalId, 'Key Vault Secrets User', string(i))
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

// Diagnostic Settings for monitoring
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${keyVaultName}-diagnostics'
  scope: keyVault
  properties: {
    logs: [
      {
        category: 'AuditEvent'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
      {
        category: 'AzurePolicyEvaluationDetails'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
  }
}

// Outputs
@description('Key Vault resource ID')
output keyVaultId string = keyVault.id

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Key Vault tenant ID')
output tenantId string = keyVault.properties.tenantId

