resource "azurerm_resource_group" "olearn" {
  location = var.resource_group_location
  name     = "rg-${var.identifier}-${var.course_short_name}"

  tags = var.default_tags
}

resource "azurerm_storage_account" "olearn" {
  name                     = "sa${var.identifier}${var.course_short_name}"
  resource_group_name      = azurerm_resource_group.olearn.name
  location                 = azurerm_resource_group.olearn.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = var.default_tags
}

# Add storage container to store files
resource "azurerm_storage_container" "olearn" {
  name                  = "st-${var.identifier}-${var.course_short_name}"
  storage_account_name  = azurerm_storage_account.olearn.name
  container_access_type = "private"
}

# Add storage queue to store messages
resource "azurerm_storage_queue" "olearn" {
  name                 = "sq-${var.identifier}-${var.course_short_name}"
  storage_account_name = azurerm_storage_account.olearn.name
}

# TODO: Upload the base model
resource "azurerm_storage_blob" "model" {
  name                   = "models/model_1.keras"
  storage_account_name   = azurerm_storage_account.olearn.name
  storage_container_name = azurerm_storage_container.olearn.name
  type                   = "Block"
  source                 = "../../../src/azurite_populate/model_1.keras"
}

# Upload validation data
resource "azurerm_storage_blob" "val_data" {
  name                   = "datasets/val_data.zip"
  storage_account_name   = azurerm_storage_account.olearn.name
  storage_container_name = azurerm_storage_container.olearn.name
  type                   = "Block"
  source                 = "../../../src/azurite_populate/val_data.zip"
}

# # TODO: Upload the base model
# resource "azurerm_storage_blob" "dataset" {
#   name                   = "datasets/dataset.csv"
#   storage_account_name   = azurerm_storage_account.olearn.name
#   storage_container_name = azurerm_storage_container.olearn.name
#   type                   = "Block"
#   source                 = "../../../src/azurite_populate/dataset.csv"
# }

resource "azurerm_container_group" "olearn" {
  name                        = "ci-${var.identifier}-${var.course_short_name}"
  location                    = azurerm_resource_group.olearn.location
  resource_group_name         = azurerm_resource_group.olearn.name
  ip_address_type             = "Public"
  dns_name_label              = "aci-label"
  os_type                     = "Linux"
  restart_policy              = "OnFailure"
  sku                         = "Standard"
  dns_name_label_reuse_policy = "ResourceGroupReuse"

  depends_on = [azurerm_storage_blob.model, azurerm_storage_blob.val_data]

  identity {
    type = "SystemAssigned"
  }

  container {
    name   = "flowerui"
    image  = var.frontend_image
    cpu    = "1.0"
    memory = "1.0"
    ports {
      port     = 80
      protocol = "TCP"
    }

    environment_variables = {
      USE_AZURE_CREDENTIAL = var.use_azure_credential # Set to False to use connection string (below)
      STORAGE_ACCOUNT_NAME = azurerm_storage_account.olearn.name
      STORAGE_BLOB_URL     = azurerm_storage_account.olearn.primary_blob_endpoint
      STORAGE_QUEUE_URL    = azurerm_storage_account.olearn.primary_queue_endpoint
      STORAGE_CONTAINER    = azurerm_storage_container.olearn.name
      STORAGE_QUEUE        = azurerm_storage_queue.olearn.name
      PREDICT_URL    = "http://localhost:8888/predict"
    }

    # This is only needed if NOT using DefaultAzureCredential (SystemAssigned Identity)
    secure_environment_variables = {
      STORAGE_CONNECTION_STRING = var.use_azure_credential ? "" : azurerm_storage_account.olearn.primary_connection_string
    }
  }

  container {
    name   = "flowerpredict"
    image  = var.backend_image
    cpu    = "1.0"
    memory = "1.0"
    ports {
      port     = 8888
      protocol = "TCP"
    }

    environment_variables = {
      USE_AZURE_CREDENTIAL = var.use_azure_credential
      STORAGE_ACCOUNT_NAME = azurerm_storage_account.olearn.name
      STORAGE_BLOB_URL     = azurerm_storage_account.olearn.primary_blob_endpoint
      STORAGE_QUEUE_URL    = azurerm_storage_account.olearn.primary_queue_endpoint
      STORAGE_CONTAINER    = azurerm_storage_container.olearn.name
      STORAGE_QUEUE        = azurerm_storage_queue.olearn.name
    }

    # This is only needed if NOT using DefaultAzureCredential (SystemAssigned Identity)
    secure_environment_variables = {
      STORAGE_CONNECTION_STRING = var.use_azure_credential ? "" : azurerm_storage_account.olearn.primary_connection_string
    }
  }

  container {
    name   = "modeller"
    image  = var.modeller_image
    cpu    = "1.0"
    memory = "1.0"

    environment_variables = {
      USE_AZURE_CREDENTIAL = var.use_azure_credential
      STORAGE_ACCOUNT_NAME = azurerm_storage_account.olearn.name
      STORAGE_BLOB_URL     = azurerm_storage_account.olearn.primary_blob_endpoint
      STORAGE_QUEUE_URL    = azurerm_storage_account.olearn.primary_queue_endpoint
      STORAGE_CONTAINER    = azurerm_storage_container.olearn.name
      STORAGE_QUEUE        = azurerm_storage_queue.olearn.name
    }

    # This is only needed if NOT using DefaultAzureCredential (SystemAssigned Identity)
    secure_environment_variables = {
      STORAGE_CONNECTION_STRING = var.use_azure_credential ? "" : azurerm_storage_account.olearn.primary_connection_string
    }
  }

  tags = var.default_tags
}


# # Let's give the azurerm_container_group's identity access to the storage account
# resource "azurerm_role_assignment" "olearn_blob" {
#   scope                = azurerm_storage_account.olearn.id
#   role_definition_name = "Storage Blob Data Contributor"
#   principal_id         = azurerm_container_group.olearn.identity[0].principal_id
# }

# # Let's tive azurerm_container_group's identity access to the storage queue
# resource "azurerm_role_assignment" "olearn_queue" {
#   scope                = azurerm_storage_account.olearn.id
#   role_definition_name = "Storage Queue Data Contributor"
#   principal_id         = azurerm_container_group.olearn.identity[0].principal_id
# }
