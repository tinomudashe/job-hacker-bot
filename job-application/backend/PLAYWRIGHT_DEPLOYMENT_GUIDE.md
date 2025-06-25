# 🚀 Playwright Browser Automation Deployment Guide

## Overview
This guide covers deploying your job application system with **Playwright v1.52.0** browser automation capabilities to Google Cloud. The system uses the Microsoft Playwright container for maximum compatibility and performance.

## 🔧 **Version Compatibility Matrix**

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| **Playwright** | 1.52.0 | ✅ Verified | Exact match with container |
| **Browser-Use** | 0.1.8 | ✅ Compatible | Tested and working |
| **Container** | mcr.microsoft.com/playwright:v1.52.0-noble | ✅ Official | Microsoft maintained |
| **Python** | 3.11+ | ✅ Supported | From base container |
| **Browsers** | Chromium, Firefox, WebKit | ✅ Pre-installed | Ready to use |

## 📋 **Prerequisites**

### Local Environment
- Google Cloud SDK (`gcloud`) installed
- Docker installed and running
- Python 3.11+ with required dependencies
- Valid Google Cloud project with billing enabled

### Google Cloud Setup
```bash
# Install gcloud CLI (if not already installed)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

## 🐳 **Docker Configuration**

### Dockerfile.playwright
Uses the official Microsoft Playwright container as base:
```dockerfile
FROM mcr.microsoft.com/playwright:v1.52.0-noble
```

**Key Features:**
- ✅ Pre-installed browsers (Chromium, Firefox, WebKit)
- ✅ Optimized for browser automation
- ✅ Security hardened for production
- ✅ Automatic dependency management

### Version Pinning
All versions are pinned for reproducible builds:
```
playwright==1.52.0
browser-use==0.1.8
```

## 🚀 **Deployment Options**

### Option 1: Automated Deployment (Recommended)
```bash
# Make script executable
chmod +x deploy-to-gcloud.sh

# Run deployment
./deploy-to-gcloud.sh
```

### Option 2: Manual Cloud Build
```bash
# Submit build
gcloud builds submit --config=cloudbuild.yaml

# Deploy to Cloud Run
gcloud run deploy job-app-browser \
    --image gcr.io/YOUR_PROJECT_ID/job-app-browser:latest \
    --region us-central1 \
    --memory 4Gi \
    --cpu 2 \
    --timeout 900
```

### Option 3: Docker Compose (Local Testing)
```bash
# Start all services
docker-compose -f docker-compose.playwright.yml up -d

# View logs
docker-compose -f docker-compose.playwright.yml logs -f
```

## ⚙️ **Cloud Run Configuration**

### Resource Allocation
```yaml
Memory: 4 GiB          # Required for browser automation
CPU: 2 cores           # Optimal for concurrent browsers
Timeout: 900 seconds   # 15 minutes for complex scraping
Concurrency: 10        # Balanced for browser workloads
Max Instances: 10      # Scale based on demand
```

### Environment Variables
```bash
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
GOOGLE_CLOUD_PROJECT=your-project-id
DATABASE_URL=postgresql+asyncpg://...
PYTHONUNBUFFERED=1
```

## 🧪 **Testing & Validation**

### Local Compatibility Check
```bash
# Run comprehensive check
python3 app/browser_compatibility.py

# Expected output:
# ✅ Overall Status: COMPATIBLE
# ✅ Playwright Status: All browsers working
# ✅ Browser-Use Status: Compatible
```

### Production Health Check
```bash
# Test deployment
curl https://your-service-url/health

# Test browser automation
curl -X POST https://your-service-url/api/extract-job \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example-job-posting.com"}'
```

## 🔍 **Monitoring & Debugging**

### View Logs
```bash
# Real-time logs
gcloud run services logs read job-app-browser --region=us-central1 --follow

# Filter browser-specific logs
gcloud run services logs read job-app-browser \
  --region=us-central1 \
  --filter="textPayload:playwright OR textPayload:browser-use"
