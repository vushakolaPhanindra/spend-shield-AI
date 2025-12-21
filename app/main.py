"""
FastAPI backend for SpendShield AI
Provides REST API endpoints for document analysis and audit retrieval
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import uuid
import shutil
from datetime import datetime
from contextlib import asynccontextmanager

from app.db import db
from app.graph import get_compiled_graph


# Pydantic models
class AnalyzeResponse(BaseModel):
    thread_id: str
    status: str
    message: str


class AnomalyResponse(BaseModel):
    flag_type: str
    severity: str
    description: str
    evidence: Dict[str, Any]


class AuditResponse(BaseModel):
    thread_id: str
    status: str
    current_node: str
    fraud_risk_score: float
    anomalies: List[AnomalyResponse]
    final_report: str
    recommendations: List[str]
    extracted_data: Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    errors: List[str]


# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    print("🚀 Starting SpendShield AI...")
    await db.initialize()
    print("✅ Database initialized")
    
    # Ensure upload directory exists
    os.makedirs("uploads", exist_ok=True)
    print("✅ Upload directory ready")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down SpendShield AI...")
    await db.close()
    print("✅ Database connections closed")


# Initialize FastAPI app
app = FastAPI(
    title="SpendShield AI",
    description="Autonomous fraud detection system for public expenditure",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "service": "SpendShield AI",
        "timestamp": datetime.now().isoformat()
    }


# Main analysis endpoint
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    file: UploadFile = File(...),
    department: Optional[str] = Form(None),
    fiscal_year: Optional[int] = Form(None)
):
    """
    Upload a document and initiate fraud analysis
    
    Args:
        file: Document file (PDF, PNG, JPG, JPEG)
        department: Optional department name
        fiscal_year: Optional fiscal year
    
    Returns:
        AnalyzeResponse with thread_id for tracking
    """
    
    # Validate file type
    allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 10MB"
        )
    
    try:
        # Generate unique thread ID
        thread_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{thread_id}{file_ext}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📄 File uploaded: {file_path}")
        
        # Initialize state
        initial_state = {
            "document_path": file_path,
            "thread_id": thread_id,
            "extracted_data": None,
            "extraction_reasoning": "",
            "verification_result": None,
            "verification_reasoning": "",
            "anomalies": [],
            "anomaly_reasoning": "",
            "fraud_risk_score": 0.0,
            "final_report": "",
            "recommendations": [],
            "current_node": "",
            "errors": [],
            "processing_time": 0.0
        }
        
        # Get compiled graph
        graph = get_compiled_graph()
        
        # Run the graph asynchronously
        config = {"configurable": {"thread_id": thread_id}}
        
        # Start processing in background (for production, use task queue like Celery)
        # For now, we'll process synchronously
        start_time = datetime.now()
        
        final_state = None
        async for state in graph.astream(initial_state, config):
            final_state = state
            print(f"📊 Current node: {list(state.keys())}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Analysis complete in {processing_time:.2f}s - Thread: {thread_id}")
        
        return AnalyzeResponse(
            thread_id=thread_id,
            status="completed",
            message=f"Analysis completed in {processing_time:.2f} seconds"
        )
        
    except Exception as e:
        print(f"❌ Error processing document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


# Audit retrieval endpoint
@app.get("/audit/{thread_id}", response_model=AuditResponse)
async def get_audit(thread_id: str):
    """
    Retrieve audit state and history for a specific thread
    
    Args:
        thread_id: Unique thread identifier
    
    Returns:
        AuditResponse with complete audit information
    """
    
    try:
        # Get compiled graph
        graph = get_compiled_graph()
        
        # Get state from checkpoint
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get the latest state
        state = graph.get_state(config)
        
        if not state or not state.values:
            raise HTTPException(
                status_code=404,
                detail=f"Audit not found for thread_id: {thread_id}"
            )
        
        state_values = state.values
        
        # Get flags from database
        flags = await db.get_flags_by_thread(thread_id)
        
        # Convert anomalies to response format
        anomalies = [
            AnomalyResponse(
                flag_type=a['flag_type'],
                severity=a['severity'],
                description=a['description'],
                evidence=a['evidence']
            )
            for a in state_values.get('anomalies', [])
        ]
        
        # Determine status
        current_node = state_values.get('current_node', '')
        if current_node == 'reporter':
            status = 'completed'
        elif state_values.get('errors'):
            status = 'failed'
        else:
            status = 'processing'
        
        return AuditResponse(
            thread_id=thread_id,
            status=status,
            current_node=current_node,
            fraud_risk_score=state_values.get('fraud_risk_score', 0.0),
            anomalies=anomalies,
            final_report=state_values.get('final_report', ''),
            recommendations=state_values.get('recommendations', []),
            extracted_data=state_values.get('extracted_data'),
            verification_result=state_values.get('verification_result'),
            errors=state_values.get('errors', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving audit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving audit: {str(e)}"
        )


# List all audits endpoint
@app.get("/audits")
async def list_audits(limit: int = 10):
    """
    List recent audits
    
    Args:
        limit: Maximum number of audits to return
    
    Returns:
        List of recent audit summaries
    """
    
    try:
        # Query flags table for recent audits
        async with db.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT DISTINCT ON (thread_id)
                        thread_id,
                        fraud_risk_score,
                        flagged_at,
                        COUNT(*) OVER (PARTITION BY thread_id) as anomaly_count
                    FROM flags
                    ORDER BY thread_id, flagged_at DESC
                    LIMIT %s
                """, (limit,))
                
                audits = await cur.fetchall()
        
        return {
            "audits": [
                {
                    "thread_id": audit['thread_id'],
                    "fraud_risk_score": float(audit['fraud_risk_score']) if audit['fraud_risk_score'] else 0.0,
                    "anomaly_count": audit['anomaly_count'],
                    "flagged_at": audit['flagged_at'].isoformat()
                }
                for audit in audits
            ]
        }
        
    except Exception as e:
        print(f"❌ Error listing audits: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing audits: {str(e)}"
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "SpendShield AI",
        "version": "1.0.0",
        "description": "Autonomous fraud detection system for public expenditure",
        "endpoints": {
            "POST /analyze": "Upload document for fraud analysis",
            "GET /audit/{thread_id}": "Retrieve audit results",
            "GET /audits": "List recent audits",
            "GET /health": "Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
