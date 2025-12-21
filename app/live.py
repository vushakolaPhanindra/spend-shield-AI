"""
SpendShield AI - Optimized Live Application
Real-time fraud detection with enhanced performance and error handling
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import uuid
import shutil
import asyncio
from datetime import datetime
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    import google.generativeai as genai
    from PIL import Image
    import io
    import json
    import re
    AI_LIBRARIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI libraries not available: {e}")
    AI_LIBRARIES_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="SpendShield AI - Live",
    description="Real-time fraud detection system with AI-powered analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found, serving without static files")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
    PORT = int(os.getenv("PORT", 8080))
    
    @classmethod
    def is_ai_enabled(cls) -> bool:
        return (
            AI_LIBRARIES_AVAILABLE and 
            cls.GOOGLE_API_KEY and 
            cls.GOOGLE_API_KEY != "your_google_api_key_here"
        )

# Configure Gemini AI
AI_ENABLED = Config.is_ai_enabled()
if AI_ENABLED:
    try:
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        logger.info("✅ Google Gemini AI configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure Gemini AI: {e}")
        AI_ENABLED = False
else:
    logger.warning("⚠️  AI disabled: Using mock data mode")

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)

# In-memory storage with size limit
class AnalysisCache:
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
    
    def add(self, thread_id: str, data: Dict):
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[thread_id] = data
    
    def get(self, thread_id: str) -> Optional[Dict]:
        return self.cache.get(thread_id)
    
    def list_recent(self, limit: int = 10) -> List[Dict]:
        return list(self.cache.items())[-limit:]

analyses_cache = AnalysisCache()

# Pydantic models with validation
class AnalyzeResponse(BaseModel):
    thread_id: str = Field(..., description="Unique analysis identifier")
    status: str = Field(..., description="Analysis status")
    message: str = Field(..., description="Status message")

class AnomalyDetail(BaseModel):
    flag_type: str = Field(..., description="Type of anomaly")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Detailed description")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting evidence")

class AuditResponse(BaseModel):
    thread_id: str
    status: str
    fraud_risk_score: float = Field(..., ge=0, le=100)
    risk_level: str
    anomalies: List[AnomalyDetail]
    final_report: str
    recommendations: List[str]
    extracted_data: Optional[Dict[str, Any]] = None
    processing_time: float

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 SpendShield AI starting up...")
    logger.info(f"AI Enabled: {AI_ENABLED}")
    logger.info(f"Upload Directory: {Config.UPLOAD_DIR}")
    logger.info(f"Max File Size: {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB")

# Dashboard endpoint
@app.get("/", include_in_schema=False)
async def dashboard():
    """Serve the interactive dashboard"""
    try:
        return FileResponse("static/index.html")
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Dashboard not found. Please ensure static files are present."}
        )

# Health check with detailed status
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return {
        "status": "healthy",
        "service": "SpendShield AI (Live)",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "ai_enabled": AI_ENABLED,
        "ai_libraries": AI_LIBRARIES_AVAILABLE,
        "upload_dir_exists": os.path.exists(Config.UPLOAD_DIR),
        "cached_analyses": len(analyses_cache.cache),
        "features": {
            "file_upload": True,
            "ai_extraction": AI_ENABLED,
            "mock_mode": not AI_ENABLED,
            "real_time_analysis": True
        }
    }

# Demo endpoint with caching
@lru_cache(maxsize=1)
def get_demo_data():
    """Cached demo data"""
    return {
        "scenario": "Mock Invoice Analysis",
        "document": {
            "vendor": "QuickFix Solutions Ltd",
            "vendor_id": "VND005",
            "invoice_number": "INV-2024-500",
            "amount": 50000.00,
            "item": "Office supplies",
            "quantity": 1000,
            "unit_price": 50.00
        },
        "analysis": {
            "step_1_extraction": {
                "status": "✅ Complete",
                "agent": "Extractor",
                "result": "Document successfully extracted"
            },
            "step_2_verification": {
                "status": "✅ Complete",
                "agent": "Verifier",
                "vendor_exists": False,
                "historical_avg_price": 40.00
            },
            "step_3_anomaly_detection": {
                "status": "✅ Complete",
                "agent": "Anomaly Detector",
                "anomalies": [
                    {
                        "type": "ghost_vendor",
                        "severity": "CRITICAL",
                        "description": "Vendor not found in database"
                    },
                    {
                        "type": "price_inflation",
                        "severity": "HIGH",
                        "description": "25% price inflation detected",
                        "current_price": 50.00,
                        "historical_avg": 40.00,
                        "inflation_pct": 25.0
                    }
                ]
            },
            "step_4_reporting": {
                "status": "✅ Complete",
                "agent": "Reporter",
                "fraud_risk_score": 65,
                "risk_level": "HIGH",
                "recommendation": "REJECT & INVESTIGATE"
            }
        },
        "recommendations": [
            "Verify the legitimacy of QuickFix Solutions Ltd",
            "Investigate the 25% price inflation",
            "Suspend payment pending investigation",
            "Strengthen procurement controls"
        ]
    }

@app.get("/demo")
async def demo():
    """Fraud detection demo data"""
    return get_demo_data()

# Optimized file validation
def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """Validate uploaded file"""
    # Check extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in Config.ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"
    
    # Check size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > Config.MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None

# Real-time document analysis endpoint
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to analyze"),
    department: Optional[str] = Form(None, description="Department name"),
    fiscal_year: Optional[int] = Form(None, description="Fiscal year")
):
    """
    Upload and analyze a document in real-time
    
    - **file**: Invoice, tender, or approval document (PDF, PNG, JPG, JPEG)
    - **department**: Optional department name
    - **fiscal_year**: Optional fiscal year
    """
    
    # Validate file
    is_valid, error_message = validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    start_time = datetime.now()
    thread_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1].lower()
    file_path = os.path.join(Config.UPLOAD_DIR, f"{thread_id}{file_ext}")
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📄 File uploaded: {file.filename} ({thread_id})")
        
        # Process the document
        if AI_ENABLED and file_ext in ['.png', '.jpg', '.jpeg']:
            result = await process_image_with_ai(file_path, thread_id, department, fiscal_year)
        else:
            result = await process_with_mock_data(file_path, thread_id, department, fiscal_year)
        
        # Update processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result["processing_time"] = processing_time
        
        # Store in cache
        analyses_cache.add(thread_id, result)
        
        # Schedule file cleanup in background
        background_tasks.add_task(cleanup_old_files, Config.UPLOAD_DIR, max_age_hours=24)
        
        logger.info(f"✅ Analysis complete in {processing_time:.2f}s - Thread: {thread_id}")
        
        return AnalyzeResponse(
            thread_id=thread_id,
            status="completed",
            message=f"Analysis completed in {processing_time:.2f} seconds"
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing document: {str(e)}", exc_info=True)
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

async def process_image_with_ai(
    file_path: str, 
    thread_id: str, 
    department: Optional[str], 
    fiscal_year: Optional[int]
) -> Dict:
    """Process image using Google Gemini AI with error handling"""
    
    try:
        # Load image
        img = Image.open(file_path)
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Extract data from image
        extraction_prompt = """
        Analyze this invoice/procurement document and extract the following information in valid JSON format:
        {
            "vendor_name": "company name",
            "vendor_id": "vendor ID if present",
            "invoice_number": "invoice/document number",
            "date": "transaction date",
            "total_amount": numeric value,
            "items": [
                {
                    "description": "item description",
                    "quantity": numeric,
                    "unit_price": numeric,
                    "total": numeric
                }
            ],
            "currency": "currency code"
        }
        
        If any field is not found, use null. Be precise and extract only what you see.
        Return ONLY the JSON, no additional text.
        """
        
        response = model.generate_content([extraction_prompt, img])
        extracted_text = response.text
        
        # Parse extracted data with better error handling
        json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
        if json_match:
            try:
                extracted_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response as JSON, using fallback")
                extracted_data = create_fallback_data()
        else:
            extracted_data = create_fallback_data()
        
        # Analyze for anomalies
        anomalies, fraud_score = detect_anomalies(extracted_data)
        risk_level = calculate_risk_level(fraud_score)
        recommendations = generate_recommendations(anomalies, fraud_score)
        
        return {
            "thread_id": thread_id,
            "status": "completed",
            "fraud_risk_score": fraud_score,
            "risk_level": risk_level,
            "anomalies": anomalies,
            "final_report": f"AI Analysis completed. Risk Score: {fraud_score}/100. {len(anomalies)} anomalies detected.",
            "recommendations": recommendations,
            "extracted_data": extracted_data,
            "processing_time": 0.0
        }
        
    except Exception as e:
        logger.error(f"AI processing error: {e}", exc_info=True)
        return await process_with_mock_data(file_path, thread_id, department, fiscal_year)

def create_fallback_data() -> Dict:
    """Create fallback data when extraction fails"""
    return {
        "vendor_name": "Extracted Vendor",
        "vendor_id": None,
        "invoice_number": "EXT-001",
        "total_amount": 10000.00,
        "items": [{"description": "Extracted Item", "quantity": 1, "unit_price": 10000.00, "total": 10000.00}],
        "currency": "USD"
    }

def detect_anomalies(extracted_data: Dict) -> tuple[List[Dict], float]:
    """Detect fraud anomalies and calculate score"""
    anomalies = []
    fraud_score = 0
    
    # Check for high amount
    total_amount = extracted_data.get("total_amount", 0)
    if total_amount > 25000:
        anomalies.append({
            "flag_type": "high_value",
            "severity": "MEDIUM",
            "description": f"High value transaction: ${total_amount:,.2f}",
            "evidence": {"amount": total_amount}
        })
        fraud_score += 20
    
    # Check for missing vendor ID
    if not extracted_data.get("vendor_id"):
        anomalies.append({
            "flag_type": "missing_vendor_id",
            "severity": "HIGH",
            "description": "Vendor ID not found in document",
            "evidence": {"vendor_name": extracted_data.get("vendor_name")}
        })
        fraud_score += 30
    
    # Check for missing invoice number
    if not extracted_data.get("invoice_number"):
        anomalies.append({
            "flag_type": "missing_invoice_number",
            "severity": "HIGH",
            "description": "Invoice number not found",
            "evidence": {}
        })
        fraud_score += 25
    
    return anomalies, fraud_score

def calculate_risk_level(fraud_score: float) -> str:
    """Calculate risk level from fraud score"""
    if fraud_score >= 70:
        return "CRITICAL"
    elif fraud_score >= 40:
        return "HIGH"
    elif fraud_score >= 20:
        return "MEDIUM"
    else:
        return "LOW"

def generate_recommendations(anomalies: List[Dict], fraud_score: float) -> List[str]:
    """Generate actionable recommendations"""
    recommendations = []
    
    if fraud_score >= 70:
        recommendations.append("⛔ REJECT transaction immediately")
        recommendations.append("🔍 Launch full investigation")
    elif fraud_score >= 40:
        recommendations.append("⚠️ Hold payment pending review")
        recommendations.append("📋 Request additional documentation")
    
    if any(a["flag_type"] == "missing_vendor_id" for a in anomalies):
        recommendations.append("✅ Verify vendor registration and credentials")
    
    if any(a["flag_type"] == "high_value" for a in anomalies):
        recommendations.append("👤 Require additional approval from senior management")
    
    if not recommendations:
        recommendations.append("✅ Transaction appears normal - proceed with standard approval")
    
    recommendations.append("📊 Cross-check with procurement records")
    
    return recommendations

async def process_with_mock_data(
    file_path: str, 
    thread_id: str, 
    department: Optional[str], 
    fiscal_year: Optional[int]
) -> Dict:
    """Process with mock data when AI is not available"""
    
    return {
        "thread_id": thread_id,
        "status": "completed",
        "fraud_risk_score": 65.0,
        "risk_level": "HIGH",
        "anomalies": [
            {
                "flag_type": "ghost_vendor",
                "severity": "CRITICAL",
                "description": "Vendor not found in database",
                "evidence": {"vendor_name": "Unknown Vendor"}
            },
            {
                "flag_type": "price_inflation",
                "severity": "HIGH",
                "description": "25% price inflation detected",
                "evidence": {"current_price": 50.00, "historical_avg": 40.00}
            }
        ],
        "final_report": "Mock analysis completed. This is demo data. Configure GOOGLE_API_KEY for real AI analysis.",
        "recommendations": [
            "Verify vendor legitimacy",
            "Investigate price inflation",
            "Suspend payment pending review",
            "Cross-check with procurement records"
        ],
        "extracted_data": {
            "vendor_name": "Mock Vendor Inc",
            "vendor_id": None,
            "total_amount": 50000.00,
            "invoice_number": "MOCK-001",
            "currency": "USD"
        },
        "processing_time": 0.5
    }

# Get audit results
@app.get("/audit/{thread_id}", response_model=AuditResponse)
async def get_audit(thread_id: str):
    """Retrieve audit results for a specific analysis"""
    
    result = analyses_cache.get(thread_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Audit not found for thread_id: {thread_id}"
        )
    
    return AuditResponse(
        thread_id=result["thread_id"],
        status=result["status"],
        fraud_risk_score=result["fraud_risk_score"],
        risk_level=result["risk_level"],
        anomalies=[AnomalyDetail(**a) for a in result["anomalies"]],
        final_report=result["final_report"],
        recommendations=result["recommendations"],
        extracted_data=result.get("extracted_data"),
        processing_time=result.get("processing_time", 0.0)
    )

# List all audits
@app.get("/audits")
async def list_audits(limit: int = 10):
    """List recent audits"""
    
    recent = analyses_cache.list_recent(limit)
    audits = []
    
    for thread_id, result in recent:
        audits.append({
            "thread_id": thread_id,
            "fraud_risk_score": result["fraud_risk_score"],
            "risk_level": result["risk_level"],
            "anomaly_count": len(result["anomalies"]),
            "status": result["status"],
            "timestamp": result.get("timestamp", datetime.now().isoformat())
        })
    
    return {"audits": audits, "total": len(audits)}

# Background task for cleanup
async def cleanup_old_files(directory: str, max_age_hours: int = 24):
    """Clean up old uploaded files"""
    try:
        now = datetime.now()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = now - datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_age.total_seconds() > max_age_hours * 3600:
                    os.remove(filepath)
                    logger.info(f"🗑️ Cleaned up old file: {filename}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("🚀 Starting SpendShield AI (Optimized Live Version)")
    print("=" * 80)
    print()
    print(f"📊 Dashboard: http://localhost:{Config.PORT}")
    print(f"📚 API Docs: http://localhost:{Config.PORT}/docs")
    print(f"🤖 AI Enabled: {AI_ENABLED}")
    print(f"📁 Upload Directory: {Config.UPLOAD_DIR}")
    print(f"📦 Max File Size: {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB")
    print()
    if not AI_ENABLED:
        print("⚠️  Set GOOGLE_API_KEY in .env for real AI analysis")
        print("   Get your key: https://aistudio.google.com/app/apikey")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    uvicorn.run(
        "app.live:app",
        host="0.0.0.0",
        port=Config.PORT,
        reload=True,
        log_level="info"
    )