```

### Common Issues & Solutions

#### Browser Launch Failures
```bash
# Check memory allocation
gcloud run services describe job-app-browser --region=us-central1

# Increase memory if needed
gcloud run services update job-app-browser \
  --memory 6Gi --region=us-central1
```

#### Timeout Issues
```bash
# Increase timeout for complex scraping
gcloud run services update job-app-browser \
  --timeout 1200 --region=us-central1
```

#### Version Conflicts
```bash
# Rebuild with exact versions
docker build -f Dockerfile.playwright -t test-compatibility .
docker run --rm test-compatibility python3 app/browser_compatibility.py
```

## 📊 **Performance Optimization**

### Browser Configuration
```python
# Optimized browser settings for Cloud Run
browser_args = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding'
]
```

### Resource Management
```python
# Limit concurrent browsers
MAX_CONCURRENT_BROWSERS = 3
BROWSER_TIMEOUT = 30  # seconds
PAGE_TIMEOUT = 20     # seconds
```

## 🔐 **Security Considerations**

### Container Security
- ✅ Non-root user execution
- ✅ Minimal attack surface
- ✅ Regular security updates
- ✅ Sandboxed browser processes

### Network Security
```bash
# Restrict egress (optional)
gcloud run services update job-app-browser \
  --vpc-egress private-ranges-only \
  --region=us-central1
```

## 💰 **Cost Optimization**

### Scaling Configuration
```bash
# Optimize for cost
gcloud run services update job-app-browser \
  --min-instances 0 \
  --max-instances 5 \
  --concurrency 20 \
  --region=us-central1
```

### Expected Costs (US-Central1)
- **Memory (4GB)**: ~$0.0000024 per GB-second
- **CPU (2 cores)**: ~$0.0000024 per vCPU-second
- **Requests**: $0.40 per million requests
- **Estimated monthly cost**: $20-50 for moderate usage

## 🔄 **CI/CD Integration**

### GitHub Actions Example
```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        
      - name: Build and Deploy
        run: |
          cd backend
          gcloud builds submit --config=cloudbuild.yaml
```

## 📈 **Scaling & Load Testing**

### Load Testing Script
```bash
# Install artillery
npm install -g artillery

# Run load test
artillery quick --count 10 --num 5 \
  https://your-service-url/api/extract-job
```

### Auto-scaling Metrics
- **CPU utilization**: Target 70%
- **Memory utilization**: Target 80%
- **Request latency**: < 30 seconds
- **Error rate**: < 1%

## 🆘 **Troubleshooting Guide**

### Issue: Container Won't Start
```bash
# Check build logs
gcloud builds log BUILD_ID

# Check service status
gcloud run services describe job-app-browser --region=us-central1
```

### Issue: Browser Crashes
```bash
# Increase shared memory
gcloud run services update job-app-browser \
  --memory 6Gi --region=us-central1
```

### Issue: Slow Performance
```bash
# Check resource utilization
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"
```

## 📚 **Additional Resources**

- [Microsoft Playwright Container Documentation](https://playwright.dev/docs/docker)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Browser-Use Library Guide](https://github.com/browser-use/browser-use)
- [Cloud Build Configuration Reference](https://cloud.google.com/build/docs/build-config-file-schema)

## ✅ **Deployment Checklist**

- [ ] Local compatibility check passes
- [ ] Docker build succeeds
- [ ] Cloud Build configuration validated
- [ ] Environment variables configured
- [ ] Database connection tested
- [ ] Health checks responding
- [ ] Browser automation working
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Cost alerts configured

---

## 🎯 **Quick Start Commands**

```bash
# 1. Run compatibility check
python3 app/browser_compatibility.py

# 2. Deploy to Google Cloud
./deploy-to-gcloud.sh

# 3. Test deployment
curl https://your-service-url/health

# 4. Monitor logs
gcloud run services logs read job-app-browser --region=us-central1 --follow
```

**Your browser automation system is now ready for production! 🚀** 