output "AZURE_RESOURCE_GROUP" {
  value       = azurerm_resource_group.this.name
  description = "The name of the Azure Resource Group."
}

output "AZURE_AI_FOUNDRY_NAME" {
  value       = module.ai_foundry.ai_foundry_name
  description = "The name of the Azure AI Services."
}

output "AZURE_AI_PROJECT_NAME" {
  value       = module.ai_foundry.ai_foundry_project_name["project_1"]
  description = "The name of the Azure AI Project."
}

output "AZURE_AI_PROJECT_ID" {
  value       = module.ai_foundry.ai_foundry_project_id["project_1"]
  description = "The ID of the Azure AI Project."
}

output "AZURE_AI_PROJECT_ENDPOINT" {
  value       = "https://${module.ai_foundry.ai_foundry_name}.services.ai.azure.com/projects/${module.ai_foundry.ai_foundry_project_name["project_1"]}"
  description = "The endpoint of the Azure AI Project."
}

output "AZURE_APPLICATION_INSIGHTS_NAME" {
  value       = azurerm_application_insights.this.name
  description = "The name of the Azure Application Insights."
}

output "MODEL_DEPLOYMENT_NAME" {
  value       = basename(module.ai_foundry.ai_model_deployment_ids["gpt-5-mini"])
  description = "The name of the deployed model."
}
