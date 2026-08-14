output "server_id" {
  value       = azurerm_postgresql_flexible_server.main.id
  description = "PostgreSQL Flexible Server resource ID."
}

output "fully_qualified_domain_name" {
  value       = azurerm_postgresql_flexible_server.main.fqdn
  description = "Private PostgreSQL server hostname."
}

output "database_name" {
  value       = azurerm_postgresql_flexible_server_database.main.name
  description = "Application database name."
}
