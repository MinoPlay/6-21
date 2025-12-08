@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@description('Primary location for all resources')
param location string = 'northeurope'

@description('The name for the habit tracker web app')
param appName string = 'habit-tracker-${uniqueString(resourceGroup().id)}'

// Generate resource token for unique naming
var resourceToken = uniqueString(resourceGroup().id, location, environmentName)

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${resourceToken}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
  tags: {
    environment: environmentName
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${resourceToken}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
  tags: {
    environment: environmentName
  }
}

// App Service Plan (Free tier - Linux)
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: 'asp-${resourceToken}'
  location: location
  sku: {
    name: 'F1'  // Free tier
    tier: 'Free'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true  // Required for Linux
  }
  tags: {
    environment: environmentName
  }
}

// App Service (Python Web App)
resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appName
  location: location
  tags: {
    'azd-service-name': 'web'
    environment: environmentName
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.10'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appCommandLine: 'gunicorn --bind=0.0.0.0 --timeout 600 \'app:create_app()\''
      alwaysOn: false  // Not available in Free tier
      pythonVersion: '3.10'
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// App Service Configuration (App Settings)
resource appServiceConfig 'Microsoft.Web/sites/config@2023-01-01' = {
  name: 'appsettings'
  parent: appService
  properties: {
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
    ApplicationInsightsAgent_EXTENSION_VERSION: '~3'
    FLASK_ENV: 'production'
    SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
    ENABLE_ORYX_BUILD: 'true'
    SECRET_KEY: uniqueString(resourceGroup().id, appService.id)
  }
}

// Outputs
output webAppName string = appService.name
output webAppUri string = 'https://${appService.properties.defaultHostName}'
output applicationInsightsConnectionString string = appInsights.properties.ConnectionString
output resourceGroupName string = resourceGroup().name
output subscriptionId string = subscription().subscriptionId
