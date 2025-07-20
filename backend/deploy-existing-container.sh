#!/bin/bash

# Google Cloud Deployment Script (for Existing Local Images)
# This script deploys an existing local Docker image to Cloud Run.

set -e

# --- Colors for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Robust .env file parser ---
# This function safely loads environment variables from a .env file.
load_env() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        # Read the file line by line, trim whitespace, and export valid variables.
        # This is safer than `xargs` as it handles special characters.
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            if [[ "$line" =~ ^\s*#.*$ || -z "$line" ]]; then
                continue
            fi
            # Export the line if it is a valid KEY=VALUE pair
            if [[ "$line" =~ ^[a-zA-Z_][a-zA-Z0-9_]*= ]]; then
                export "$line"
            fi
        done < "$env_file"
    fi
}

# --- Configuration ---
# Load environment variables using the robust function
load_env "backend/.env"

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"able-bazaar-466212-r9"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"job-hacker-bot"}
GCR_IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
LOCAL_IMAGE_NAME=${1:-$GCR_IMAGE_NAME}

echo -e "${BLUE}🚀 Starting Google Cloud Deployment for Existing Container${NC}"
echo "=================================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Local Image to Use: $LOCAL_IMAGE_NAME"
echo "Target GCR Image: $GCR_IMAGE_NAME"
echo ""

# --- Prerequisite Checks ---
echo -e "${YELLOW}📋 Checking Prerequisites...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
    exit 1
fi
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with gcloud. Please run 'gcloud auth login'${NC}"
    exit 1
fi

# --- Steps ---
# (The rest of the script remains the same)

echo -e "${BLUE}🏗️  Checking for local Docker image...${NC}"
if docker image inspect "$LOCAL_IMAGE_NAME" &> /dev/null; then
    echo -e "${GREEN}✅ Found local image: '$LOCAL_IMAGE_NAME'. Skipping build.${NC}"
else
    echo -e "${YELLOW}⚠️  Local image '$LOCAL_IMAGE_NAME' not found. Building it now...${NC}"
    docker build -t "$LOCAL_IMAGE_NAME" -f backend/Dockerfile backend
fi

echo -e "${BLUE}🏷️  Tagging image for Google Container Registry...${NC}"
docker tag "$LOCAL_IMAGE_NAME" "$GCR_IMAGE_NAME:latest"

echo -e "${BLUE}🔐 Authenticating Docker with Google Container Registry...${NC}"
gcloud auth configure-docker

echo -e "${BLUE}⬆️  Pushing image to Google Container Registry...${NC}"
docker push "$GCR_IMAGE_NAME:latest"

echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image "$GCR_IMAGE_NAME:latest" \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 900 \
    --concurrency 10 \
    --max-instances 10 \
    --min-instances 0 \
    --env-vars-from-file backend/.env

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================================="
echo -e "Service URL: ${BLUE}$SERVICE_URL${NC}"
echo ""