## How to Run
Open a PowerShell terminal.
Navigate to this directory (test_script_folder).
Execute the script directly:

```Powershell
.\check-builder-permissions.ps1
```

If you get an error message saying "...script execution is disabled on this system," run the following command to allow scripts to run only in the current window. This change is temporary and safe.

```Powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```