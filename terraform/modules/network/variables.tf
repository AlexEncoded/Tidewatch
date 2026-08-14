variable "name" {
  description = "Virtual Network name."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "resource_group_name" {
  description = "Resource Group containing the network."
  type        = string
}

variable "address_space" {
  description = "Virtual Network CIDR ranges."
  type        = list(string)
}

variable "aks_subnet_prefixes" {
  description = "CIDR ranges for AKS nodes and workloads."
  type        = list(string)
}

variable "postgres_subnet_prefixes" {
  description = "CIDR ranges reserved for PostgreSQL private access."
  type        = list(string)
}

variable "tags" {
  description = "Tags applied to network resources."
  type        = map(string)
  default     = {}
}
