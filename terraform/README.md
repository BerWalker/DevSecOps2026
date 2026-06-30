# Terraform — AWS (PhishGuard)

Minimal AWS infrastructure:

- VPC with a public subnet
- Security group (SSH, HTTP :80, gateway :5000)
- EC2 Amazon Linux 2023 with Docker

## Prerequisites

| Tool | Purpose |
|------|---------|
| [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.0 | IaC |
| [AWS CLI](https://aws.amazon.com/cli/) | Credentials |
| AWS key pair | SSH to EC2 |

Configure AWS credentials (one of):

```powershell
aws configure
# or AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars
```

Create a key pair in AWS (if you do not have one):

```powershell
aws ec2 create-key-pair --key-name my-aws-key --query 'KeyMaterial' --output text > my-aws-key.pem
```

## Usage

```powershell
cd terraform
Copy-Item terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — especially ssh_key_name and allowed_ssh_cidr

terraform init
terraform plan
terraform apply
```

After `apply`, note the public IP:

```powershell
terraform output app_url
```

## Deploy the app on EC2

```powershell
ssh -i my-aws-key.pem ec2-user@<PUBLIC_IP>
sudo git clone https://github.com/YOUR_USER/devsecops2026.git /opt/phishguard
cd /opt/phishguard
cp .env.example .env
# Edit .env (JWT, INTERNAL_API_KEY, etc.)
docker compose up -d --build
```

Open: `http://<PUBLIC_IP>:5000`

## Destroy resources

```powershell
terraform destroy
```

> State is stored locally (`terraform.tfstate`). Do not commit that file.
