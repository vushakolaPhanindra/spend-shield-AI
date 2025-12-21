# SpendShield AI - Google Cloud Run Deployment Script
# This script deploys the application to Google Cloud Run

$separator = "=" * 100

Write-Host $separator -ForegroundColor Cyan
Write-Host "SpendShield AI - Google Cloud Run Deployment" -ForegroundColor Cyan
Write-Host $separator -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"
$REGION = "us-central1"
$SERVICE_NAME = "spendshield-ai"

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host "  Service Name: $SERVICE_NAME" -ForegroundColor White
Write-Host ""

# Check if gcloud is installed
Write-Host "Step 1: Checking Google Cloud SDK installation..." -ForegroundColor Yellow
try {
    $gcloudVersion = gcloud --version 2>&1 | Select-Object -First 1
    Write-Host "Google Cloud SDK found: $gcloudVersion" -ForegroundColor Green
}
catch {
    Write-Host "Google Cloud SDK not found!" -ForegroundColor Red
    Write-Host "Please install it from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Set the project
Write-Host "Step 2: Setting Google Cloud project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to set project. Please check your Project ID." -ForegroundColor Red
    exit 1
}
Write-Host "Project set successfully" -ForegroundColor Green
Write-Host ""

# Enable required APIs
Write-Host "Step 3: Enabling required Google Cloud APIs..." -ForegroundColor Yellow
Write-Host "  - Cloud Run API" -ForegroundColor Gray
Write-Host "  - Cloud Build API" -ForegroundColor Gray
Write-Host "  - Container Registry API" -ForegroundColor Gray
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to enable APIs" -ForegroundColor Red
    exit 1
}
Write-Host "APIs enabled successfully" -ForegroundColor Green
Write-Host ""

# Get API Key
Write-Host "Step 4: Configuring environment variables..." -ForegroundColor Yellow
$GOOGLE_API_KEY = ""
if (Test-Path ".env") {
    $envContent = Get-Content .env
    $apiKeyLine = $envContent | Where-Object { $_ -match "^GOOGLE_API_KEY=" }
    if ($apiKeyLine) {
        $GOOGLE_API_KEY = $apiKeyLine -replace "^GOOGLE_API_KEY=", ""
        Write-Host "Found API key in .env file" -ForegroundColor Green
    }
}

if ([string]::IsNullOrWhiteSpace($GOOGLE_API_KEY)) {
    Write-Host "No API key found in .env file" -ForegroundColor Yellow
    $GOOGLE_API_KEY = Read-Host "Enter your Google AI API Key (or press Enter to skip)"
}

if ([string]::IsNullOrWhiteSpace($GOOGLE_API_KEY)) {
    Write-Host "Deploying without API key - system will use mock data" -ForegroundColor Yellow
    $envVars = "PORT=8080,UPLOAD_DIR=/tmp/uploads"
}
else {
    Write-Host "API key configured" -ForegroundColor Green
    $envVars = "PORT=8080,UPLOAD_DIR=/tmp/uploads,GOOGLE_API_KEY=$GOOGLE_API_KEY"
}
Write-Host ""

# Build and deploy using Cloud Build
Write-Host "Step 5: Building and deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "This will take 5-10 minutes. Please wait..." -ForegroundColor Gray
Write-Host ""

gcloud builds submit --config cloudbuild.yaml --substitutions=_REGION=$REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "Cloud Build failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Trying direct deployment method..." -ForegroundColor Yellow
    
    # Alternative: Direct deployment
    gcloud run deploy $SERVICE_NAME `
        --source . `
        --region $REGION `
        --platform managed `
        --allow-unauthenticated `
        --port 8080 `
        --memory 1Gi `
        --cpu 2 `
        --max-instances 10 `
        --timeout 300 `
        --set-env-vars $envVars
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Deployment failed!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Deployment successful!" -ForegroundColor Green
Write-Host ""

# Get the service URL
Write-Host "Step 6: Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

Write-Host ""
Write-Host $separator -ForegroundColor Green
Write-Host "SpendShield AI is now live on Google Cloud Run!" -ForegroundColor Green
Write-Host $separator -ForegroundColor Green
Write-Host ""
Write-Host "Service URL: $serviceUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access your application:" -ForegroundColor Yellow
Write-Host "  Dashboard:  $serviceUrl" -ForegroundColor White
Write-Host "  API Docs:   $serviceUrl/docs" -ForegroundColor White
Write-Host "  Health:     $serviceUrl/health" -ForegroundColor White
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  View logs:     gcloud run services logs tail $SERVICE_NAME --region $REGION" -ForegroundColor White
Write-Host "  Update:        gcloud run deploy $SERVICE_NAME --source . --region $REGION" -ForegroundColor White
Write-Host "  Delete:        gcloud run services delete $SERVICE_NAME --region $REGION" -ForegroundColor White
Write-Host ""
Write-Host "Opening dashboard in browser..." -ForegroundColor Gray
Start-Process $serviceUrl
Write-Host ""
