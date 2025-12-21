# SpendShield AI - Docker Deployment Script
# This script builds and runs the live application in Docker

$separator = "=" * 80

Write-Host $separator -ForegroundColor Cyan
Write-Host "SpendShield AI - Docker Deployment" -ForegroundColor Cyan
Write-Host $separator -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
}
catch {
    Write-Host "Docker not found! Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
Write-Host ""
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host ".env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Created .env file" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Edit .env and add your GOOGLE_API_KEY" -ForegroundColor Yellow
    Write-Host "Get your API key from: https://aistudio.google.com/app/apikey" -ForegroundColor Cyan
    Write-Host ""
    
    $continue = Read-Host "Continue without API key? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Please edit .env file and run this script again." -ForegroundColor Yellow
        exit 0
    }
}

# Stop any running containers
Write-Host ""
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host "Cleaned up existing containers" -ForegroundColor Green

# Build the Docker image
Write-Host ""
Write-Host "Building Docker image..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Gray
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Docker image built successfully" -ForegroundColor Green

# Start the containers
Write-Host ""
Write-Host "Starting SpendShield AI..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start containers!" -ForegroundColor Red
    exit 1
}

# Wait for application to be ready
Write-Host ""
Write-Host "Waiting for application to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check health
$maxRetries = 10
$retryCount = 0
$healthy = $false

while ($retryCount -lt $maxRetries -and -not $healthy) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get -ErrorAction Stop
        if ($response.status -eq "healthy") {
            $healthy = $true
        }
    }
    catch {
        $retryCount++
        Write-Host "." -NoNewline -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

Write-Host ""
if ($healthy) {
    Write-Host "Application is healthy and running!" -ForegroundColor Green
}
else {
    Write-Host "Application started but health check failed" -ForegroundColor Yellow
    Write-Host "Check logs with: docker-compose logs -f" -ForegroundColor Gray
}

# Display success message
Write-Host ""
Write-Host $separator -ForegroundColor Green
Write-Host "SpendShield AI is now running in Docker!" -ForegroundColor Green
Write-Host $separator -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard: http://localhost:8080" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "Health: http://localhost:8080/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  View logs:    docker-compose logs -f" -ForegroundColor White
Write-Host "  Stop:         docker-compose down" -ForegroundColor White
Write-Host "  Restart:      docker-compose restart" -ForegroundColor White
Write-Host "  Rebuild:      docker-compose up --build -d" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop following logs, or close this window." -ForegroundColor Gray
Write-Host ""

# Follow logs
docker-compose logs -f
