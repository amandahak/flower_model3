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
  # You may want to hard-code subscription ID here to avoid logging in
  # subscription_id = "a3bda3df-892c-4baa-949a-da2037bbb34d"
}
