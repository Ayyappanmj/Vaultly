# Windows PowerShell setup
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$PSScriptRoot\vaultly.ps1" setup
