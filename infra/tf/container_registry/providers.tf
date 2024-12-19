terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
  # If you want, you can set the Azure subscription ID here
  # Default is to use the subscription ID from the Azure CLI (az account show)
  # Note: Do not use the one below, it's just an example.
  # subscription_id = "a3bda3df-892c-4baa-949a-da2037bbb34d"
}
