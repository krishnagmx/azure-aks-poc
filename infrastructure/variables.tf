variable "location" {
  type    = string
  default = "westus3"
}

variable "prefix" {
  type    = string
  default = "akspoc"
  validation {
    condition     = can(regex("^[a-z][a-z0-9]{2,12}$", var.prefix))
    error_message = "Use 3–13 lowercase letters/digits, starting with a letter."
  }
}

variable "node_size" {
  type    = string
  default = "Standard_D2s_v4"
}
