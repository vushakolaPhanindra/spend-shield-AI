# SpendShield AI - Live Docker Deployment Guide

## 🚀 **Real-Time Fraud Detection - Now Live!**

This guide will help you deploy SpendShield AI in Docker with **real-time image upload and live fraud detection**.

---

## 📋 **Prerequisites**

### **Required**
- ✅ **Docker Desktop** installed and running
  - Download: https://www.docker.com/products/docker-desktop
  - Minimum version: 20.10+

### **Optional (for AI features)**
- ✅ **Google AI API Key** (free)
  - Get it from: https://aistudio.google.com/app/apikey
  - Without this, the system will use mock data

---

## ⚡ **Quick Start (3 Steps)**

### **Step 1: Get Your API Key** (Optional but Recommended)

1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)

### **Step 2: Configure Environment**

1. Edit the `.env` file in this directory
2. Add your API key:
   ```
   GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```
3. Save the file

### **Step 3: Deploy with Docker**

Run the deployment script:
```powershell
.\deploy_docker.ps1
```

**That's it!** The script will:
- ✅ Build the Docker image
- ✅ Start the container
- ✅ Check health status
- ✅ Show you the dashboard URL

---

## 🌐 **Access Your Application**

Once deployed, access:

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8080 | Interactive web interface |
| **API Docs** | http://localhost:8080/docs | Swagger UI documentation |
| **Health Check** | http://localhost:8080/health | System status |
| **Demo Data** | http://localhost:8080/demo | Sample fraud analysis |

---

## 📤 **Upload and Analyze Documents**

### **Method 1: Web Dashboard** (Recommended)

1. Open http://localhost:8080
2. Click **"Upload Document"** in sidebar
3. **Drag and drop** an invoice image (PNG, JPG, JPEG)
4. Click **"Start Analysis"**
5. Watch the **real-time workflow** animation
6. View **results** in the Reports page

### **Method 2: API (curl)**

```bash
# Upload an image for analysis
curl -X POST http://localhost:8080/analyze \
  -F "file=@invoice.png" \
  -F "department=Finance" \
  -F "fiscal_year=2024"

# Response:
# {
#   "thread_id": "abc-123-def-456",
#   "status": "completed",
#   "message": "Analysis completed in 2.5 seconds"
# }

# Get results
curl http://localhost:8080/audit/abc-123-def-456
```

### **Method 3: Python Script**

```python
import requests

# Upload document
with open('invoice.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/analyze',
        files={'file': f},
        data={'department': 'Finance'}
    )

thread_id = response.json()['thread_id']
print(f"Analysis started: {thread_id}")

# Get results
result = requests.get(f'http://localhost:8080/audit/{thread_id}')
print(f"Risk Score: {result.json()['fraud_risk_score']}/100")
print(f"Anomalies: {len(result.json()['anomalies'])}")
```

---

## 🔄 **Real-Time Workflow**

When you upload a document, here's what happens **live**:

### **Stage 1: Extractor Agent** (2-3 seconds)
- 📄 Analyzes the uploaded image
- 🤖 Uses Google Gemini 2.0 Flash (if API key configured)
- 📊 Extracts:
  - Vendor name
  - Invoice number
  - Total amount
  - Line items
  - Transaction date

### **Stage 2: Verifier Agent** (1 second)
- 🔍 Cross-checks vendor against database
- 📈 Retrieves historical pricing data
- ⚠️ Checks vendor risk score
- 📋 Validates document completeness

### **Stage 3: Anomaly Detector** (1 second)
- 🚨 Detects fraud patterns:
  - **Ghost Vendors** - Unregistered vendors
  - **Price Inflation** - >20% price increases
  - **High Value** - Transactions >$25,000
  - **Missing Data** - Incomplete documents

### **Stage 4: Reporter Agent** (1 second)
- 📊 Calculates fraud risk score (0-100)
- 🎯 Determines risk level (LOW/MEDIUM/HIGH/CRITICAL)
- 💡 Generates actionable recommendations
- 📄 Creates comprehensive report

**Total Time**: 5-7 seconds for complete analysis!

---

## 📊 **Understanding Results**

### **Risk Scores**

| Score | Level | Action |
|-------|-------|--------|
| 0-20 | 🟢 LOW | Approve normally |
| 21-40 | 🟡 MEDIUM | Review recommended |
| 41-70 | 🟠 HIGH | Detailed investigation required |
| 71-100 | 🔴 CRITICAL | Reject and investigate immediately |

### **Anomaly Types**

| Type | Severity | Description |
|------|----------|-------------|
| **Ghost Vendor** | CRITICAL | Vendor not in database |
| **Price Inflation** | HIGH | >20% above historical average |
| **High Value** | MEDIUM | Transaction >$25,000 |
| **Missing Vendor ID** | HIGH | No vendor identification |
| **Duplicate Invoice** | CRITICAL | Reference number already exists |

---

## 🐳 **Docker Commands**

### **View Logs**
```powershell
# Follow live logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View specific service
docker-compose logs app
```

### **Stop Application**
```powershell
docker-compose down
```

### **Restart Application**
```powershell
docker-compose restart
```

### **Rebuild and Restart**
```powershell
docker-compose up --build -d
```

### **Check Status**
```powershell
docker-compose ps
```

### **Access Container Shell**
```powershell
docker exec -it spendshield-live /bin/bash
```

