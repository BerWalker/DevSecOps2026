#!/bin/bash
set -euo pipefail

dnf update -y
dnf install -y docker docker-compose-plugin git
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

mkdir -p /opt/${project_name}
chown ec2-user:ec2-user /opt/${project_name}

echo "Docker installed. Clone the repo to /opt/${project_name} and run: docker compose up -d --build"
