// ============================================================================
// Azure Container Apps Environment Module
// ============================================================================
// Provides a managed environment for running containerized applications.

@description('Name of the Container Apps Environment')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags to apply to the resource')
param tags object = {}

@description('Log Analytics Workspace ID for logging')
param logAnalyticsWorkspaceId string

@description('Application Insights connection string')
@secure()
param appInsightsConnectionString string = ''

@description('Enable zone redundancy')
param zoneRedundant bool = false

@description('Workload profile type')
@allowed(['Consumption', 'D4', 'D8', 'D16', 'D32', 'E4', 'E8', 'E16', 'E32'])
param workloadProfileType string = 'Consumption'

// Get Log Analytics Workspace details
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: split(logAnalyticsWorkspaceId, '/')[8]
}

// Azure Container Apps Environment Resource
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    daprAIConnectionString: appInsightsConnectionString
    zoneRedundant: zoneRedundant
    workloadProfiles: workloadProfileType == 'Consumption' ? [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ] : [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
      {
        name: workloadProfileType
        workloadProfileType: workloadProfileType
        minimumCount: 1
        maximumCount: 3
      }
    ]
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Container Apps Environment resource ID')
output environmentId string = containerAppsEnv.id

@description('Container Apps Environment name')
output name string = containerAppsEnv.name

@description('Container Apps Environment default domain')
output defaultDomain string = containerAppsEnv.properties.defaultDomain

@description('Container Apps Environment static IP')
output staticIp string = containerAppsEnv.properties.staticIp

