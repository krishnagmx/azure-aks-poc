resource "azurerm_monitor_diagnostic_setting" "appgw" {
  name                       = "appgw-diagnostics"
  target_resource_id         = module.appgw.appgw_id
  log_analytics_workspace_id = "/subscriptions/7480ede3-a872-4211-8c1e-f24d018ebbd6/resourceGroups/DefaultResourceGroup-USW3/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-7480ede3-a872-4211-8c1e-f24d018ebbd6-USW3"

  enabled_log {
    category = "ApplicationGatewayAccessLog"
  }

  enabled_log {
    category = "ApplicationGatewayPerformanceLog"
  }

  enabled_log {
    category = "ApplicationGatewayFirewallLog"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}
