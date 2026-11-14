@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0.."

echo ======================================================================
echo   ip+ - Creating Desktop and Start Menu Shortcuts
echo ======================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$currDir = (Get-Location).Path; " ^
  "Get-ChildItem -LiteralPath $currDir -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue; " ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$exeCandidate = Join-Path $currDir 'ip+.exe'; " ^
  "if (Test-Path $exeCandidate) { $target = $exeCandidate } else { $target = Join-Path $currDir 'ip+.bat' }; " ^
  "$icon = Join-Path $currDir 'assets\ip_plus.ico'; " ^
  "if (-not (Test-Path $icon)) { $icon = Join-Path $currDir 'assets\iphone_link.ico' }; " ^
  "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$startMenu = [Environment]::GetFolderPath('Programs'); " ^
  "$oldDesk = Join-Path $desktop 'iPhone Link.lnk'; if (Test-Path $oldDesk) { Remove-Item $oldDesk -Force -ErrorAction SilentlyContinue }; " ^
  "$oldStart = Join-Path $startMenu 'iPhone Link.lnk'; if (Test-Path $oldStart) { Remove-Item $oldStart -Force -ErrorAction SilentlyContinue }; " ^
  "$deskLnk = Join-Path $desktop 'ip+.lnk'; " ^
  "$scDesk = $ws.CreateShortcut($deskLnk); " ^
  "$scDesk.TargetPath = $target; " ^
  "$scDesk.WorkingDirectory = $currDir; " ^
  "$scDesk.IconLocation = $icon; " ^
  "$scDesk.Description = 'ip+ — Native 60fps iPhone Mirroring for Windows 11'; " ^
  "$scDesk.Save(); " ^
  "Write-Host '[OK] Desktop Shortcut created:' $deskLnk '->' $target -ForegroundColor Green; " ^
  "$startLnk = Join-Path $startMenu 'ip+.lnk'; " ^
  "$scStart = $ws.CreateShortcut($startLnk); " ^
  "$scStart.TargetPath = $target; " ^
  "$scStart.WorkingDirectory = $currDir; " ^
  "$scStart.IconLocation = $icon; " ^
  "$scStart.Description = 'ip+ — Native 60fps iPhone Mirroring for Windows 11'; " ^
  "$scStart.Save(); " ^
  "Write-Host '[OK] Start Menu Shortcut created:' $startLnk '->' $target -ForegroundColor Green;"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo   [BERHASIL] Shortcut "ip+" dengan icon native telah dibuat
    echo   di Desktop dan Start Menu Windows Anda!
    echo ======================================================================
) else (
    echo.
    echo [ERROR] Gagal membuat shortcut. Pastikan izin akses PowerShell aktif.
)
