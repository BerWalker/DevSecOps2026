output "instance_public_ip" {
  description = "Public IP of the server"
  value       = aws_instance.app.public_ip
}

output "app_url" {
  description = "PhishGuard URL after manually deploying the stack"
  value       = "http://${aws_instance.app.public_ip}:5000"
}

output "ssh_command" {
  description = "SSH command (adjust the .pem key path)"
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ec2-user@${aws_instance.app.public_ip}"
}
