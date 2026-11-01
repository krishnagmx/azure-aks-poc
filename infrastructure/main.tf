resource "azurerm_resource_group" "app" {
  name     = "${var.prefix}-rg"
  location = var.location
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_container_registry" "app" {
  name                = "${var.prefix}acr${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.app.name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = false
}

resource "azurerm_kubernetes_cluster" "app" {
  name                      = "${var.prefix}-aks"
  resource_group_name       = azurerm_resource_group.app.name
  location                  = var.location
  dns_prefix                = var.prefix
  sku_tier                  = "Free"
  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  default_node_pool {
    name                = "system"
    vm_size             = var.node_size
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 3
    upgrade_settings {
      max_surge = "1"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    pod_cidr            = "10.244.0.0/16"
    service_cidr        = "172.16.0.0/16"
    dns_service_ip      = "172.16.0.10"
  }
}

resource "azurerm_role_assignment" "pull" {
  scope                            = azurerm_container_registry.app.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_kubernetes_cluster.app.kubelet_identity[0].object_id
  skip_service_principal_aad_check = true
}

resource "azurerm_storage_account" "app" {
  name                            = "${var.prefix}sa${random_string.suffix.result}"
  resource_group_name             = azurerm_resource_group.app.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    delete_retention_policy {
      days = 7
    }
  }
}

resource "azurerm_storage_container" "app" {
  name                  = "app-data"
  storage_account_name  = azurerm_storage_account.app.name
  container_access_type = "private"
}

resource "azurerm_user_assigned_identity" "app" {
  name                = "${var.prefix}-app"
  resource_group_name = azurerm_resource_group.app.name
  location            = var.location
}

resource "azurerm_federated_identity_credential" "app" {
  name                = "aks-app"
  resource_group_name = azurerm_resource_group.app.name
  parent_id           = azurerm_user_assigned_identity.app.id
  issuer              = azurerm_kubernetes_cluster.app.oidc_issuer_url
  audience            = ["api://AzureADTokenExchange"]
  subject             = "system:serviceaccount:poc-app:app"
}

resource "azurerm_role_assignment" "blob" {
  scope                            = "${azurerm_storage_account.app.id}/blobServices/default/containers/${azurerm_storage_container.app.name}"
  role_definition_name             = "Storage Blob Data Contributor"
  principal_id                     = azurerm_user_assigned_identity.app.principal_id
  skip_service_principal_aad_check = true
}
