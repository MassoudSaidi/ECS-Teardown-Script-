import logging
import json
# from icecream import ic
from aws_credentials import AWSCredentials
# from src.btap.common_paths import CommonPaths

class IAMRoles():
    def __init__(self, build_env_name = None):
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = ""
        self.max_duration = 43200
        self.assume_role_policy = {}
        self.managed_policies = []
        self.description = ''
        self.build_env_name = build_env_name

    def arn(self):
        iam_res = AWSCredentials().iam_resource
        role = iam_res.Role(self.full_role_name())
        role.load()
        return role.arn

    def full_role_name(self):
        if self.build_env_name is None:
            # return f"{CommonPaths().get_build_env_name().replace('.', '-')}-{self.role_name}"
            return f"test-env-{self.role_name}"
        else:
            return f"{self.build_env_name.replace('.', '-')}-{self.role_name}"

    def create_role(self):
        # delete if it already exists.
        self.delete()
        iam_client = AWSCredentials().iam_client
        iam_res = AWSCredentials().iam_resource
        iam_client.create_role(
            Path=self.path,
            RoleName=self.full_role_name(),
            AssumeRolePolicyDocument=(json.dumps(self.assume_role_policy)),
            Description=self.description,
            MaxSessionDuration=self.max_duration
        )
        role = iam_res.Role(self.full_role_name())
        role.load()
        for managed_policy in self.managed_policies:
            role.attach_policy(
                PolicyArn=managed_policy.get('PolicyArn')
            )
        logging.info(f'{self.full_role_name()} iam role has been created')

    def delete(self):
        iam = AWSCredentials().iam_client
        iam_res = AWSCredentials().iam_resource
        try:
            role = iam_res.Role(self.full_role_name())
            role.load()

            # Detach all managed policies
            for mp in role.attached_policies.all():
                role.detach_policy(PolicyArn=mp.arn)

            # Delete all inline policies
            for ip in role.policies.all():
                ip.delete()

            # Finally delete the role
            iam.delete_role(RoleName=self.full_role_name())

        except iam.exceptions.NoSuchEntityException:
            logging.info(f'iam_role {self.full_role_name()} did not exist. So not deleting.')

    def get_credentials(self):
        credentials = AWSCredentials()
        return credentials

class IAMCodeBuildRole(IAMRoles):
    def __init__(self, build_env_name = None):
        self.build_env_name = build_env_name
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = "code_build"
        self.max_duration = 43200
        self.description = ''
        self.assume_role_policy = {'Version': '2012-10-17',
                                   'Statement': [
                                       {
                                           'Action': 'sts:AssumeRole',
                                           'Effect': 'Allow',
                                           'Principal': {
                                               'Service': 'codebuild.amazonaws.com'
                                           }
                                       }
                                   ]
                                   }

        self.managed_policies = [{'PolicyArn': 'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess',
                                  'PolicyName': 'AmazonEC2ContainerRegistryFullAccess'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/CloudWatchFullAccess',
                                  'PolicyName': 'CloudWatchFullAccess'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                                  'PolicyName': 'AmazonS3FullAccess'}]

class IAMBatchJobRole(IAMRoles):
    def __init__(self, build_env_name = None):
        self.build_env_name = build_env_name
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = "batch_job_role"
        self.max_duration = 43200
        self.description = ''
        self.assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        self.managed_policies = [
            {
                'PolicyArn': 'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'PolicyName': 'AmazonS3FullAccess'},
            {
                'PolicyArn': 'arn:aws:iam::aws:policy/AWSBatchFullAccess',
                'PolicyName': 'AWSBatchFullAccess'},
            {
                'PolicyArn': 'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'PolicyName': 'AmazonDynamoDBFullAccess'},
            {
                'PolicyArn': 'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess',
                'PolicyName': 'AmazonEC2ContainerRegistryFullAccess'},



        ]


class IAMBatchServiceRole(IAMRoles):
    def __init__(self, build_env_name = None):
        self.build_env_name = build_env_name
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = "batch_service_role"
        self.max_duration = 43200
        self.description = ''
        self.assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "batch.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        self.managed_policies = [{'PolicyArn': 'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess',
                                  'PolicyName': 'AmazonEC2ContainerRegistryFullAccess'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/AmazonRDSFullAccess',
                                  'PolicyName': 'AmazonRDSFullAccess'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole',
                                  'PolicyName': 'AWSBatchServiceRole'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                                  'PolicyName': 'AmazonS3FullAccess'}]




