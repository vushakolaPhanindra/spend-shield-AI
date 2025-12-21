# SpendShield AI - Project Structure

## ✅ **Clean Project Structure**

```
newprop/
├── app/                          # Backend Application
│   ├── __init__.py              # Package initializer
│   ├── live.py                  # ✅ Main FastAPI application (ACTIVE)
│   ├── graph.py                 # Multi-agent graph logic
│   ├── db.py                    # Database utilities
│   ├── main.py                  # Alternative entry point
│   └── simple.py                # Simplified version
│
├── static/                       # Frontend Assets
│   ├── index.html               # ✅ Main dashboard UI
│   ├── css/
│   │   └── styles.css           # ✅ Dashboard styles
│   └── js/
│       └── app.js               # ✅ Frontend logic (integrated with backend)
│
├── uploads/                      # File upload directory
│
├── tests/                        # Test files
│
├── .env                          # Environment configuration
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Docker Compose config
│
├── deploy_cloudrun.ps1           # Cloud Run deployment script
├── deploy_docker.ps1             # Docker deployment script
├── deploy.sh                     # Cloud Shell deployment script
├── run_live.ps1                  # ✅ Local run script (USE THIS)
├── run_local.ps1                 # Alternative run script
│
├── .gcloudignore                 # Cloud deployment exclusions
├── .gitignore                    # Git exclusions
├── cloudbuild.yaml               # Cloud Build configuration
├── pyproject.toml                # Python project metadata
│
├── README.md                     # Project documentation
├── DASHBOARD_GUIDE.md            # Dashboard usage guide
├── DEPLOYMENT.md                 # Deployment instructions
├── DOCKER_DEPLOYMENT.md          # Docker deployment guide
├── QUICK_START.md                # Quick start guide
│
└── test_invoice.png              # Sample test file

```

## 🎯 **Active Components**

### **Backend (app/live.py)**
- ✅ FastAPI application
- ✅ File upload endpoint (`/analyze`)
- ✅ Health check endpoint (`/health`)
- ✅ Demo data endpoint (`/demo`)
- ✅ Audit results endpoint (`/audit/{thread_id}`)
- ✅ Google Gemini AI integration
- ✅ Mock data fallback

### **Frontend (static/)**
- ✅ Interactive dashboard (index.html)
- ✅ File upload with drag & drop
- ✅ Real-time workflow visualization
- ✅ Fraud risk reports
- ✅ Analysis history
- ✅ Settings page

### **Integration**
- ✅ Frontend calls backend API at `http://localhost:8080`
- ✅ File upload → `/analyze` endpoint
- ✅ Results fetched from `/audit/{thread_id}`
- ✅ Demo mode uses `/demo` endpoint
- ✅ Health check via `/health`

## 🚀 **How to Run**

### **Option 1: Run Locally (Recommended)**

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the application
.\run_live.ps1
```

### **Option 2: Run Directly**

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run with Python
python -m uvicorn app.live:app --host 0.0.0.0 --port 8080 --reload
```

### **Option 3: Docker**

```powershell
# Build and run with Docker
.\deploy_docker.ps1
```

### **Option 4: Cloud Run**

```powershell
# Deploy to Google Cloud Run
.\deploy_cloudrun.ps1
```

## 🌐 **Access Points**

After running:
- **Dashboard:** http://localhost:8080
- **API Docs:** http://localhost:8080/docs
- **Health Check:** http://localhost:8080/health
- **Demo Data:** http://localhost:8080/demo

## 📋 **Environment Variables**

Edit `.env` file:

```env
GOOGLE_API_KEY=your_google_ai_api_key_here
PORT=8080
HOST=0.0.0.0
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
```

## ✨ **Features**

1. **Real-time File Upload**
   - Drag & drop interface
   - PDF, PNG, JPG, JPEG support
   - Max 10MB file size

2. **AI-Powered Analysis**
   - Google Gemini 2.0 Flash
   - Automatic data extraction
   - Fraud pattern detection

3. **Multi-Agent Workflow**
   - Extractor Agent
   - Verifier Agent
   - Anomaly Detector
   - Reporter Agent

4. **Interactive Dashboard**
   - Live statistics
   - Workflow visualization
   - Detailed reports
   - Analysis history

## 🔧 **Dependencies**

All dependencies in `requirements.txt`:
- FastAPI - Web framework
- Uvicorn - ASGI server
- Google Generative AI - AI integration
- LangGraph - Multi-agent orchestration
- Pillow - Image processing
- Pydantic - Data validation

## 📝 **Notes**

- Backend and frontend are fully integrated
- Works with or without Google AI API key
- Mock data mode available for testing
- Production-ready with Docker/Cloud Run support

---

**Status:** ✅ Ready to Run  
**Last Updated:** December 21, 2024
