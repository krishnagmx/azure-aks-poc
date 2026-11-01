output "deployment" {
  description = "Non-secret settings consumed by scripts/deploy.sh."
  value = {
    resource_group = azurerm_resource_group.app.name
    cluster        = azurerm_kubernetes_cluster.app.name
    registry       = azurerm_container_registry.app.name
    image          = "${azurerm_container_registry.app.login_server}/app"
    storage_url    = azurerm_storage_account.app.primary_blob_endpoint
    client_id      = azurerm_user_assigned_identity.app.client_id
  }
}
