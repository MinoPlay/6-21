# GitHub Actions Deployment Guide

This repository includes automated deployment to Azure using GitHub Actions and Bicep Infrastructure as Code.

## Prerequisites

1. **Azure Subscription** - [Create free account](https://azure.microsoft.com/free/)
2. **GitHub Repository** - Your code is already in: https://github.com/MinoPlay/6-21
3. **Azure Service Principal** - For authentication

## Setup Steps

### 1. Create Azure Service Principal

Run these commands in Azure Cloud Shell or locally with Azure CLI:

```bash
# Set your subscription (if you have multiple)
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Create a service principal with Contributor role
az ad sp create-for-rbac \
  --name "github-habit-tracker" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth
```

This will output JSON like:
```json
{
  "clientId": "xxx",
  "clientSecret": "xxx",
  "subscriptionId": "xxx",
  "tenantId": "xxx",
  ...
}
```

### 2. Configure GitHub Secrets

Go to your repository: https://github.com/MinoPlay/6-21/settings/secrets/actions

Click **New repository secret** and add these three secrets:

| Secret Name | Value | Where to find it |
|------------|-------|------------------|
| `AZURE_CLIENT_ID` | The `clientId` from JSON output | Service principal output |
| `AZURE_TENANT_ID` | The `tenantId` from JSON output | Service principal output |
| `AZURE_SUBSCRIPTION_ID` | The `subscriptionId` from JSON output | Service principal output |

**Note:** For newer GitHub Actions Azure login (OpenID Connect), you only need these 3 secrets, not the full JSON.

### 3. Configure Federated Identity (Recommended - More Secure)

Instead of using client secret, use OpenID Connect:

```bash
# Get your Service Principal Object ID
SP_OBJECT_ID=$(az ad sp list --display-name "github-habit-tracker" --query "[0].id" -o tsv)

# Create federated credential for main branch
az ad app federated-credential create \
  --id $SP_OBJECT_ID \
  --parameters '{
    "name": "github-main-branch",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:MinoPlay/6-21:ref:refs/heads/master",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

## Deployment Workflows

### Workflow 1: Full Deployment (Infrastructure + App)

**File:** `.github/workflows/azure-deploy.yml`

**Triggers:**
- Push to `master` branch
- Manual trigger via GitHub Actions UI

**What it does:**
1. Builds Python application
2. Deploys Azure infrastructure (Resource Group, App Service, App Insights, etc.)
3. Deploys application code to Azure Web App

**To run manually:**
1. Go to: https://github.com/MinoPlay/6-21/actions
2. Click "Deploy Habit Tracker to Azure"
3. Click "Run workflow" → "Run workflow"

### Workflow 2: Deploy App Only

**File:** `.github/workflows/deploy-webapp-only.yml`

**Triggers:**
- Manual only (workflow_dispatch)

**What it does:**
1. Builds Python application
2. Deploys ONLY the app code (no infrastructure changes)

**To run:**
1. Go to: https://github.com/MinoPlay/6-21/actions
2. Click "Deploy Web App Only"
3. Click "Run workflow"
4. Enter your existing web app name (e.g., `habit-tracker-abc123`)
5. Click "Run workflow"

## Infrastructure Details

### Bicep Template (`infra/main.bicep`)

Creates these Azure resources:

| Resource | Type | SKU/Tier | Purpose |
|----------|------|----------|---------|
| Log Analytics Workspace | `Microsoft.OperationalInsights/workspaces` | PerGB2018 | Centralized logging |
| Application Insights | `Microsoft.Insights/components` | Standard | Application monitoring |
| App Service Plan | `Microsoft.Web/serverfarms` | F1 (Free) | Hosting plan for web app |
| App Service | `Microsoft.Web/sites` | Linux, Python 3.10 | Web application host |

**Naming Convention:**
- Resource names use `uniqueString()` for global uniqueness
- Format: `{type}-{resourceToken}` (e.g., `asp-abc123xyz`)
- Web app name: `habit-tracker-{uniqueString}`

**App Settings Configured:**
- `APPLICATIONINSIGHTS_CONNECTION_STRING` - For monitoring
- `FLASK_ENV` - Set to `production`
- `SCM_DO_BUILD_DURING_DEPLOYMENT` - Enables Oryx build
- `SECRET_KEY` - Auto-generated secure key

### Resource Group

- Name: `rg-habit-tracker`
- Location: `eastus` (configurable in workflow)

## Customization

### Change Azure Region

Edit `.github/workflows/azure-deploy.yml`:

```yaml
env:
  AZURE_LOCATION: westeurope  # Change from eastus
```

### Change Resource Group Name

Edit both workflow files:

```yaml
env:
  AZURE_RESOURCE_GROUP: my-custom-rg-name
```

### Upgrade to Paid Tier

Edit `infra/main.bicep`:

```bicep
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: 'asp-${resourceToken}'
  location: location
  sku: {
    name: 'B1'  // Change from F1
    tier: 'Basic'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}
```

Then set `alwaysOn: true` in the App Service config.

### Add Custom Domain

Edit `infra/main.bicep` to add:

```bicep
resource customDomain 'Microsoft.Web/sites/hostNameBindings@2023-01-01' = {
  name: 'www.yourdomain.com'
  parent: appService
  properties: {
    siteName: appService.name
    hostNameType: 'Verified'
  }
}
```

## Monitoring and Troubleshooting

### View Deployment Logs

1. Go to: https://github.com/MinoPlay/6-21/actions
2. Click on a workflow run
3. Click on a job (e.g., "deploy-infrastructure")
4. Expand steps to see detailed logs

### View Application Logs in Azure

```bash
# Stream live logs
az webapp log tail --name YOUR_WEBAPP_NAME --resource-group rg-habit-tracker

# Download log files
az webapp log download --name YOUR_WEBAPP_NAME --resource-group rg-habit-tracker
```

### View in Azure Portal

After deployment, the workflow outputs a link to Azure Portal:
```
https://portal.azure.com/#@/resource/subscriptions/{sub-id}/resourceGroups/rg-habit-tracker/providers/Microsoft.Web/sites/{app-name}
```

### Common Issues

**Authentication Failed:**
- Verify GitHub secrets are set correctly
- Check service principal has Contributor role
- Ensure subscription ID is correct

**Deployment Failed:**
- Check that `requirements.txt` includes `gunicorn`
- Verify Python version matches (3.10)
- Check Azure quota limits (Free tier allows 10 apps per subscription)

**App Not Starting:**
- Check startup command in `main.bicep`
- Verify all dependencies are in `requirements.txt`
- Check Application Insights logs for errors

## Cost Estimate

**Free Tier (F1):**
- Cost: **$0/month**
- Limitations:
  - 60 minutes compute per day
  - 1 GB disk space
  - Apps sleep after 20 min inactivity
  - No custom domains
  - No auto-scaling

**Basic Tier (B1):**
- Cost: **~$13/month**
- Benefits:
  - Always on (no sleep)
  - Custom domains
  - 1.75 GB RAM
  - 10 GB storage

**Application Insights:**
- First 5 GB/month: Free
- Additional: $2.30/GB
- Expected for personal use: < $1/month

## Cleanup

### Delete Everything

```bash
# Delete resource group and all resources
az group delete --name rg-habit-tracker --yes --no-wait
```

### Delete Just the App (Keep Infrastructure)

```bash
# Delete only the web app
az webapp delete --name YOUR_WEBAPP_NAME --resource-group rg-habit-tracker
```

## CI/CD Flow Diagram

```
┌─────────────────┐
│  Git Push to    │
│  master branch  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Job      │
│  - Setup Python │
│  - Install deps │
│  - Create pkg   │
│  - Upload       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deploy Infra   │
│  - Login Azure  │
│  - Create RG    │
│  - Deploy Bicep │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deploy App     │
│  - Download pkg │
│  - Deploy code  │
│  - Output URL   │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │  Live! │
    └────────┘
```

## Next Steps

1. **Set up GitHub Secrets** (Step 2 above)
2. **Push to master branch** or run workflow manually
3. **Wait 5-10 minutes** for deployment
4. **Access your app** at the URL provided in workflow output
5. **Add to phone home screen** for PWA experience

Your habit tracker will be automatically deployed every time you push to master! 🚀
