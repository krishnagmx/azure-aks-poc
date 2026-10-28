terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "krishnapocstate2026"
    container_name       = "tfstate"
    key                  = "aks-poc.tfstate"
  }
}