# SpendShield AI - Live Application Runner
# Runs the real-time fraud detection system locally

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "SpendShield AI - Live Application" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    exit 1
}

# Check .env
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ Created .env file" -ForegroundColor Green
}

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "env:$name" -Value $value
    }
}

# Check API key
$apiKeySet = $env:GOOGLE_API_KEY -and $env:GOOGLE_API_KEY -ne "your_google_api_key_here"

Write-Host ""
if ($apiKeySet) {
    Write-Host "✅ Google API Key configured" -ForegroundColor Green
    Write-Host "   AI-powered analysis enabled" -ForegroundColor Gray
} else {
    Write-Host "⚠️  Google API Key not configured" -ForegroundColor Yellow
    Write-Host "   Using mock data for demonstrations" -ForegroundColor Gray
    Write-Host "   Get your free API key: https://aistudio.google.com/app/apikey" -ForegroundColor Cyan
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "⚠️  Virtual environment not found" -ForegroundColor Yellow
    Write-Host "   Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
    & "venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment created and activated" -ForegroundColor Green
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Create uploads directory
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "✅ Created uploads directory" -ForegroundColor Green
}

# Set Python path
$env:PYTHONPATH = $PWD

# Start the application
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "🚀 Starting SpendShield AI Live Application" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""
Write-Host "📊 Dashboard:  http://localhost:8080" -ForegroundColor Cyan
Write-Host "📚 API Docs:   http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "❤️  Health:     http://localhost:8080/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Features:" -ForegroundColor Yellow
Write-Host "  ✅ Real-time document upload" -ForegroundColor White
Write-Host "  ✅ Live fraud detection" -ForegroundColor White
Write-Host "  ✅ Interactive workflow visualization" -ForegroundColor White
if ($apiKeySet) {
    Write-Host "  ✅ AI-powered analysis (Gemini 2.0 Flash)" -ForegroundColor White
} else {
    Write-Host "  ⚠️  Mock data mode (set GOOGLE_API_KEY for AI)" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""

# Run the live application
python -m uvicorn app.live:app --host 0.0.0.0 --port 8080 --reload
