targetScope = 'resourceGroup'

@description('Short lowercase application name used in resource names.')
param applicationName string = 'casloop'

@description('Deployment environment name.')
@allowed(['dev', 'test', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all regional resources.')
param location string = resourceGroup().location

@description('Foundry project resource ID receiving the agent caller role assignment.')
param foundryProjectResourceId string

var suffix = uniqueString(resourceGroup().id, applicationName, environment)
var foundrySegments = split(foundryProjectResourceId, '/')
var tags = {
  application: applicationName
  environment: environment
  managedBy: 'bicep'
  dataClassification: 'internal'
}

module observability 'modules/observability.bicep' = {
  name: 'observability'
  params: {
    name: '${applicationName}-${environment}'
    location: location
    tags: tags
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: take('st${applicationName}${environment}${suffix}', 24)
    location: location
    tags: tags
  }
}

module ingress 'modules/function-ingress.bicep' = {
  name: 'function-ingress'
  params: {
    name: '${applicationName}-${environment}-${suffix}'
    location: location
    storageAccountName: storage.outputs.name
    storageAccountId: storage.outputs.id
    queueName: storage.outputs.queueName
    applicationInsightsConnectionString: observability.outputs.connectionString
    tags: tags
  }
}

module foundryRbac 'modules/foundry-rbac.bicep' = {
  name: 'foundry-rbac'
  scope: resourceGroup(foundrySegments[2], foundrySegments[4])
  params: {
    accountName: foundrySegments[8]
    projectName: foundrySegments[10]
    principalId: ingress.outputs.principalId
  }
}

@description('System-assigned principal used by ingress for queue and Foundry access.')
output ingressPrincipalId string = ingress.outputs.principalId

@description('Ingress function resource ID.')
output ingressResourceId string = ingress.outputs.id
