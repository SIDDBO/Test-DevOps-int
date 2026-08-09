# Terraform - Infrastructure as Code

## Overview

Complete AWS infrastructure definition using Terraform for Kubernetes cluster setup on EC2.

## What Gets Created

### Network
- VPC (Virtual Private Cloud)
- Subnet with public IP assignment
- Internet Gateway for outbound access
- Route tables and associations
- Security groups with controlled access

### Compute
- EC2 t3.micro instance (free tier eligible)
- 30GB EBS volume (free tier max)
- Elastic IP for static public address
- CloudWatch monitoring enabled

### Security
- Security group with SSH, HTTP, HTTPS, and Kubernetes ports
- IAM roles and policies
- Private key pair for SSH access

### Kubernetes
- Bootstrap script via user-data
- Kubeadm cluster initialization
- Docker container runtime
- CNI setup (Flannel)
- Helm installation

## Prerequisites

```bash
# Install Terraform
brew install terraform  # macOS
# or download from https://www.terraform.io/downloads.html

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format

# Verify
terraform version
aws sts get-caller-identity
```

## Quick Start

### 1. Initialize

```bash
# Download required providers
terraform init

# Validate configuration
terraform validate
```

### 2. Plan

```bash
# Review what will be created
terraform plan -out=tfplan

# Expected output:
# Plan: 9 to add, 0 to change, 0 to destroy
```

### 3. Apply

```bash
# Create AWS resources
terraform apply tfplan

# Wait 5-10 minutes for resources to be created
```

### 4. Outputs

```bash
# Get connection information
terraform output

# Get specific output
terraform output instance_public_ip
terraform output ssh_command
```

## Configuration

### variables.tf

All input variables are defined here:

| Variable | Default | Purpose |
|----------|---------|---------|
| `aws_region` | us-east-1 | AWS region |
| `environment` | production | Environment name |
| `project_name` | task-app | Project identifier |
| `instance_type` | t3.micro | EC2 instance type |
| `root_volume_size` | 30 | EBS volume size (GB) |
| `allowed_ssh_cidr` | 0.0.0.0/0 | SSH access CIDR |

### terraform.tfvars

Create this file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

Example content:
```hcl
aws_region = "us-east-1"
environment = "production"
project_name = "task-app"
instance_type = "t3.micro"
root_volume_size = 30

# Restrict SSH for security
allowed_ssh_cidr = ["203.0.113.42/32"]  # Your IP
```

## File Organization

### main.tf
Core infrastructure:
- VPC and networking
- Security groups
- IAM roles
- EC2 instance
- Elastic IP

### variables.tf
Input variable definitions

### outputs.tf
Output values after creation:
- Instance IP
- Security group ID
- VPC ID
- SSH command

### user_data.sh
Initialization script that runs on EC2:
- System updates
- Docker installation
- Kubernetes installation
- Cluster initialization

## State Management

Terraform maintains state in:
```
terraform.tfstate       # Current state
terraform.tfstate.backup  # Previous state
.terraform.lock.hcl     # Provider versions
```

**⚠️ Never commit tfstate files to Git!**

### Remote State (Optional)

For team environments:

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key = "task-app/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Usage

### Create Everything

```bash
terraform apply
```

### Update Configuration

Edit `variables.tf` or `terraform.tfvars`, then:

```bash
terraform plan
terraform apply
```

### Scale Resources

Change `root_volume_size` in tfvars:

```hcl
root_volume_size = 50  # Increase from 30GB

terraform plan
terraform apply
```

### Destroy Everything

```bash
terraform destroy

# Confirm by typing "yes"
```

**⚠️ This will delete ALL resources!**

### Destroy Specific Resource

```bash
terraform destroy -target=aws_instance.k8s_master
```

## Accessing the Instance

### SSH Connection

```bash
# Using output command
ssh -i ~/.aws/keys/task-app-key.pem $(terraform output instance_public_ip | tr -d '"')

# Or manually
ssh -i ~/.aws/keys/task-app-key.pem ubuntu@<public-ip>
```

### Copy Kubeconfig

```bash
scp -i ~/.aws/keys/task-app-key.pem \
  ubuntu@$(terraform output instance_public_ip | tr -d '"'):/home/ubuntu/.kube/config \
  ~/.kube/config
```

## Monitoring

### Check Resource Status

```bash
# List all resources
terraform state list

# Show resource details
terraform state show aws_instance.k8s_master

# Check drift (differences from current AWS state)
terraform refresh
terraform plan
```

### View in AWS Console

1. EC2 > Instances - see running instance
2. VPC > Your VPCs - see network setup
3. Security Groups - see firewall rules
4. Elastic IPs - see public IP allocation

## Cost Estimation

```bash
# Estimate infrastructure cost
terraform plan -out=tfplan
# Check output for resource count

# AWS Free Tier (12 months):
# EC2 t3.micro: $0
# EBS 30GB: $0
# Data transfer: $0
# Total: $0/month
```

## Troubleshooting

### Authentication Failed

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Re-configure
aws configure
```

### Instance Stuck on "pending"

```bash
# Check AWS limits
aws ec2 describe-account-attributes \
  --attribute-names supported-platforms

# Check for errors
terraform show
```

### SSH Connection Refused

```bash
# Verify security group allows port 22
aws ec2 describe-security-groups \
  --group-ids <group-id>

# Verify EC2 instance is running
aws ec2 describe-instances \
  --instance-ids <instance-id>
```

### User Data Script Failed

```bash
# SSH into instance
ssh -i key.pem ubuntu@<ip>

# Check logs
tail -f /var/log/user-data.log

# Check cloud-init status
cloud-init status
```

## Security Best Practices

### SSH Access
```hcl
# Restrict to your IP instead of 0.0.0.0/0
allowed_ssh_cidr = ["YOUR_IP/32"]
```

### Secrets
```hcl
# Store sensitive data in AWS Secrets Manager
# Reference via:
data "aws_secretsmanager_secret" "db_password" {
  name = "rds-password"
}
```

### Encryption
```hcl
# Enable EBS encryption
resource "aws_ebs_encryption_by_default" "example" {
  enabled = true
}
```

## Advanced Topics

### Multiple Environments

Create separate tfvars files:
```bash
terraform.tfvars.dev
terraform.tfvars.prod
terraform.tfvars.staging
```

Use with:
```bash
terraform apply -var-file=terraform.tfvars.prod
```

### Workspace Separation

```bash
# Create workspace
terraform workspace new prod

# List workspaces
terraform workspace list

# Switch workspace
terraform workspace select prod

# Apply to specific workspace
terraform apply
```

### Auto-Approval

```bash
# Skip confirmation prompt (use with caution!)
terraform apply -auto-approve
```

## Cleanup

```bash
# Destroy all resources
terraform destroy

# Remove Terraform files (if starting over)
rm -rf .terraform/
rm terraform.tfstate*
```

## Additional Resources

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://terraform.io/docs/cloud/guides/recommended-practices.html)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
# Test-DevOps-int
