provider "azurerm" {
  features {
    resource_group {
      # POC-only: lets `terraform destroy` clean up even if a resource
      # was added manually outside Terraform. Remove for production.
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      # POC-only: purge on destroy so repeated test runs can reuse the same
      # key vault name without waiting out the soft-delete retention window.
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

provider "azapi" {
}

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}