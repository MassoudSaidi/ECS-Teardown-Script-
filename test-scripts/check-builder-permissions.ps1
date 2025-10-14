<#
.SYNOPSIS
    Verifies that the "builder" AWS profile has the required read and list permissions.
.DESCRIPTION
    This script is compatible with all versions of the AWS CLI. It activates the
    project-local AWS configuration and tests a list of essential IAM "read" and
    "list" permissions using safe, live API calls.
.PARAMETER Profile
    The name of the AWS builder profile to test. Defaults to "base".
.EXAMPLE
    .\check-builder-permissions.ps1
#>
param (
    [string]$Profile = "base"
)

# --- 1. Activate Project-Local AWS Configuration ---
try {
    $ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
    $AwsConfigFile = Join-Path $ProjectRoot ".aws\config"
    $AwsCredentialsFile = Join-Path $ProjectRoot ".aws\credentials"

    if (-not (Test-Path $AwsConfigFile) -or -not (Test-Path $AwsCredentialsFile)) {
        throw "Could not find the local AWS configuration files in '$ProjectRoot\.aws'"
    }

    $env:AWS_CONFIG_FILE = $AwsConfigFile
    $env:AWS_SHARED_CREDENTIALS_FILE = $AwsCredentialsFile
    $env:AWS_PROFILE = $Profile
}
catch {
    Write-Host "FATAL: Failed to set up AWS environment. Error: $_" -ForegroundColor Red
    return
}

Write-Host "--- Using AWS config from '$ProjectRoot\.aws'" -ForegroundColor Cyan
Write-Host "--- Verifying identity for profile '$Profile' ---" -ForegroundColor Cyan

# --- 2. Verify Identity (Requires sts:GetCallerIdentity) ---
$identity = aws sts get-caller-identity --output json | ConvertFrom-Json
if (-not $identity) {
    Write-Host "FATAL: Could not get AWS identity for profile '$Profile'. Please verify credentials and the 'sts:GetCallerIdentity' permission." -ForegroundColor Red
    return
}
$userName = $identity.Arn.Split('/')[-1]
Write-Host "Identity confirmed: $($identity.Arn)" -ForegroundColor Green

# --- 3. Define the Required READ Permissions and Their Test Commands ---
# This version only tests safe, read-only permissions.
$permissionTests = @{
    "iam:GetRole"                  = "aws iam get-role --role-name an-example-role-that-may-not-exist"
    "iam:GetUserPolicy"            = "aws iam get-user-policy --user-name $userName --policy-name an-example-policy-that-may-not-exist"
    "iam:ListPolicyVersions"       = "aws iam list-policy-versions --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --max-items 1"
    "iam:ListAttachedRolePolicies" = "aws iam list-attached-role-policies --role-name an-example-role-that-may-not-exist --max-items 1"
    "iam:ListRolePolicies"         = "aws iam list-role-policies --role-name an-example-role-that-may-not-exist --max-items 1"
    "iam:ListRoles"                = "aws iam list-roles --max-items 1"
    "iam:ListUserPolicies"         = "aws iam list-user-policies --user-name $userName --max-items 1"
}

Write-Host "`n--- Testing Required READ-ONLY IAM Permissions ---" -ForegroundColor Cyan
$allPassed = $true

# --- 4. Loop Through and Test Each Permission ---
foreach ($entry in $permissionTests.GetEnumerator()) {
    $permission = $entry.Name
    $command = $entry.Value
    
    Write-Host ("Checking {0,-35}" -f $permission) -NoNewline

    $result = Invoke-Expression "$command 2>&1"

    # Success is either a clean exit (0), or an error that is NOT 'AccessDenied'.
    # Errors like 'NoSuchEntity' are expected and prove the permission check passed.
    if (($LASTEXITCODE -eq 0) -or ($result -notmatch "AccessDenied")) {
        Write-Host "ALLOWED" -ForegroundColor Green
    } else {
        Write-Host "DENIED" -ForegroundColor Red
        Write-Host "  └─ Reason: $result" -ForegroundColor DarkRed
        $allPassed = $false
    }
}

# --- 5. Final Summary ---
if ($allPassed) {
    Write-Host "`nSUCCESS: All required builder READ permissions are correctly configured for profile '$Profile'." -ForegroundColor Green
    Write-Host "This is a strong indicator that your write permissions (Create/Delete) are also correct." -ForegroundColor Yellow
} else {
    Write-Host "`nFAILURE: One or more required READ permissions are missing for profile '$Profile'. Please review the DENIED messages above." -ForegroundColor Red
}