from aws_iam_roles import IAMTerraformDeployerRole

build_environment = "dev3"
role = IAMTerraformDeployerRole(build_env_name=build_environment)  
role.create_role()
print("Terraform Deployer Role ARN:", role.arn())
