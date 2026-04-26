# Run the hospital dashboard project end-to-end in PowerShell
# Usage: .\run_project.ps1

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python not found in PATH. Use the full python path if needed." -ForegroundColor Yellow
    exit 1
}

# Create virtual environment if missing
if (-not (Test-Path .\venv)) {
    Write-Host "Creating virtual environment..."
    python -m venv .\venv
}

# Activate virtual environment for this session
$venvActivate = Join-Path (Join-Path .\venv Scripts) Activate.ps1
if (Test-Path $venvActivate) {
    Write-Host "Activating virtual environment..."
    . $venvActivate
} else {
    Write-Host "Virtual environment activation file not found." -ForegroundColor Yellow
}

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip | Out-Null
python -m pip install -r requirements.txt

Write-Host "Generating hospital data..."
python .\scripts\generate_hospital_data.py

Write-Host "Loading data into SQLite database..."
python .\scripts\load_data.py

Write-Host "Cleaning and transforming data..."
python .\scripts\data_cleaning.py

Write-Host "Generating interactive dashboard..."
python .\scripts\generate_report.py

Write-Host "\n✅ Project run complete." -ForegroundColor Green
Write-Host "Open notebooks/03_visualizations.ipynb to view the dashboard, or open output/*.html files in your browser."
