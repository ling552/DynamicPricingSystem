$ErrorActionPreference = "Stop"

python -m pip install -r requirements-build.txt
python -m PyInstaller --clean --noconfirm DynamicPricingSystem.spec

Write-Host ""
Write-Host "Build complete:"
Write-Host (Resolve-Path ".\dist\DynamicPricingSystem.exe")
Write-Host "Run the exe. It will create .\dist\data\ and .\dist\logs\ next to itself."
