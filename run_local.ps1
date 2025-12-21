# SpendShield AI - Local Runner
# This script runs the application locally without Docker

Write-Host "================================" -ForegroundColor Cyan
Write-Host "SpendShield AI - Local Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file and add your GOOGLE_API_KEY" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Steps:" -ForegroundColor Cyan
    Write-Host "1. Copy .env.example to .env" -ForegroundColor White
    Write-Host "2. Edit .env and add your Google AI API key" -ForegroundColor White
    Write-Host "3. Get your API key from: https://aistudio.google.com/app/apikey" -ForegroundColor White
    exit 1
}

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "env:$name" -Value $value
    }
}

# Check if API key is set
if (-not $env:GOOGLE_API_KEY -or $env:GOOGLE_API_KEY -eq "your_google_api_key_here") {
    Write-Host "❌ GOOGLE_API_KEY not set in .env file!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please edit .env and add your Google AI API key:" -ForegroundColor Yellow
    Write-Host "1. Get your API key from: https://aistudio.google.com/app/apikey" -ForegroundColor White
    Write-Host "2. Edit .env file" -ForegroundColor White
    Write-Host "3. Replace 'your_google_api_key_here' with your actual API key" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ Environment variables loaded" -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host ""
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Cyan
& "venv\Scripts\Activate.ps1"

# Check if dependencies are installed
Write-Host ""
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Check PostgreSQL
Write-Host ""
Write-Host "🔍 Checking PostgreSQL..." -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: PostgreSQL must be running!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Option 1: Install PostgreSQL locally" -ForegroundColor White
Write-Host "  Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Gray
Write-Host ""
Write-Host "Option 2: Use Docker for PostgreSQL only" -ForegroundColor White
Write-Host "  docker run -d --name spendshield-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=spendshield -p 5432:5432 postgres:15-alpine" -ForegroundColor Gray
Write-Host ""
Write-Host "Option 3: Skip database (will cause errors)" -ForegroundColor White
Write-Host ""

$continue = Read-Host "Is PostgreSQL running? (y/n/skip)"

if ($continue -eq "skip") {
    Write-Host ""
    Write-Host "⚠️  Running without database - some features will not work!" -ForegroundColor Yellow
}
elseif ($continue -ne "y") {
    Write-Host ""
    Write-Host "Please start PostgreSQL and run this script again." -ForegroundColor Yellow
    exit 0
}

# Start the application
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "🚀 Starting SpendShield AI..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "API will be available at: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
