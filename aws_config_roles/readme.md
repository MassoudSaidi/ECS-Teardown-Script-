
### Open a PowerShell terminal at the root of the project.

```Powershell
PS C:\path\to\your-project>
```

#### Step 1: Point to the Project-Local AWS Configuration and activate the "Builder" Profile
These commands tell the AWS CLI to use the config and credentials files located inside this project's .aws folder, instead of the default global location (~/.aws). This change is temporary and only applies to your current terminal session.

```Powershell
$env:AWS_CONFIG_FILE = ".\.aws\config" ; $env:AWS_SHARED_CREDENTIALS_FILE = ".\.aws\credentials" ; $env:AWS_PROFILE = "default"
```
Test:
```bash
aws sts get-caller-identity
```
Sample output:
```json
{
    "UserId": "XXXXXXXXXXXXXXXXXXXXXXXXX",
    "Account": "88888888888888",
    "Arn": "arn:aws:iam::866134557891:user/bsup_assume_role_dev"
}
```

#### Step 2: Run the create role python script
The Python script must be run by the "builder" user, which is configured in the base profile. This command sets the active profile for the script execution.
```Powershell
python ./aws_config_roles/create_role.py
```
sample output:
```bash
Terraform Deployer Role ARN: arn:aws:iam::866134557891:role/service-role/dev2-terraform_deployer_role
```