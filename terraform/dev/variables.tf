variable "subscription_id" {
  description = "Azure subscription used by this environment."
  type        = string
  default     = null
  nullable    = true
}

variable "location" {
  description = "Azure region for development resources."
  type        = string
  default     = "westeurope"
}

variable "project_name" {
  description = "Short project name used in resource names and tags."
  type        = string
  default     = "tidewatch"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Owner tag for cost and responsibility tracking."
  type        = string
  default     = "tidewatch-team"
}

variable "postgres_admin_login" {
  description = "PostgreSQL administrator login."
  type        = string
  default     = "tidewatchadmin"
}

variable "postgres_admin_password" {
  description = "PostgreSQL administrator password. Store only in secure tfvars or CI secrets."
  type        = string
  sensitive   = true
  default     = null
  nullable    = true
}

variable "aks_node_count" {
  description = "Initial AKS system node count."
  type        = number
  default     = 1
}

variable "aks_node_vm_size" {
  description = "AKS system node VM size."
  type        = string
  default     = "Standard_B2s"
}

variable "workload_identity_namespace" {
  description = "Kubernetes namespace used by the API ServiceAccount."
  type        = string
  default     = "tidewatch-dev"
}

variable "workload_identity_service_account" {
  description = "Kubernetes ServiceAccount federated to the API identity."
  type        = string
  default     = "tidewatch-api"
}
