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
