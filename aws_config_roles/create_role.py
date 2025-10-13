from aws_iam_roles import IAMTerraformDeployerRole

role = IAMTerraformDeployerRole(build_env_name="dev2")  
role.create_role()
print("Terraform Deployer Role ARN:", role.arn())
