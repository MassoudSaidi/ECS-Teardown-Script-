# AWS Environment Configuration Guide

## 1. Overview

This guide provides step-by-step instructions for configuring your local AWS environment within the `my-project` directory to securely deploy and manage infrastructure. This project uses a local `.aws` folder to ensure its credentials and configuration are isolated and do not conflict with your global AWS settings.

We will establish two distinct AWS profiles:

- **default Profile (The Builder)**: A profile using your primary IAM user credentials. Its sole purpose is to run the Python script that creates and manages the custom IAM deployment role. It has the direct permissions needed to build the necessary IAM resources.

- **dev Profile (The Consumer)**: A profile that does not have its own credentials. Instead, it assumes the custom role created by the default profile. This profile will be used by Terraform to deploy and manage the main application infrastructure (ECS, ElastiCache, etc.). This ensures Terraform operates with limited, temporary permissions.

This separation of duties is a critical security measure that prevents long-term user credentials from being used for routine infrastructure tasks.

## 2. Initial Setup: Project-Local AWS Configuration

This project uses a dedicated `.aws` folder inside `my-project/`. To make the AWS CLI use these files instead of the default ones in your home directory, we must set specific environment variables in our terminal session.

### Step 2.1: Configure Credentials File

Navigate to the `my-project/.aws/` directory.

Create a file named `credentials` (with no file extension).

Open the file and paste the following content. Replace the placeholder values with the actual Access Key ID and Secret Access Key for your `bsup_assume_role_dev` IAM user.

This file is located at `my-project/.aws/credentials`
```ini
[default]  
aws_access_key_id = AKIAxxxxxxxxxxxxxxxx  
aws_secret_access_key = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Important**: The Secret Access Key should be pasted exactly as provided. Do not wrap it in quotes, even if it contains special characters like +.

### Step 2.2: Configure Config File

In the same `my-project/.aws/` directory, create a file named `config`.

Open the file and paste the following content. The `role_arn` must be exactly as shown, including the `/service-role/` path.

 This file is located at `my-project/.aws/config`
```ini
[default]  
region = ca-central-1  
output = json  

[profile dev]  
role_arn = arn:aws:iam::866134557891:role/service-role/dev2-terraform_deployer_role  
source_profile = default  
output = json  
region = ca-central-1
```
Save and close both files. Your local project environment is now configured.

## 3. Workflow: Activating the Local Configuration and Switching Profiles

For every new terminal session, you must first tell the AWS CLI where to find your local configuration files before you can select a profile.

### In PowerShell:
Navigate to the root of your project (my-project/)

```powershell
# Point to the local config and credentials files
$env:AWS_CONFIG_FILE = ".\.aws\config"
$env:AWS_SHARED_CREDENTIALS_FILE = ".\.aws\credentials"

# Set the active profile to the Builder (for Python script)
$env:AWS_PROFILE = "default"

# Set the active profile to the Consumer (for Terraform)
$env:AWS_PROFILE = "dev"
```

### In Command Prompt (CMD):
Navigate to the root of your project (my-project/)

```cmd
:: Point to the local config and credentials files
set AWS_CONFIG_FILE=.\.aws\config
set AWS_SHARED_CREDENTIALS_FILE=.\.aws\credentials

:: Set the active profile to the Builder (for Python script)
set AWS_PROFILE=default

