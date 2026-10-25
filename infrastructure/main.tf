data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "rg" {
  name     = "${var.prefix}-rg"
  location = var.location
}

module "network" {
  source              = "./modules/network"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  prefix              = var.prefix
}

module "keyvault" {
  source              = "./modules/keyvault"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  prefix              = var.prefix
  tenant_id           = data.azurerm_client_config.current.tenant_id
  object_id           = data.azurerm_client_config.current.object_id
}

module "aks" {
  source              = "./modules/aks"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  prefix              = var.prefix
  subnet_id           = module.network.aks_subnet_id
  key_vault_id        = module.keyvault.key_vault_id
}

module "database" {
  source              = "./modules/database"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  prefix              = var.prefix
  subnet_id           = module.network.data_subnet_id
  vnet_id             = module.network.vnet_id
  admin_password      = var.postgres_admin_password
}