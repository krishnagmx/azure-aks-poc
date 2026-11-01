terraform {
  backend "azurerm" {
    container_name = "tfstate"
    key            = "aks-poc.tfstate"
  }
}