:: Set the active profile to the Consumer (for Terraform)
set AWS_PROFILE=dev
```

**Note:** These environment variables are temporary and only last for the current terminal session. If you close your terminal, you must set them again.

### Create/Update the IAM Role: 
Before running Terraform, always ensure the deployment role is up-to-date.

Open a new terminal at the my-project root.

Activate the builder configuration:

**PowerShell:**

```powershell
$env:AWS_CONFIG_FILE = ".\.aws\config"
$env:AWS_SHARED_CREDENTIALS_FILE = ".\.aws\credentials"
$env:AWS_PROFILE = "default"
```

**CMD:**

```cmd
set AWS_CONFIG_FILE=.\.aws\config
set AWS_SHARED_CREDENTIALS_FILE=.\.aws\credentials
set AWS_PROFILE=default
```

Run the Python script from the directory: `python ./aws_config_roles/create_role.py`

### Deploy Infrastructure with Terraform: 
Once the role is ready, use it to run your Terraform commands.

AWS Authentication for Terraform
This Terraform solution is managed by Terragrunt and is pre-configured to use a specific AWS profile named `dev`for all deployment operations.
This approach is a security best practice. The dev profile does not use long-term user credentials. Instead, it securely assumes a temporary, permissions-limited IAM role (`dev2-terraform_deployer_role`) that is purpose-built for managing this infrastructure.
The profile is "hardcoded" within the terragrunt.hcl file in each deployment directory (e.g., `infrastructure/live/dev`, `infrastructure/bootstrap-git-actions` and `infrastructure/bootstrap-cognito`). This ensures that all deployments are consistent and secure by default.

```hcl
# Example from terragrunt.hcl

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region                   = "ca-central-1"
  profile                  = "dev" # <-- Hardcoded to use the 'dev' profile

  # The provider is also pointed to the project-local .aws folder
  shared_config_files      = ["${get_repo_root()}/.aws/config"]
  shared_credentials_files = ["${get_repo_root()}/.aws/credentials"]
}
EOF
}
```

### Your Local Setup Requirement
To use this solution, you only need to ensure your project-local .aws folder is correctly configured. Terragrunt handles the rest automatically.
The .aws folder must exist in the project root.
Your .aws/credentials file must contain the keys for the [default] profile.
Your .aws/config file must contain the definitions for [profile dev].

Navigate to the `terraform/` directory and run your commands: `terragrunt apply`, etc.


## 4. Verification and Debugging Toolkit

Before running these commands, ensure your terminal is correctly configured with the `AWS_..._FILE` and `AWS_PROFILE` environment variables as described above. This is the most important command to confirm which identity you are currently operating as.

### Verify the Builder (User):
First, set your session to use the default profile.

```Bash
aws sts get-caller-identity
```

**Expected Output:** 
```json
{
    "UserId": "XXXXXXXXXXXXXXXXXXXXXXXXX",
    "Account": "88888888888888",
    "Arn": "arn:aws:iam::866134557891:user/bsup_assume_role_dev"
}
```

### Verify the Consumer (Role):
First, set your session to use the dev profile.

```Bash
aws sts get-caller-identity
```

For simple tests you may switch to specific profiles by:
```bash
aws sts get-caller-identity --profile dev
```

**Expected Output:** 
```json
{
    "UserId": "AROA4TKNEQTBSODGRCTCR:botocore-session-1760546334",
    "Account": "866134557891",
    "Arn": "arn:aws:sts::866134557891:assumed-role/dev2-terraform_deployer_role/botocore-session-1760546334"
}
```

If you get an `AccessDenied` error when trying to use the dev profile, switch your terminal to use the default profile and run these diagnostic commands:

#### Check if the Role Exists:

```Bash
aws iam get-role --role-name dev2-terraform_deployer_role
```

**Debug Tip:** If this fails, the Python script did not run successfully.

#### Check if the Policy is Attached to the Role:

```Bash
aws iam list-attached-role-policies --role-name dev2-terraform_deployer_role
```

**Debug Tip:** If the output is empty, the Python script failed to attach the permissions policy.

### Advanced: Simulate the AssumeRole Action

This command will tell you exactly which policy is causing a denial.

```Bash
aws iam simulate-principal-policy ^
    --policy-source-arn arn:aws:iam::866134557891:user/bsup_assume_role_dev ^
    --action-names "sts:AssumeRole" ^
    --resource-arns "arn:aws:iam::866134557891:role/service-role/dev2-terraform_deployer_role"
```

**Debug Tip:** Look at the `EvalDecision` field in the output. It will explicitly state allowed or denied and reference the policy statement that caused the decision.