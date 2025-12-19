// ============================================================================
// Key Vault Secrets Module
// ============================================================================
// Creates secrets in an existing Key Vault

@description('Name of the Key Vault')
param keyVaultName string

@description('Redis Cache name')
param redisCacheName string

// Reference to existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Reference to existing Redis Cache
resource redisCache 'Microsoft.Cache/redis@2024-03-01' existing = {
  name: redisCacheName
}

// Redis password secret
resource redisPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'redis-password'
  properties: {
    value: redisCache.listKeys().primaryKey
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Redis password secret URI')
output redisPasswordSecretUri string = redisPasswordSecret.properties.secretUri