---

## 📁 **File Upload Specifications**

### **Supported Formats**
- ✅ **PNG** - Recommended for invoices
- ✅ **JPG/JPEG** - Good for scanned documents
- ✅ **PDF** - Supported (first page analyzed)

### **File Size Limits**
- **Maximum**: 10MB per file
- **Recommended**: 1-5MB for best performance

### **Image Quality**
- **Minimum Resolution**: 800x600 pixels
- **Recommended**: 1920x1080 or higher
- **DPI**: 150+ for scanned documents

### **Best Practices**
- ✅ Clear, well-lit images
- ✅ All text visible and readable
- ✅ No shadows or glare
- ✅ Straight orientation (not tilted)
- ✅ High contrast

---

## 🔧 **Configuration**

### **Environment Variables**

Edit `.env` file to configure:

```env
# AI Configuration (Required for real analysis)
GOOGLE_API_KEY=your_key_here

# Server Configuration
PORT=8080
HOST=0.0.0.0

# Upload Configuration
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg

# Detection Thresholds
PRICE_INFLATION_THRESHOLD=20  # Percentage
HIGH_VALUE_THRESHOLD=25000    # Dollars
```

### **Changing Port**

To run on a different port (e.g., 9000):

1. Edit `docker-compose.yml`:
   ```yaml
   ports:
     - "9000:8080"  # Change 9000 to your desired port
   ```

2. Restart:
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

3. Access at: http://localhost:9000

---

## 🐛 **Troubleshooting**

### **Problem: Docker build fails**

**Solution**:
```powershell
# Clean Docker cache
docker system prune -a

# Rebuild
docker-compose build --no-cache
```

### **Problem: Port 8080 already in use**

**Solution**:
```powershell
# Find what's using the port
netstat -ano | findstr :8080

# Kill the process or change port in docker-compose.yml
```

### **Problem: Application not responding**

**Solution**:
```powershell
# Check container status
docker-compose ps

# View logs for errors
docker-compose logs app

# Restart
docker-compose restart
```

### **Problem: AI analysis not working**

**Solution**:
1. Check if API key is set in `.env`
2. Verify API key is valid
3. Check logs: `docker-compose logs app | findstr "AI"`
4. Without API key, system uses mock data (this is normal)

### **Problem: File upload fails**

**Solution**:
1. Check file size (must be <10MB)
2. Verify file format (PNG, JPG, JPEG, PDF only)
3. Check uploads directory permissions
4. View logs: `docker-compose logs app`

---

## 📊 **Performance Metrics**

### **Expected Performance**

| Metric | Value |
|--------|-------|
| **Startup Time** | 5-10 seconds |
| **Analysis Time** | 5-7 seconds per document |
| **Concurrent Uploads** | 10+ simultaneous |
| **Memory Usage** | ~200MB |
| **CPU Usage** | 10-30% during analysis |

### **Scaling**

For high-volume deployments:

1. **Increase container resources**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

2. **Add multiple replicas**:
   ```powershell
   docker-compose up --scale app=3 -d
   ```

---

## 🔒 **Security Considerations**

### **Production Deployment**

Before deploying to production:

1. **Change default credentials**
2. **Enable HTTPS** (use reverse proxy like Nginx)
3. **Add authentication** (JWT tokens)
4. **Implement rate limiting**
5. **Set up firewall rules**
6. **Enable audit logging**
7. **Regular security updates**

### **API Key Security**

- ✅ Never commit `.env` to Git
- ✅ Use environment variables in production
- ✅ Rotate API keys regularly
- ✅ Monitor API usage

---

## 📈 **Monitoring**

### **Health Checks**

```powershell
# Check application health
Invoke-RestMethod http://localhost:8080/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "SpendShield AI (Live)",
#   "ai_enabled": true,
#   "upload_dir": true
# }
```

### **Logs**

```powershell
# Real-time logs
docker-compose logs -f app

# Search logs
docker-compose logs app | Select-String "ERROR"

# Export logs
docker-compose logs app > logs.txt
```

---

## 🎯 **Next Steps**

### **After Deployment**

1. ✅ **Test with sample invoice** - Upload a test image
2. ✅ **Review results** - Check the generated report
3. ✅ **Customize thresholds** - Adjust detection sensitivity
4. ✅ **Integrate with systems** - Connect to your workflow
5. ✅ **Monitor performance** - Track analysis metrics

### **Optional Enhancements**

- 📧 **Email notifications** for high-risk detections
- 📊 **Analytics dashboard** with charts
- 🔄 **Batch processing** for multiple files
- 💾 **Database integration** for persistence
- 🌐 **Multi-language support**

---

## 📞 **Support**

### **Documentation**
- README.md - Project overview
- DASHBOARD_GUIDE.md - UI walkthrough
- DEPLOYMENT.md - Advanced deployment options

### **API Documentation**
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### **Logs**
```powershell
docker-compose logs -f
```

---

## 🎉 **Success!**

You now have a **fully functional, real-time fraud detection system** running in Docker!

**Features**:
- ✅ Real-time document upload
- ✅ AI-powered analysis
- ✅ Live workflow visualization
- ✅ Instant results
- ✅ Production-ready deployment

**Start detecting fraud now at: http://localhost:8080** 🚀

---

**Version**: 1.0.0  
**Last Updated**: December 21, 2024  
**Status**: ✅ Production Ready
