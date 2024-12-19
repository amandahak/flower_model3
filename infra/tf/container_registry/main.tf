resource "azurerm_resource_group" "acr" {
  name     = "rg-${var.identifier}-${var.course_short_name}-acr"
  location = var.resource_group_location
}

resource "azurerm_container_registry" "acr" {
  name                   = "cr${var.identifier}${var.course_short_name}"
  resource_group_name    = azurerm_resource_group.acr.name
  location               = azurerm_resource_group.acr.location
  sku                    = "Standard"
  admin_enabled          = false
  anonymous_pull_enabled = true

  tags = var.default_tags
}
