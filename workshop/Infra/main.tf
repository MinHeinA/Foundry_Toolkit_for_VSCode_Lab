locals {
  base_name = "globalai"
  location  = "australiaeast"
}

data "azurerm_client_config" "current" {}

module "naming" {
  source  = "Azure/naming/azurerm"
  version = "0.4.3"

  suffix        = [local.base_name]
  unique-length = 5
}

resource "azurerm_resource_group" "this" {
  name     = module.naming.resource_group.name_unique
  location = local.location
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = module.naming.log_analytics_workspace.name_unique
  location            = local.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "this" {
  name                = module.naming.application_insights.name_unique
  location            = local.location
  resource_group_name = azurerm_resource_group.this.name
  workspace_id        = azurerm_log_analytics_workspace.this.id
  application_type    = "web"
}

module "ai_foundry" {
  source  = "Azure/avm-ptn-aiml-ai-foundry/azurerm"
  version = "0.11.2"

  base_name                  = local.base_name
  location                   = local.location
  resource_group_resource_id = azurerm_resource_group.this.id
  ai_foundry = {
    create_ai_agent_service       = false
    disable_local_auth            = true
    public_network_access_enabled = true
    name                          = module.naming.cognitive_account.name_unique
    managed_identities = {
      system_assigned = true
    }
    role_assignments = {
      foundry_owner_current_runner = {
        principal_id               = data.azurerm_client_config.current.object_id
        role_definition_id_or_name = "Foundry Owner"
      }
    }
  }
  ai_model_deployments = {
    "gpt-5.4-mini" = {
      name = "gpt-5.4-mini"
      model = {
        format  = "OpenAI"
        name    = "gpt-5.4-mini"
        version = "2026-03-17"
      }
      scale = {
        type     = "GlobalStandard"
        capacity = 1000 # One capacity unit equals 1,000 TPM.
      }
    }
  }
  ai_projects = {
    project_1 = {
      name                       = "project-1-${module.naming.cognitive_account.name_unique}"
      description                = "Project 1 of ${module.naming.cognitive_account.name_unique}"
      display_name               = "Project 1 of ${module.naming.cognitive_account.name_unique}"
      create_project_connections = false
    }
  }
  create_byor              = false
  create_private_endpoints = false
}

# The Foundry AVM does not currently expose the deployment-level service tier.
resource "azapi_update_resource" "gpt_5_4_mini_priority_processing" {
  type        = "Microsoft.CognitiveServices/accounts/deployments@2025-10-01-preview"
  resource_id = module.ai_foundry.ai_model_deployment_ids["gpt-5.4-mini"]

  body = {
    properties = {
      serviceTier = "Priority"
    }
  }
}

resource "azapi_resource" "app_insights_connection" {
  type      = "Microsoft.CognitiveServices/accounts/connections@2026-05-01"
  parent_id = module.ai_foundry.ai_foundry_id
  name      = "${azurerm_application_insights.this.name}-conn"

  body = {
    properties = {
      category      = "AppInsights"
      target        = azurerm_application_insights.this.id
      authType      = "ApiKey" # AAD not supported yet
      isSharedToAll = true
      credentials = {
        key = azurerm_application_insights.this.connection_string
      }
      metadata = {
        ApiType    = "Azure"
        ResourceId = azurerm_application_insights.this.id
      }
    }
  }
}

# Once terraform destroy command ran successfuly, 
# delete the soft deleted foundry from azure portal 
