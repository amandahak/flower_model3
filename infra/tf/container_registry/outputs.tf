output "registry_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "registry_name" {
  value = azurerm_container_registry.acr.name
}

# Alternative would be to set the admin_enabled to true and output the username and password
# Having it set to false, and having the Standard SKU, we could use RBAC to manage the access to the registry
#
# We will not. We simply use the anonymous_pull_enabled==true
# We have no secrets in our Docker images, so we don't need to protect them

# output "registry_username" {
#   value = azurerm_container_registry.acr.admin_username
# }

# output "registry_password" {
#   value     = azurerm_container_registry.acr.admin_password
#   sensitive = true
# }
