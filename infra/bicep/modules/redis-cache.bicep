// ============================================================================
// Azure Cache for Redis Module
// ============================================================================
// Provides a managed Redis cache for session storage and caching.

@description('Name of the Redis Cache')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags to apply to the resource')
param tags object = {}

@description('SKU for the Redis Cache')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

@description('Capacity (size) of the Redis Cache')
@minValue(0)
@maxValue(6)
param capacity int = 0

@description('Enable non-SSL port (not recommended)')
param enableNonSslPort bool = false

@description('Minimum TLS version')
@allowed(['1.0', '1.1', '1.2'])
param minimumTlsVersion string = '1.2'

// Azure Cache for Redis Resource
resource redisCache 'Microsoft.Cache/redis@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: sku
      family: sku == 'Premium' ? 'P' : 'C'
      capacity: capacity
    }
    enableNonSslPort: enableNonSslPort
    minimumTlsVersion: minimumTlsVersion
    redisConfiguration: {
      'maxmemory-policy': 'volatile-lru'
    }
    publicNetworkAccess: 'Enabled'
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Redis Cache resource ID')
output redisCacheId string = redisCache.id

@description('Redis Cache name')
output name string = redisCache.name

@description('Redis Cache hostname')
output hostname string = redisCache.properties.hostName

@description('Redis Cache SSL port')
output sslPort int = redisCache.properties.sslPort

@description('Redis Cache non-SSL port')
output port int = redisCache.properties.port

// Note: Primary key and connection string should be retrieved from Key Vault
// or using listKeys() at deployment time, not exposed as outputs

