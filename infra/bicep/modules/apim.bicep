@description('API Management Service Name')
param apimName string

@description('Location')
param location string = resourceGroup().location

@description('Tags')
param tags object = {}

@description('Publisher Email')
param publisherEmail string = 'admin@keiko.local'

@description('Publisher Name')
param publisherName string = 'Keiko'

@description('SKU Name')
@allowed(['Consumption', 'Developer', 'Basic', 'Standard', 'Premium'])
param skuName string = 'Developer'

@description('SKU Capacity')
param skuCapacity int = 1

// Create API Management Service
resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: apimName
  location: location
  tags: tags
  sku: {
    name: skuName
    capacity: skuCapacity
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Create API for Chat Service
resource chatApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'chat-api'
  properties: {
    displayName: 'Chat API'
    path: 'chat'
    protocols: ['https']
    subscriptionRequired: true
    serviceUrl: 'http://chat-service'
  }
}

// Create API for Search Service
resource searchApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'search-api'
  properties: {
    displayName: 'Search API'
    path: 'search'
    protocols: ['https']
    subscriptionRequired: true
    serviceUrl: 'http://search-service'
  }
}

// Create API for Document Service
resource documentApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'document-api'
  properties: {
    displayName: 'Document API'
    path: 'documents'
    protocols: ['https']
    subscriptionRequired: true
    serviceUrl: 'http://document-service'
  }
}

// Global Rate Limiting Policy
resource globalPolicy 'Microsoft.ApiManagement/service/policies@2023-05-01-preview' = {
  parent: apim
  name: 'policy'
  properties: {
    value: '''
      <policies>
        <inbound>
          <rate-limit calls="1000" renewal-period="60" />
          <quota calls="10000" renewal-period="86400" />
          <cors allow-credentials="true">
            <allowed-origins>
              <origin>*</origin>
            </allowed-origins>
            <allowed-methods>
              <method>GET</method>
              <method>POST</method>
              <method>PUT</method>
              <method>DELETE</method>
              <method>OPTIONS</method>
            </allowed-methods>
            <allowed-headers>
              <header>*</header>
            </allowed-headers>
          </cors>
        </inbound>
        <backend>
          <forward-request />
        </backend>
        <outbound />
        <on-error />
      </policies>
    '''
    format: 'xml'
  }
}

// Chat API Rate Limiting Policy
resource chatApiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  parent: chatApi
  name: 'policy'
  properties: {
    value: '''
      <policies>
        <inbound>
          <base />
          <rate-limit-by-key calls="100" renewal-period="60" counter-key="@(context.Request.IpAddress)" />
        </inbound>
        <backend>
          <base />
        </backend>
        <outbound>
          <base />
        </outbound>
        <on-error>
          <base />
        </on-error>
      </policies>
    '''
    format: 'xml'
  }
}

output apimId string = apim.id
output apimName string = apim.name
output apimGatewayUrl string = apim.properties.gatewayUrl
output apimPrincipalId string = apim.identity.principalId

