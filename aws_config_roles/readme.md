
## Open a PowerShell terminal at the root of the project.

```Powershell
PS C:\path\to\your-project>
```

## Step 1: Point to the Project-Local AWS Configuration
These commands tell the AWS CLI to use the config and credentials files located inside this project's .aws folder, instead of the default global location (~/.aws). This change is temporary and only applies to your current terminal session.

```Powershell
$env:AWS_CONFIG_FILE = ".\.aws\config"
$env:AWS_SHARED_CREDENTIALS_FILE = ".\.aws\credentials"
```

Step 2: Activate the "Builder" Profile
The Python script must be run by the "builder" user, which is configured in the base profile. This command sets the active profile for the script execution.



(Nuke_1) PS E:\bsup\proj155-BTAP\AWS\Python\Nuke_1> $env:AWS_CONFIG_FILE = ".\.aws\config"
(Nuke_1) PS E:\bsup\proj155-BTAP\AWS\Python\Nuke_1> $env:AWS_SHARED_CREDENTIALS_FILE = ".\.aws\credentials"
(Nuke_1) PS E:\bsup\proj155-BTAP\AWS\Python\Nuke_1> python aws_config_roles/create_role.py
(Nuke_1) PS E:\bsup\proj155-BTAP\AWS\Python\Nuke_1> aws sts get-caller-identity --profile dev