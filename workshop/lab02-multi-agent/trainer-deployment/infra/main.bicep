targetScope = 'resourceGroup'

@description('Azure region of the existing Container Apps environment.')
param location string = resourceGroup().location

@description('azd environment name used only for deterministic naming and tags.')
@minLength(2)
@maxLength(32)
param environmentName string

@description('Name of the existing Container Apps managed environment.')
param managedEnvironmentName string = 'cae-oceans-mcp-demo-clckvj'

@description('Name of the existing Azure Container Registry.')
param containerRegistryName string = 'acrmcpodjhd42rocw6g'

@description('Name of the new trainer-owned Careers MCP Container App.')
@minLength(2)
@maxLength(32)
param containerAppName string = 'ca-careers-job-mcp-workshop'

@description('Container image to apply. Keep the public bootstrap image only for the first provision.')
param containerImage string

@description('Shared event-scoped key required by the MCP and REST endpoints.')
@secure()
@minLength(32)
param careersMcpApiKey string

@description('Normal minimum replica count. Raise to two immediately before the event.')
@minValue(1)
@maxValue(2)
param minReplicas int = 1

@description('Maximum replica count for workshop bursts.')
@minValue(2)
@maxValue(10)
param maxReplicas int = 5

var mcpSecretName = 'careers-workshop-key'
var bootstrapImage = 'mcr.microsoft.com/dotnet/samples:aspnetapp'
var usesPrivateImage = containerImage != bootstrapImage
var acrPullRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)
var commonTags = {
  'azd-env-name': environmentName
  'azd-service-name': 'careers-job-mcp'
  workload: 'careers-job-fit-workshop'
  component: 'mcp-server'
  dataPolicy: 'public-job-snapshot-synthetic-resumes-only'
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: managedEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource careersMcp 'Microsoft.App/containerApps@2025-01-01' = {
  name: containerAppName
  location: location
  tags: commonTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: managedEnvironment.id
    configuration: {
      activeRevisionsMode: 'Multiple'
      registries: usesPrivateImage
        ? [
            {
              server: containerRegistry.properties.loginServer
              identity: 'system'
            }
          ]
        : []
      ingress: {
        external: true
        allowInsecure: false
        targetPort: 8080
        transport: 'auto'
      }
      secrets: [
        {
          name: mcpSecretName
          value: careersMcpApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'careers-job-mcp'
          image: containerImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'CAREERS_MCP_API_KEY'
              secretRef: mcpSecretName
            }
            {
              name: 'CAREERS_DB_PATH'
              value: '/app/data/careers-jobs.sqlite3'
            }
            {
              name: 'CAREERS_LOG_LEVEL'
              value: 'INFO'
            }
            {
              name: 'CAREERS_REQUEST_TIMEOUT_SECONDS'
              value: '10'
            }
          ]
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/'
                port: 8080
                scheme: 'HTTP'
              }
              initialDelaySeconds: 1
              periodSeconds: 2
              timeoutSeconds: 2
              failureThreshold: 30
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: 8080
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 30
              timeoutSeconds: 3
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: 8080
                scheme: 'HTTP'
              }
              initialDelaySeconds: 2
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 6
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                concurrentRequests: '25'
              }
            }
          }
        ]
      }
    }
  }
}

resource careersMcpAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, careersMcp.id, acrPullRoleDefinitionId)
  scope: containerRegistry
  properties: {
    roleDefinitionId: acrPullRoleDefinitionId
    principalId: careersMcp.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Allow the Careers job MCP Container App to pull its workshop image.'
  }
}

output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = resourceGroup().name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.name
output AZURE_CONTAINER_ENVIRONMENT_NAME string = managedEnvironment.name
output CAREERS_MCP_CONTAINER_APP_NAME string = careersMcp.name
output CAREERS_MCP_ENDPOINT string = 'https://${careersMcp.properties.configuration.ingress.fqdn}/mcp'
output SERVICE_CAREERS_JOB_MCP_NAME string = careersMcp.name
output SERVICE_CAREERS_JOB_MCP_URI string = 'https://${careersMcp.properties.configuration.ingress.fqdn}'
