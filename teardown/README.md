# smart_nuke.py

## Overview
`smart_nuke.py` is a Python utility designed to **forcefully and safely tear down AWS ECS environments** that were deployed using Terraform/Terragrunt.  

In complex ECS stacks (clusters, services, load balancers, auto-scaling groups), a standard `terragrunt destroy` may fail due to dependency deadlocks or state drift. This script provides a **sequential, logic-driven cleanup process** to ensure that orphaned resources do not remain active and that future deployments succeed.

---

## Why is this script needed?
- **terragrunt destroy limitations**: terragrunt destroys resources in parallel based on dependency graphs. In ECS/VPC stacks, this can lead to deadlocks (e.g., ENIs still attached, Security Groups still in use).
- **Cost control**: Orphaned resources left running by failed destroys can continue to generate AWS costs.
- **Deployment reliability**: "Ghost" resources not tracked in state files can break future `terragrunt apply` commands.

---

## What the script does
- Reads the environment configuration dynamically using `terragrunt output -json`.
- Scales down ECS services to zero, draining tasks and releasing ENIs.
- Deletes ECS services, load balancers, auto-scaling groups, and ECS clusters in a safe, sequential order.
- Complements Terraform by ensuring a **clean teardown** where `terragrunt destroy` might fail.

⚠️ **Important**:  
This script **only targets ECS infrastructure**. It does **not** affect other Terraform modules such as bootstrap Cognito or supporting resources.

---

## Prerequisites
Before running, ensure the following are installed and configured:
- **Python 3.x** with required libraries:
  ```bash
  pip install boto3
