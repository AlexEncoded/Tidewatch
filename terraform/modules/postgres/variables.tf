variable "name" {
  description = "Globally unique PostgreSQL Flexible Server name."
  type        = string
}

variable "database_name" {
  description = "Application database name."
  type        = string
}

variable "administrator_login" {
  description = "PostgreSQL administrator login."
  type        = string
}

variable "administrator_password" {
  description = "PostgreSQL administrator password."
  type        = string
  sensitive   = true
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "resource_group_name" {
  description = "Resource Group containing PostgreSQL."
  type        = string
}

variable "delegated_subnet_id" {
  description = "Delegated PostgreSQL subnet resource ID."
  type        = string
}

variable "virtual_network_id" {
  description = "Virtual Network resource ID for the private DNS link."
  type        = string
}

variable "tags" {
  description = "Tags applied to database resources."
  type        = map(string)
  default     = {}
}
