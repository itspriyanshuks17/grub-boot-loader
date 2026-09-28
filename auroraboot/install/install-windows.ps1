# AuroraBoot installer for Windows (UEFI). EXPERIMENTAL / UNTESTED - try in a VM first.
# Run in an elevated PowerShell:   .\install-windows.ps1 [-Try]
#   -Try : boot AuroraBoot once on next restart (does not change permanent boot order)
param([switch]$Try)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$efi = Join-Path $root 'build\AuroraBoot.efi'; if (-not (Test-Path $efi)) { $efi = Join-Path $root 'dist\AuroraBoot.efi' }
if (-not (Test-Path $efi)) { throw 'AuroraBoot.efi not found' }
mountvol S: /S
try {
  New-Item -ItemType Directory -Force S:\EFI\AuroraBoot | Out-Null
  Copy-Item $efi S:\EFI\AuroraBoot\AuroraBoot.efi -Force
  if (-not (Test-Path S:\EFI\AuroraBoot\aurora.conf)) { Copy-Item (Join-Path $root 'config\aurora.conf') S:\EFI\AuroraBoot\aurora.conf }
} finally { mountvol S: /D }
$out = bcdedit /copy '{bootmgr}' /d 'AuroraBoot'
$guid = [regex]::Match($out, '\{[0-9a-fA-F-]+\}').Value
bcdedit /set $guid path '\EFI\AuroraBoot\AuroraBoot.efi' | Out-Null
bcdedit /set '{fwbootmgr}' displayorder $guid /addlast | Out-Null
if ($Try) { bcdedit /set '{fwbootmgr}' bootsequence $guid | Out-Null; Write-Host 'Restart: AuroraBoot runs once.' }
else { Write-Host 'Added to firmware boot list (order unchanged). Choose it from the boot menu.' }
Write-Host 'Note: with Secure Boot ON the firmware will refuse this unsigned binary. See README > Secure Boot.'
