variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Resource name prefix"
  type        = string
  default     = "phishguard"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ssh_key_name" {
  description = "Name of an existing AWS key pair (created in the console or CLI)"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed for SSH (recommended: your IP/32)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
