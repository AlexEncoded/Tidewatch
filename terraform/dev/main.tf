locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    project     = var.project_name
    environment = var.environment
    owner       = var.owner
    managed_by  = "terraform"
  }
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_container_registry" "main" {
  name                = "${var.project_name}${var.environment}acr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.common_tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

module "network" {
  source = "../modules/network"

  name                   = "vnet-${local.name_prefix}"
  location               = azurerm_resource_group.main.location
  resource_group_name    = azurerm_resource_group.main.name
  address_space          = ["10.20.0.0/16"]
  aks_subnet_prefixes    = ["10.20.0.0/20"]
  postgres_subnet_prefixes = ["10.20.16.0/24"]
  tags                   = local.common_tags
}

module "postgres" {
  source = "../modules/postgres"

  name                   = "${var.project_name}-${var.environment}-postgres"
  database_name          = var.project_name
  administrator_login    = var.postgres_admin_login
  administrator_password = var.postgres_admin_password
  location               = azurerm_resource_group.main.location
  resource_group_name    = azurerm_resource_group.main.name
  delegated_subnet_id    = module.network.postgres_subnet_id
  virtual_network_id     = module.network.virtual_network_id
  tags                   = local.common_tags
}

module "aks" {
  source = "../modules/kubernetes"

  name                = "aks-${local.name_prefix}"
  dns_prefix          = local.name_prefix
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = module.network.aks_subnet_id
  node_count          = var.aks_node_count
  node_vm_size        = var.aks_node_vm_size
  tags                = local.common_tags
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = module.aks.kubelet_identity_object_id
}

module "key_vault" {
  source = "../modules/key-vault"

  name                = "kv-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  tags                = local.common_tags
}
