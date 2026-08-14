variable "name" {
  description = "AKS cluster name."
  type        = string
}

variable "dns_prefix" {
  description = "DNS prefix for the AKS API server."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "resource_group_name" {
  description = "Resource Group containing AKS."
  type        = string
}

variable "subnet_id" {
  description = "Subnet used by AKS nodes."
  type        = string
}

variable "node_count" {
  description = "Initial number of system nodes."
  type        = number
  default     = 1
}

variable "node_vm_size" {
  description = "VM size for the system node pool."
  type        = string
  default     = "Standard_B2s"
}

variable "tags" {
  description = "Tags applied to AKS resources."
  type        = map(string)
  default     = {}
}
