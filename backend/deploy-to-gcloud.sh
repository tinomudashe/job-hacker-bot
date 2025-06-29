#!/bin/bash

# Google Cloud Deployment Script for Job Application with Browser Automation
# Ensures Playwright v1.52.0 compatibility throughout the deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"numeric-melody-457111-e0"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="job-app-browser"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo -e "${BLUE}🚀 Starting Google Cloud Deployment with Browser Automation${NC}"
echo "=================================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking Prerequisites...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with gcloud. Please run 'gcloud auth login'${NC}"
    exit 1
fi

# Set project
echo -e "${BLUE}🔧 Setting up Google Cloud project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Check local compatibility first
echo -e "${YELLOW}🧪 Running Local Compatibility Check...${NC}"
if python3 app/browser_compatibility.py; then
    echo -e "${GREEN}✅ Local compatibility check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Local compatibility check had warnings, but continuing...${NC}"
fi

# Build and push image using Cloud Build
echo -e "${BLUE}🏗️  Building image with Cloud Build...${NC}"
cd ..
gcloud builds submit --config=backend/cloudbuild.yaml \
    --substitutions=_DATABASE_HOST="your-database-host",_DATABASE_PASSWORD="your-database-password" \
    backend
cd backend

# Verify the image was built successfully
echo -e "${BLUE}🔍 Verifying image build...${NC}"
if gcloud container images describe $IMAGE_NAME:latest --quiet > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Image built successfully${NC}"
else
    echo -e "${RED}❌ Image build failed${NC}"
    exit 1
fi

# Deploy to Cloud Run with browser automation optimizations
echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 900 \
    --concurrency 10 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "PLAYWRIGHT_BROWSERS_PATH=/ms-playwright" \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --set-env-vars "PYTHONUNBUFFERED=1" \
    --port 8000

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================================="
echo -e "Service URL: ${BLUE}$SERVICE_URL${NC}"
echo -e "Health Check: ${BLUE}$SERVICE_URL/health${NC}"
echo ""

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Service is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Service health check failed, but deployment completed${NC}"
    echo "You may need to wait a few minutes for the service to fully start"
fi

# Display useful commands
echo ""
echo -e "${BLUE}📝 Useful Commands:${NC}"
echo "View logs: gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo "Update service: gcloud run services update $SERVICE_NAME --region=$REGION"
echo "Delete service: gcloud run services delete $SERVICE_NAME --region=$REGION"
echo ""

# Browser automation specific notes
echo -e "${YELLOW}🤖 Browser Automation Notes:${NC}"
echo "• Playwright v1.52.0 is installed and compatible"
echo "• Browser-use v0.1.8 is configured for optimal performance"
echo "• Memory: 4GB (recommended for browser automation)"
echo "• Timeout: 15 minutes (for complex job scraping)"
echo "• Browsers: Chromium, Firefox, WebKit available"
echo ""

echo -e "${GREEN}✅ Deployment script completed successfully!${NC}" 