class IAMTerraformDeployerRole(IAMRoles):
    def __init__(self, build_env_name=None):
        self.build_env_name = build_env_name
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = "terraform_deployer_role"
        self.max_duration = 43200
        self.description = 'Role used by Terraform to deploy ECS + Redis infrastructure'

        # This is the trust policy: allows Terraform (via IAM users/roles) to assume it
        self.assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": self._get_current_principal_arn()
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        # No managed policies here — instead, we create and attach custom one
        self.managed_policies = []


        # Inline custom policy JSON
        self.custom_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "CoreEC2Networking",
                    "Effect": "Allow",
                    "Action": [
                        "ec2:*Vpc*",
                        "ec2:*Subnet*",
                        "ec2:*SecurityGroup*",
                        "ec2:*Route*",
                        "ec2:*InternetGateway*",
                        "ec2:*NatGateway*",
                        "ec2:*Eip*",
                        "ec2:Describe*",
                        "ec2:CreateTags",
                        "ec2:DeleteTags",
                        
                        "ec2:AllocateAddress",
                        "ec2:ReleaseAddress",
                        "ec2:AssociateAddress",
                        "ec2:*NetworkAcl*",
                        "ec2:CreateNetworkAclEntry",
                        "ec2:DeleteNetworkAclEntry"                        
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "EC2LaunchTemplatesASG",
                    "Effect": "Allow",
                    "Action": [
                        "ec2:CreateLaunchTemplate",
                        "ec2:DeleteLaunchTemplate",
                        "ec2:CreateLaunchTemplateVersion",
                        "ec2:ModifyLaunchTemplate",
                        "autoscaling:*",
                        "ec2:RunInstances"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "ELB",
                    "Effect": "Allow",
                    "Action": "elasticloadbalancing:*",
                    "Resource": "*"
                },
                {
                    "Sid": "ECS",
                    "Effect": "Allow",
                    "Action": "ecs:*",
                    "Resource": "*"
                },
                {
                    "Sid": "ElastiCache",
                    "Effect": "Allow",
                    "Action": "elasticache:*",
                    "Resource": "*"
                },
                {
                    "Sid": "CloudWatch",
                    "Effect": "Allow",
                    "Action": [
                        "cloudwatch:*",
                        "logs:*"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "SSMReadOnly",
                    "Effect": "Allow",
                    "Action": [
                        "ssm:GetParameter",
                        "ssm:GetParameters",
                        "ssm:GetParametersByPath"
                    ],
                    "Resource": "arn:aws:ssm:*:*:parameter/aws/service/ecs/optimized-ami/*"
                },
                {
                    "Sid": "IAMRolesPoliciesProfiles",
                    "Effect": "Allow",
                    "Action": [
                        "iam:CreateRole",
                        "iam:DeleteRole",
                        "iam:PutRolePolicy",
                        "iam:DeleteRolePolicy",
                        "iam:AttachRolePolicy",
                        "iam:DetachRolePolicy",
                        "iam:CreatePolicy",
                        "iam:DeletePolicy",
                        "iam:CreateInstanceProfile",
                        "iam:DeleteInstanceProfile",
                        "iam:AddRoleToInstanceProfile",
                        "iam:RemoveRoleFromInstanceProfile",
                        "iam:GetRole",
                        "iam:GetPolicy",
                        "iam:GetInstanceProfile",
                        "iam:PassRole",
                        "iam:SimulatePrincipalPolicy",

                        
                        "iam:GetPolicyVersion",
                        "iam:ListAttachedRolePolicies",
                        "iam:ListInstanceProfilesForRole",
                        "iam:ListPolicyVersions",
                        "iam:ListRolePolicies"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Lambda",
                    "Effect": "Allow",
                    "Action": [
                        "lambda:CreateFunction",
                        "lambda:UpdateFunctionCode",
                        "lambda:AddPermission",
                        "lambda:InvokeFunction",
                        "lambda:DeleteFunction",
                        "lambda:GetFunction",
                        "lambda:GetFunctionConfiguration",

                        "lambda:TagResource",      
                        "lambda:UntagResource",
                        "lambda:ListVersionsByFunction",    
                        "lambda:UpdateFunctionConfiguration",
                        "lambda:GetFunctionCodeSigningConfig" ,
                        "lambda:GetPolicy",
                        "lambda:RemovePermission" 
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Cognito",
                    "Effect": "Allow",
                    "Action": [
                        "cognito-idp:CreateUserPool",
                        "cognito-idp:DeleteUserPool",
                        "cognito-idp:DescribeUserPool",
                        "cognito-idp:CreateUserPoolClient",
                        "cognito-idp:UpdateUserPoolClient",
                        "cognito-idp:DeleteUserPoolClient",
                        "cognito-idp:CreateUserPoolDomain",
                        "cognito-idp:DeleteUserPoolDomain",
                        "cognito-idp:CreateGroup",
                        "cognito-idp:DeleteGroup",
                        "cognito-idp:UpdateGroup",
                        "cognito-idp:UpdateUserPool",
                        "cognito-idp:TagResource", 
                        "cognito-idp:UntagResource",
                        "cognito-idp:SetUserPoolMfaConfig",
                        "cognito-idp:GetUserPoolMfaConfig",
                        "cognito-idp:DescribeUserPoolDomain",
                        "cognito-idp:GetGroup",
                        "cognito-idp:DescribeUserPoolClient"
                    ],
                    "Resource": "*"
                }
            ]
        }

    def _get_current_principal_arn(self):
        """
        Auto-detect the ARN of the current SSO/assumed role.
        Falls back to account_id:root if not available.
        """
        sts = self.credentials.sts_client
        ident = sts.get_caller_identity()
        return ident['Arn']


    def create_role(self):
        # First, ensure the previous state is clean.
        logging.info("--- Starting role creation process ---")
        self.delete()
        iam_client = self.credentials.iam_client
        role_name = self.full_role_name()

        # --- Step A: Create the Role ---
        try:
            logging.info(f"Attempting to create role: {role_name}")
            iam_client.create_role(
                Path=self.path,
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(self.assume_role_policy),
                Description=self.description,
                MaxSessionDuration=self.max_duration
            )
            logging.info("SUCCESS: Role created.")
        except Exception as e:
            logging.error(f"FATAL: Failed to create role. Error: {e}")
            return # Stop execution if the role can't be created

        # --- Use a waiter to handle IAM propagation delays ---
        try:
            logging.info(f"Waiting for role '{role_name}' to exist...")
            waiter = iam_client.get_waiter('role_exists')
            waiter.wait(RoleName=role_name)
            logging.info("SUCCESS: Role existence confirmed.")
        except Exception as e:
            logging.error(f"FATAL: Waiter failed for role. Error: {e}")
            return

        # --- Step B: Create the Managed Policy ---
        policy_arn = None
        policy_name = f"{role_name}-policy"
        try:
            logging.info(f"Attempting to create policy: {policy_name}")
            response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(self.custom_policy)
            )
            policy_arn = response['Policy']['Arn']
            logging.info(f"SUCCESS: Policy created with ARN: {policy_arn}")
        except Exception as e:
            logging.error(f"FATAL: Failed to create policy. Error: {e}")
            return # Stop execution if the policy can't be created

        # --- Step C: Attach the Policy to the Role ---
        try:
            logging.info(f"Attempting to attach policy '{policy_arn}' to role '{role_name}'")
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            logging.info("SUCCESS: Policy attached to role.")
        except Exception as e:
            logging.error(f"FATAL: Failed to attach policy. Error: {e}")
            return # Stop execution if attachment fails

        logging.info(f"--- Role creation process completed successfully for {role_name} ---")

    def delete(self):
            """
            A self-contained delete method that robustly cleans up the role and the custom policy with its versions.
            This method does NOT call super().delete().
            """
            iam_client = self.credentials.iam_client
            role_name = self.full_role_name()
            policy_name = f"{role_name}-policy"
            logging.info(f"Attempting to delete role '{role_name}' and its custom policy '{policy_name}'.")

            # We need the Account ID to build the Policy ARN, which is required for many API calls
            try:
                account_id = self.credentials.sts_client.get_caller_identity()["Account"]
                policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            except Exception as e:
                logging.error(f"Could not determine AWS Account ID. Aborting delete. Error: {e}")
                return

            # Step 1: Detach the policy from the role.
            # This must be done before either the role or policy can be deleted.
            try:
                iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                logging.info(f"Detached policy '{policy_name}' from role '{role_name}'.")
            except iam_client.exceptions.NoSuchEntityException:
                # This is not an error. It just means the role or policy is already gone.
                logging.info(f"Role '{role_name}' or policy '{policy_name}' not found, no need to detach.")
            except Exception as e:
                logging.warning(f"Could not detach policy. This may be okay if resources are already gone. Error: {e}")

            # Step 2: Delete the role.
            try:
                iam_client.delete_role(RoleName=role_name)
                logging.info(f"Deleted role '{role_name}'.")
            except iam_client.exceptions.NoSuchEntityException:
                logging.info(f"Role '{role_name}' did not exist, no need to delete.")
            except Exception as e:
                logging.warning(f"Could not delete role. This may be okay if it's already gone. Error: {e}")

            # Step 3: Clean up the policy and its versions.
            # This runs even if the role deletion failed, ensuring we clean up an orphaned policy.
            try:
                # First, list and delete all non-default versions.
                versions_response = iam_client.list_policy_versions(PolicyArn=policy_arn)
                for version in versions_response.get("Versions", []):
                    if not version.get("IsDefaultVersion"):
                        logging.info(f"Deleting version '{version.get('VersionId')}' of policy '{policy_name}'.")
                        iam_client.delete_policy_version(PolicyArn=policy_arn, VersionId=version.get("VersionId"))

                # Finally, delete the policy itself.
                iam_client.delete_policy(PolicyArn=policy_arn)
                logging.info(f"Successfully deleted policy '{policy_name}'.")
            except iam_client.exceptions.NoSuchEntityException:
                logging.info(f"Policy '{policy_name}' did not exist, no need to delete.")
            except Exception as e:
                logging.warning(f"Could not delete policy. This may be okay if it's already gone. Error: {e}")