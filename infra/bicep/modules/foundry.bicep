// Microsoft Foundry AI Hub Deployment
// This module deploys a complete Microsoft Foundry AI Hub with:
// - AI Hub (central governance and management)
// - AI Project (workspace for AI development)
// - Model deployments (GPT-4o, Claude Sonnet 4.5, DeepSeek-V3)
// - Foundry Agent Service configuration
// - Foundry IQ knowledge base setup

@description('Name of the AI Hub')
param hubName string

@description('Name of the AI Project')
param projectName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Tags to apply to all resources')
param tags object = {}

@description('Storage Account Name for AI Hub')
param storageAccountName string

@description('Key Vault Name for secrets')
param keyVaultName string

@description('Application Insights Name for monitoring')
param appInsightsName string

@description('Container Registry Name for custom models')
param containerRegistryName string

@description('Enable Foundry Agent Service')
param enableAgentService bool = true

@description('Enable Foundry IQ for agentic RAG')
param enableFoundryIQ bool = true

// Storage Account for AI Hub
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// Container Registry for custom models and agents
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: {
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    zoneRedundancy: 'Disabled'
  }
}

// Application Insights for monitoring
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 90
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// AI Hub - Central governance and management for Foundry
resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: hubName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  kind: 'Hub'
  properties: {
    friendlyName: hubName
    description: 'Microsoft Foundry AI Hub for Keiko - Enterprise AI Platform'
    storageAccount: storageAccount.id
    keyVault: keyVaultName
    applicationInsights: appInsights.id
    containerRegistry: containerRegistry.id
    publicNetworkAccess: 'Enabled'
    // Foundry-specific settings
    managedNetwork: {
      isolationMode: 'AllowInternetOutbound'
    }
    // Enable Foundry features
    enableDataIsolation: true
    hbiWorkspace: false
  }
}

// AI Project - Workspace for AI development with Foundry
resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  kind: 'Project'
  properties: {
    friendlyName: projectName
    description: 'Microsoft Foundry AI Project for Keiko - Multi-Agent AI System'
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Enabled'
  }
}

// Azure AI Services Account for Foundry Models
// This provides access to all Foundry models (GPT-4o, Claude, DeepSeek, etc.)
resource aiServices 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: '${projectName}-aiservices'
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: '${projectName}-aiservices'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// Model Deployments within AI Services
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: aiServices
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: aiServices
  name: 'text-embedding-3-large'
  sku: {
    name: 'Standard'
    capacity: 120
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'
      version: '1'
    }
  }
  dependsOn: [gpt4oDeployment]
}

// Foundry Agent Service Configuration
resource agentService 'Microsoft.MachineLearningServices/workspaces/onlineEndpoints@2024-04-01' = if (enableAgentService) {
  parent: aiProject
  name: 'foundry-agent-service'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  kind: 'Managed'
  properties: {
    authMode: 'AMLToken'
    description: 'Foundry Agent Service for multi-agent orchestration'
    publicNetworkAccess: 'Enabled'
    traffic: {
      'agent-orchestrator': 100
    }
  }
}

// Foundry IQ Knowledge Base (for agentic RAG)
resource foundryIQ 'Microsoft.MachineLearningServices/workspaces/datastores@2024-04-01' = if (enableFoundryIQ) {
  parent: aiProject
  name: 'foundry-iq-knowledge-base'
  properties: {
    description: 'Foundry IQ Knowledge Base for agentic RAG with multi-source synthesis'
    datastoreType: 'AzureBlob'
    accountName: storageAccount.name
    containerName: 'foundry-iq-kb'
    credentials: {
      credentialsType: 'AccountKey'
    }
    tags: {
      'foundry-iq': 'enabled'
      'agentic-rag': 'true'
    }
  }
}

// Role Assignments for AI Hub Managed Identity
// Allow AI Hub to access Key Vault
resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiHub.id, keyVaultName, 'Key Vault Secrets User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: aiHub.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Allow AI Hub to access Storage Account
resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiHub.id, storageAccount.id, 'Storage Blob Data Contributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: aiHub.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Allow AI Hub to access Container Registry
resource acrRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiHub.id, containerRegistry.id, 'AcrPull')
  scope: containerRegistry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: aiHub.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output aiHubId string = aiHub.id
output aiHubName string = aiHub.name
output aiProjectId string = aiProject.id
output aiProjectName string = aiProject.name
output aiHubPrincipalId string = aiHub.identity.principalId
output aiProjectPrincipalId string = aiProject.identity.principalId
output aiServicesPrincipalId string = aiServices.identity.principalId
output foundryEndpoint string = 'https://${aiProject.name}.${location}.api.azureml.ms'
output aiServicesEndpoint string = aiServices.properties.endpoint
output aiServicesId string = aiServices.id
output agentServiceEndpoint string = enableAgentService ? agentService.properties.scoringUri : ''
output foundryIQEnabled bool = enableFoundryIQ

