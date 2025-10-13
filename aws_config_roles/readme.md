(Nuke_1) PS E:\bsup\proj155-BTAP\AWS\Python\Nuke_1> $env:AWS_CONFIG_FILE = ".\.aws\config"
(Nuke_1) PS E:\bsup\proj155-BTAP\AWS\Python\Nuke_1> $env:AWS_SHARED_CREDENTIALS_FILE = ".\.aws\credentials"
(Nuke_1) PS E:\bsup\proj155-BTAP\AWS\Python\Nuke_1> python aws_config_roles/create_role.py
(Nuke_1) PS E:\bsup\proj155-BTAP\AWS\Python\Nuke_1> aws sts get-caller-identity --profile dev