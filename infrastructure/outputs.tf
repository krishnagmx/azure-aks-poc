output "resource_group_name" { value = azurerm_resource_group.rg.name }
output "acr_login_server"    { value = module.aks.acr_login_server }
output "acr_name"            { value = module.aks.acr_name }
output "aks_cluster_name"    { value = module.aks.cluster_name }
output "key_vault_name"      { value = module.keyvault.key_vault_name }
output "postgres_fqdn"       { value = module.database.fqdn }