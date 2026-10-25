resource "random_string" "pg_suffix" {
  length  = 6
  special = false
  upper   = false
  keepers = {
    always = "constant"
  }
}

resource "azurerm_private_dns_zone" "pg" {
  name                = "${var.prefix}-pg.postgres.database.azure.com"
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_zone_virtual_network_link" "pg" {
  name                  = "pg-dns-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.pg.name
  virtual_network_id    = var.vnet_id
}

resource "azurerm_postgresql_flexible_server" "pg" {
  name                          = "${var.prefix}-pg-${random_string.pg_suffix.result}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  version                       = "16"
  delegated_subnet_id           = var.subnet_id
  private_dns_zone_id           = azurerm_private_dns_zone.pg.id
  administrator_login           = "pgadmin"
  administrator_password        = var.admin_password
  sku_name                      = "GP_Standard_D2s_v3" # Free tier SKU
  storage_mb                    = 32768
  backup_retention_days         = 7
  public_network_access_enabled = false

  depends_on = [azurerm_private_dns_zone_virtual_network_link.pg]
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = "appdb"
  server_id = azurerm_postgresql_flexible_server.pg.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}