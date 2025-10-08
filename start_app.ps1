# PowerShell script to start the CCS Quote Tool
Write-Host "Starting CCS Quote Tool..." -ForegroundColor Green

# Change to the correct directory
Set-Location "C:\Users\david\Documents\CCS quote tool"

# Show current directory
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow

# Check if app.py exists
if (Test-Path "app.py") {
    Write-Host "Found app.py - Starting Flask application..." -ForegroundColor Green
    python app.py
} else {
    Write-Host "ERROR: app.py not found in current directory!" -ForegroundColor Red
    Write-Host "Files in current directory:" -ForegroundColor Yellow
    Get-ChildItem | Format-Table Name, Length -AutoSize
}

Write-Host "Press any key to continue..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")



