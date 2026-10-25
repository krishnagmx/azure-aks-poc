variable "location" {
  default = "westus3"
}

variable "prefix" {
  default = "akspoc"
}

variable "postgres_admin_password" {
  sensitive = true
}