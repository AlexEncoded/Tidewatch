output "key_vault_id" {
  value       = azurerm_key_vault.main.id
  description = "Key Vault resource ID."
}

output "key_vault_uri" {
  value       = azurerm_key_vault.main.vault_uri
  description = "Key Vault URI."
}
