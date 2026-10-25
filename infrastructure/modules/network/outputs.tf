output "vnet_id"        { value = azurerm_virtual_network.vnet.id }
output "aks_subnet_id"  { value = azurerm_subnet.aks.id }
output "data_subnet_id" { value = azurerm_subnet.data.id }