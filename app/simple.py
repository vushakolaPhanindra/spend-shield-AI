"""
SpendShield AI - Simplified API (No Database Required)
This version runs without PostgreSQL for quick testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
import os

# Initialize FastAPI app
app = FastAPI(
    title="SpendShield AI",
    description="Autonomous fraud detection system for public expenditure",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SpendShield AI (Simplified)",
        "timestamp": datetime.now().isoformat(),
        "note": "Running without database - for testing only"
    }

# Dashboard endpoint
@app.get("/")
async def dashboard():
    """Serve the interactive dashboard"""
    return FileResponse("static/index.html")

# API Info endpoint
@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "service": "SpendShield AI",
        "version": "1.0.0 (Simplified)",
        "description": "Autonomous fraud detection system for public expenditure",
        "status": "Running without database",
        "endpoints": {
            "GET /": "Interactive Dashboard",
            "GET /api": "API information",
            "GET /health": "Health check",
            "GET /demo": "Fraud detection demo",
            "GET /docs": "API documentation"
        },
        "setup_instructions": {
            "full_version": "To run the full version with database:",
            "steps": [
                "1. Install PostgreSQL or Docker",
                "2. Start PostgreSQL on port 5432",
                "3. Run the full application with: python -m uvicorn app.main:app --reload"
            ]
        }
    }

# Demo endpoint
@app.get("/demo")
async def demo():
    """Fraud detection demo"""
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

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    
    print("=" * 80)
    print("🚀 Starting SpendShield AI (Simplified Version)")
    print("=" * 80)
    print()
    print(f"API available at: http://localhost:{port}")
    print(f"API docs: http://localhost:{port}/docs")
    print(f"Demo endpoint: http://localhost:{port}/demo")
    print()
    print("Note: This is a simplified version without database")
    print("For full functionality, set up PostgreSQL and use app.main")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    uvicorn.run(
        "app.simple:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
