#!/bin/bash
# SpendShield AI - Cloud Run Deployment Script for Cloud Shell
# Run this script in Google Cloud Shell

set -e  # Exit on error

echo "========================================================================================================="
echo "SpendShield AI - Cloud Run Deployment"
echo "========================================================================================================="
echo ""

# Configuration
PROJECT_ID="spend-shield-ai"
REGION="us-central1"
SERVICE_NAME="spendshield-ai"

echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo ""

# Step 1: Set project
echo "Step 1: Setting Google Cloud project..."
gcloud config set project $PROJECT_ID
echo "✓ Project set"
echo ""

# Step 2: Enable APIs
echo "Step 2: Enabling required APIs..."
echo "  - Cloud Run API"
echo "  - Cloud Build API"
echo "  - Container Registry API"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com
echo "✓ APIs enabled"
echo ""

# Step 3: Get API Key (optional)
echo "Step 3: Configuring environment variables..."
read -p "Enter your Google AI API Key (or press Enter to skip): " GOOGLE_API_KEY

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠ Deploying without API key - system will use mock data"
    ENV_VARS="PORT=8080,UPLOAD_DIR=/tmp/uploads"
else
    echo "✓ API key configured"
    ENV_VARS="PORT=8080,UPLOAD_DIR=/tmp/uploads,GOOGLE_API_KEY=$GOOGLE_API_KEY"
fi
echo ""

# Step 4: Deploy
echo "Step 4: Deploying to Cloud Run..."
echo "This will take 5-10 minutes. Please wait..."
echo ""

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 2 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars "$ENV_VARS"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================================================="
    echo "✓ Deployment Successful!"
    echo "========================================================================================================="
    echo ""
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
    
    echo "Your application is now live!"
    echo ""
    echo "Service URL: $SERVICE_URL"
    echo ""
    echo "Access your application:"
    echo "  Dashboard:  $SERVICE_URL"
    echo "  API Docs:   $SERVICE_URL/docs"
    echo "  Health:     $SERVICE_URL/health"
    echo ""
    echo "Useful Commands:"
    echo "  View logs:     gcloud run services logs tail $SERVICE_NAME --region $REGION"
    echo "  Update:        gcloud run deploy $SERVICE_NAME --source . --region $REGION"
    echo "  Delete:        gcloud run services delete $SERVICE_NAME --region $REGION"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check the error messages above for details."
    exit 1
fi
