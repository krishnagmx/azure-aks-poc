terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "azureakspocstate"  # Change to the name from Step 6
    container_name       = "tfstate"
    key                  = "aks-poc.tfstate"
  }
}