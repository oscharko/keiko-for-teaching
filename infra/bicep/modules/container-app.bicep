// ============================================================================
// Azure Container App Module
// ============================================================================
// Deploys a containerized application to Azure Container Apps.

@description('Name of the Container App')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags to apply to the resource')
param tags object = {}

@description('Container Apps Environment ID')
param containerAppsEnvId string

@description('Container Registry name')
param containerRegistryName string

@description('User-Assigned Managed Identity ID')
param managedIdentityId string

@description('Container image name (without registry)')
param imageName string

@description('Container image tag')
param imageTag string = 'latest'

@description('Target port for the container')
param targetPort int = 8080

@description('Whether the app is externally accessible')
param isExternal bool = false

@description('CPU allocation (e.g., 0.5, 1, 2)')
param cpu string = '0.5'

@description('Memory allocation (e.g., 1Gi, 2Gi)')
param memory string = '1Gi'

@description('Minimum number of replicas')
@minValue(0)
@maxValue(30)
param minReplicas int = 1

@description('Maximum number of replicas')
@minValue(1)
@maxValue(30)
param maxReplicas int = 3

@description('Environment variables for the container')
param envVars array = []

@description('Secrets for the container (Key Vault references)')
param secrets array = []

@description('Transport protocol (auto, http, http2)')
@allowed(['auto', 'http', 'http2'])
param transportProtocol string = 'auto'

@description('Workload profile name')
param workloadProfileName string = 'Consumption'

// Reference Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: containerRegistryName
}

// Build secrets array with Key Vault references
var secretsConfig = [for secret in secrets: {
  name: secret.name
  keyVaultUrl: secret.keyVaultSecretUri
  identity: managedIdentityId
}]

// Build environment variables from secrets
var secretEnvVars = [for secret in secrets: {
  name: replace(toUpper(replace(secret.name, '-', '_')), ' ', '_')
  secretRef: secret.name
}]

// Combine environment variables (use union for merging)
var allEnvVars = union(envVars, secretEnvVars)

// Azure Container App Resource
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvId
    workloadProfileName: workloadProfileName
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: isExternal
        targetPort: targetPort
        transport: transportProtocol
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
        corsPolicy: isExternal ? {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          maxAge: 86400
        } : null
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: managedIdentityId
        }
      ]
      secrets: secretsConfig
    }
    template: {
      containers: [
        {
          name: imageName
          image: '${containerRegistry.properties.loginServer}/${imageName}:${imageTag}'
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: allEnvVars
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: targetPort
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: targetPort
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Container App resource ID')
output containerAppId string = containerApp.id

@description('Container App name')
output name string = containerApp.name

@description('Container App FQDN')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Container App latest revision name')
output latestRevisionName string = containerApp.properties.latestRevisionName

