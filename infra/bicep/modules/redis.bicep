@description('Redis Cache Name')
param redisName string

@description('Location')
param location string = resourceGroup().location

@description('Tags')
param tags object = {}

resource redis 'Microsoft.Cache/redis@2024-03-01' = {
  name: redisName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'Standard'
      family: 'C'
      capacity: 1
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      'maxmemory-policy': 'volatile-lru'
    }
  }
}

output hostname string = redis.properties.hostName
output port int = redis.properties.sslPort
output redisId string = redis.id

