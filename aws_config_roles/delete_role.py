from aws_iam_roles import IAMTerraformDeployerRole

build_environment = "dev3"
role_to_delete = IAMTerraformDeployerRole(build_env_name=build_environment)

print(f"Preparing to delete the IAM role '{role_to_delete.full_role_name()}'...")

role_to_delete.delete()

print(f"Deletion process for role '{role_to_delete.full_role_name()}' has been completed.")
