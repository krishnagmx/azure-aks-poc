resource "random_string" "kv_suffix" {
  length  = 4
  special = false
  upper   = false
  keepers = {
    always = "constant"
  }
}

resource "azurerm_key_vault" "kv" {
  name                       = "${var.prefix}-kv-${random_string.kv_suffix.result}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  enable_rbac_authorization  = true
}

resource "azurerm_role_assignment" "kv_admin" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = var.object_id
}