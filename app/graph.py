"""
LangGraph workflow for SpendShield AI fraud detection
Implements a multi-agent system with Extractor, Verifier, Anomaly Detector, and Reporter nodes
"""

from typing import TypedDict, List, Optional, Annotated
from operator import add
from datetime import datetime
import os
import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
import google.generativeai as genai
from PIL import Image
import PyPDF2

from app.db import db


# Configure Google AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# State Schema
class DocumentData(TypedDict):
    """Extracted document information"""
    document_type: str
    vendor_name: str
    vendor_id: Optional[str]
    amount: float
    date: str
    line_items: List[dict]
    approval_authority: Optional[str]
    reference_number: str


class VerificationResult(TypedDict):
    """Database verification results"""
    vendor_exists: bool
    vendor_registration_date: Optional[str]
    historical_avg_price: Optional[float]
    similar_transactions: List[dict]
    vendor_risk_score: float


class AnomalyFlag(TypedDict):
    """Individual anomaly detection"""
    flag_type: str
    severity: str
    description: str
    evidence: dict


class AuditState(TypedDict):
    """Main state for the LangGraph workflow"""
    # Input
    document_path: str
    thread_id: str
    
    # Extractor outputs
    extracted_data: Optional[DocumentData]
    extraction_reasoning: str
    
    # Verifier outputs
    verification_result: Optional[VerificationResult]
    verification_reasoning: str
    
    # Anomaly Detector outputs
    anomalies: Annotated[List[AnomalyFlag], add]
    anomaly_reasoning: str
    
    # Reporter outputs
    fraud_risk_score: float
    final_report: str
    recommendations: List[str]
    
    # Metadata
    current_node: str
    errors: Annotated[List[str], add]
    processing_time: float


# Agent Nodes

async def extractor_node(state: AuditState) -> AuditState:
    """
    Node 1: Extract structured data from unstructured documents
    Uses Gemini 2.0 Flash multimodal capabilities
    """
    print(f"[EXTRACTOR] Processing document: {state['document_path']}")
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Load document
        document_path = state['document_path']
        
        # Determine document type and load accordingly
        if document_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Image document
            image = Image.open(document_path)
            
            prompt = """
            You are an expert document analyst for a fraud detection system.
            
            Analyze this government procurement document (invoice, tender, or approval) and extract the following information:
            
            1. Document Type: (invoice, tender, or approval)
            2. Vendor Name: The company or individual providing goods/services
            3. Vendor ID: Any vendor identification number (if present)
            4. Total Amount: The total monetary value
            5. Date: Transaction or document date
            6. Line Items: List of items/services with quantities and unit prices
            7. Approval Authority: Name of approving official (if present)
            8. Reference Number: Invoice number, tender ID, or approval code
            
            Provide your reasoning first, then extract the data in JSON format.
            
            Format your response as:
            
            REASONING:
            [Your detailed analysis of the document]
            
            EXTRACTED_DATA:
            {
                "document_type": "invoice",
                "vendor_name": "Company Name",
                "vendor_id": "VND123",
                "amount": 50000.00,
                "date": "2024-01-15",
                "line_items": [
                    {"item": "Office supplies", "quantity": 1000, "unit_price": 50.00}
                ],
                "approval_authority": "John Doe",
                "reference_number": "INV-2024-001"
            }
            """
            
            response = model.generate_content([prompt, image])
            
        elif document_path.lower().endswith('.pdf'):
            # PDF document - extract text and analyze
            with open(document_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
            
            prompt = f"""
            You are an expert document analyst for a fraud detection system.
            
            Analyze this government procurement document text and extract the following information:
            
            Document Text:
            {text_content}
            
            Extract:
            1. Document Type: (invoice, tender, or approval)
            2. Vendor Name: The company or individual providing goods/services
            3. Vendor ID: Any vendor identification number (if present)
            4. Total Amount: The total monetary value
            5. Date: Transaction or document date
            6. Line Items: List of items/services with quantities and unit prices
            7. Approval Authority: Name of approving official (if present)
            8. Reference Number: Invoice number, tender ID, or approval code
            
            Provide your reasoning first, then extract the data in JSON format.
            
            Format your response as:
            
            REASONING:
            [Your detailed analysis of the document]
            
            EXTRACTED_DATA:
            {
                "document_type": "invoice",
                "vendor_name": "Company Name",
                "vendor_id": "VND123",
                "amount": 50000.00,
                "date": "2024-01-15",
                "line_items": [
                    {"item": "Office supplies", "quantity": 1000, "unit_price": 50.00}
                ],
                "approval_authority": "John Doe",
                "reference_number": "INV-2024-001"
            }
            """
            
            response = model.generate_content(prompt)
        
        else:
            raise ValueError(f"Unsupported file format: {document_path}")
        
        # Parse response
        response_text = response.text
        
        # Extract reasoning and data
        reasoning_start = response_text.find("REASONING:")
        data_start = response_text.find("EXTRACTED_DATA:")
        
        if reasoning_start != -1 and data_start != -1:
            reasoning = response_text[reasoning_start + 10:data_start].strip()
            data_json = response_text[data_start + 15:].strip()
            
            # Clean JSON (remove markdown code blocks if present)
            data_json = data_json.replace("```json", "").replace("```", "").strip()
            
            extracted_data = json.loads(data_json)
        else:
            # Fallback: try to parse entire response as JSON
            reasoning = "Automated extraction"
            data_json = response_text.replace("```json", "").replace("```", "").strip()
            extracted_data = json.loads(data_json)
        
        print(f"[EXTRACTOR] Successfully extracted data from document")
        
        return {
            **state,
            "extracted_data": extracted_data,
            "extraction_reasoning": reasoning,
            "current_node": "extractor"
        }
        
    except Exception as e:
        print(f"[EXTRACTOR] Error: {str(e)}")
        return {
            **state,
            "errors": [f"Extraction error: {str(e)}"],
            "current_node": "extractor"
        }


async def verifier_node(state: AuditState) -> AuditState:
    """
    Node 2: Verify extracted data against database
    Cross-checks vendor legitimacy and historical pricing
    """
    print(f"[VERIFIER] Verifying extracted data")
    
    try:
        extracted_data = state.get('extracted_data')
        if not extracted_data:
            raise ValueError("No extracted data available")
        
        vendor_name = extracted_data.get('vendor_name')
        vendor_id = extracted_data.get('vendor_id')
        
        # Initialize Gemini for reasoning
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Query database for vendor
        vendor = None
        if vendor_id:
            vendor = await db.get_vendor_by_id(vendor_id)
        if not vendor and vendor_name:
            vendor = await db.get_vendor_by_name(vendor_name)
        
        vendor_exists = vendor is not None
        vendor_risk_score = vendor.get('risk_score', 0.0) if vendor else 0.0
        vendor_registration_date = str(vendor.get('registration_date')) if vendor else None
        
        # Get historical pricing for line items
        historical_avg_price = None
        if extracted_data.get('line_items'):
            first_item = extracted_data['line_items'][0]
            item_desc = first_item.get('item', '')
            
            if item_desc:
                price_data = await db.get_historical_avg_price(item_desc)
                if price_data and price_data.get('avg_price'):
                    historical_avg_price = float(price_data['avg_price'])
        
        # Get similar transactions
        similar_transactions = []
        if vendor:
            transactions = await db.get_vendor_transactions(vendor['vendor_id'])
            similar_transactions = [
                {
                    'reference_number': t['reference_number'],
                    'date': str(t['transaction_date']),
                    'amount': float(t['amount']),
                    'item': t['item_description']
                }
                for t in transactions
            ]
        
        # Generate reasoning using Gemini
        reasoning_prompt = f"""
        You are a fraud detection analyst verifying vendor information.
        
        Extracted Document Data:
        - Vendor: {vendor_name}
        - Vendor ID: {vendor_id}
        - Amount: ${extracted_data.get('amount', 0)}
        - Items: {extracted_data.get('line_items', [])}
        
        Database Verification Results:
        - Vendor Exists in Database: {vendor_exists}
        - Vendor Registration Date: {vendor_registration_date}
        - Vendor Risk Score: {vendor_risk_score}
        - Historical Average Price: ${historical_avg_price if historical_avg_price else 'N/A'}
        - Similar Past Transactions: {len(similar_transactions)}
        
        Provide a detailed reasoning about the verification results. Consider:
        1. Is the vendor legitimate?
        2. How does the pricing compare to historical data?
        3. Are there any red flags in the vendor's history?
        4. What is the overall risk assessment?
        
        Keep your response concise but thorough (3-5 sentences).
        """
        
        reasoning_response = model.generate_content(reasoning_prompt)
        verification_reasoning = reasoning_response.text.strip()
        
        verification_result = {
            "vendor_exists": vendor_exists,
            "vendor_registration_date": vendor_registration_date,
            "historical_avg_price": historical_avg_price,
            "similar_transactions": similar_transactions,
            "vendor_risk_score": vendor_risk_score
        }
        
        print(f"[VERIFIER] Verification complete - Vendor exists: {vendor_exists}")
        
        return {
            **state,
            "verification_result": verification_result,
            "verification_reasoning": verification_reasoning,
            "current_node": "verifier"
        }
        
    except Exception as e:
        print(f"[VERIFIER] Error: {str(e)}")
        return {
            **state,
            "errors": [f"Verification error: {str(e)}"],
            "current_node": "verifier"
        }


async def anomaly_detector_node(state: AuditState) -> AuditState:
    """
    Node 3: Detect fraud anomalies using rule-based and AI analysis
    Identifies ghost vendors, split bidding, duplicates, and price inflation
    """
    print(f"[ANOMALY DETECTOR] Analyzing for fraud patterns")
    
    try:
        extracted_data = state.get('extracted_data')
        verification_result = state.get('verification_result')
        
        if not extracted_data or not verification_result:
            raise ValueError("Missing required data for anomaly detection")
        
        anomalies = []
        
        # Initialize Gemini for reasoning
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Rule 1: Ghost Vendor Detection
        if not verification_result['vendor_exists']:
            anomalies.append({
                "flag_type": "ghost_vendor",
                "severity": "critical",
                "description": f"Vendor '{extracted_data['vendor_name']}' not found in database",
                "evidence": {
                    "vendor_name": extracted_data['vendor_name'],
                    "vendor_id": extracted_data.get('vendor_id'),
                    "amount": extracted_data['amount']
                }
            })
        elif verification_result['vendor_registration_date']:
            # Check if recently registered with large contract
            from datetime import datetime, timedelta
            reg_date = datetime.fromisoformat(verification_result['vendor_registration_date'])
            if datetime.now() - reg_date < timedelta(days=180) and extracted_data['amount'] > 50000:
                anomalies.append({
                    "flag_type": "ghost_vendor",
                    "severity": "high",
                    "description": f"Recently registered vendor ({verification_result['vendor_registration_date']}) with large contract",
                    "evidence": {
                        "registration_date": verification_result['vendor_registration_date'],
                        "contract_amount": extracted_data['amount'],
                        "days_since_registration": (datetime.now() - reg_date).days
                    }
                })
        
        # Rule 2: Price Inflation Detection
        if verification_result['historical_avg_price'] and extracted_data.get('line_items'):
            for item in extracted_data['line_items']:
                unit_price = item.get('unit_price', 0)
                historical_avg = verification_result['historical_avg_price']
                
                if unit_price > historical_avg * 1.2:  # 20% inflation threshold
                    inflation_pct = ((unit_price - historical_avg) / historical_avg) * 100
                    
                    severity = "critical" if inflation_pct > 50 else "high" if inflation_pct > 30 else "medium"
                    
                    anomalies.append({
                        "flag_type": "price_inflation",
                        "severity": severity,
                        "description": f"Price inflation detected: {inflation_pct:.1f}% above historical average",
                        "evidence": {
                            "item": item.get('item'),
                            "current_price": unit_price,
                            "historical_avg_price": historical_avg,
                            "inflation_percentage": inflation_pct
                        }
                    })
        
        # Rule 3: Duplicate Invoice Detection
        reference_number = extracted_data.get('reference_number')
        if reference_number:
            duplicate = await db.check_duplicate_reference(reference_number)
            if duplicate:
                anomalies.append({
                    "flag_type": "duplicate_invoice",
                    "severity": "critical",
                    "description": f"Duplicate reference number found: {reference_number}",
                    "evidence": {
                        "reference_number": reference_number,
                        "original_date": str(duplicate['transaction_date']),
                        "original_amount": float(duplicate['amount'])
                    }
                })
        
        # Rule 4: High Vendor Risk Score
        if verification_result['vendor_risk_score'] > 0.7:
            anomalies.append({
                "flag_type": "high_risk_vendor",
                "severity": "high",
                "description": f"Vendor has high risk score: {verification_result['vendor_risk_score']:.2f}",
                "evidence": {
                    "vendor_name": extracted_data['vendor_name'],
                    "risk_score": verification_result['vendor_risk_score']
                }
            })
        
        # Generate AI-powered reasoning
        reasoning_prompt = f"""
        You are a fraud detection expert analyzing anomalies in a government procurement document.
        
        Document Summary:
        - Vendor: {extracted_data['vendor_name']}
        - Amount: ${extracted_data['amount']}
        - Reference: {extracted_data.get('reference_number')}
        
        Detected Anomalies ({len(anomalies)}):
        {json.dumps(anomalies, indent=2)}
        
        Provide a concise analysis (3-5 sentences) explaining:
        1. The significance of these anomalies
        2. How they relate to common fraud patterns
        3. The overall fraud risk assessment
        
        Be specific and reference the actual anomalies found.
        """
        
        reasoning_response = model.generate_content(reasoning_prompt)
        anomaly_reasoning = reasoning_response.text.strip()
        
        print(f"[ANOMALY DETECTOR] Found {len(anomalies)} anomalies")
        
        return {
            **state,
            "anomalies": anomalies,
            "anomaly_reasoning": anomaly_reasoning,
            "current_node": "anomaly_detector"
        }
        
    except Exception as e:
        print(f"[ANOMALY DETECTOR] Error: {str(e)}")
        return {
            **state,
            "errors": [f"Anomaly detection error: {str(e)}"],
            "current_node": "anomaly_detector"
        }


async def reporter_node(state: AuditState) -> AuditState:
    """
    Node 4: Generate final fraud risk report
    Calculates risk score and creates comprehensive markdown report
    """
    print(f"[REPORTER] Generating final fraud risk report")
    
    try:
        extracted_data = state.get('extracted_data')
        verification_result = state.get('verification_result')
        anomalies = state.get('anomalies', [])
        
        # Calculate fraud risk score
        base_score = 0
        
        for anomaly in anomalies:
            severity = anomaly['severity']
            if severity == 'critical':
                base_score += 40
            elif severity == 'high':
                base_score += 25
            elif severity == 'medium':
                base_score += 15
            elif severity == 'low':
                base_score += 5
        
        # Apply vendor risk multiplier
        vendor_risk = verification_result.get('vendor_risk_score', 0.0) if verification_result else 0.0
        if vendor_risk > 0.7:
            base_score *= 1.5
        
        fraud_risk_score = min(base_score, 100.0)
        
        # Generate recommendations using Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        recommendations_prompt = f"""
        You are a fraud prevention advisor for government procurement.
        
        Based on this fraud analysis:
        - Fraud Risk Score: {fraud_risk_score:.1f}/100
        - Anomalies Found: {len(anomalies)}
        - Vendor Risk: {vendor_risk:.2f}
        
        Anomalies:
        {json.dumps(anomalies, indent=2)}
        
        Provide 3-5 specific, actionable recommendations for addressing these issues.
        Format as a simple list, one recommendation per line.
        """
        
        recommendations_response = model.generate_content(recommendations_prompt)
        recommendations_text = recommendations_response.text.strip()
        recommendations = [line.strip('- ').strip() for line in recommendations_text.split('\n') if line.strip()]
        
        # Generate markdown report
        risk_level = "🔴 CRITICAL" if fraud_risk_score >= 70 else "🟠 HIGH" if fraud_risk_score >= 40 else "🟡 MEDIUM" if fraud_risk_score >= 20 else "🟢 LOW"
        
        report = f"""# SpendShield AI - Fraud Risk Assessment Report

## Executive Summary

**Risk Level**: {risk_level}  
**Fraud Risk Score**: {fraud_risk_score:.1f}/100  
**Document Reference**: {extracted_data.get('reference_number', 'N/A')}  
**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Document Details

| Field | Value |
|-------|-------|
| **Document Type** | {extracted_data.get('document_type', 'N/A')} |
| **Vendor Name** | {extracted_data.get('vendor_name', 'N/A')} |
| **Vendor ID** | {extracted_data.get('vendor_id', 'N/A')} |
| **Total Amount** | ${extracted_data.get('amount', 0):,.2f} |
| **Transaction Date** | {extracted_data.get('date', 'N/A')} |
| **Approval Authority** | {extracted_data.get('approval_authority', 'N/A')} |

---

## Verification Results

| Metric | Result |
|--------|--------|
| **Vendor in Database** | {'✅ Yes' if verification_result.get('vendor_exists') else '❌ No'} |
| **Vendor Registration Date** | {verification_result.get('vendor_registration_date', 'N/A')} |
| **Vendor Risk Score** | {verification_result.get('vendor_risk_score', 0.0):.2f} |
| **Historical Avg Price** | ${verification_result.get('historical_avg_price', 0.0):.2f if verification_result.get('historical_avg_price') else 'N/A'} |
| **Similar Transactions** | {len(verification_result.get('similar_transactions', []))} |

---

## Anomalies Detected ({len(anomalies)})

"""
        
        if anomalies:
            for i, anomaly in enumerate(anomalies, 1):
                severity_emoji = "🔴" if anomaly['severity'] == 'critical' else "🟠" if anomaly['severity'] == 'high' else "🟡" if anomaly['severity'] == 'medium' else "🟢"
                report += f"""
### {i}. {severity_emoji} {anomaly['flag_type'].replace('_', ' ').title()}

**Severity**: {anomaly['severity'].upper()}  
**Description**: {anomaly['description']}

**Evidence**:
```json
{json.dumps(anomaly['evidence'], indent=2)}
```

---
"""
        else:
            report += "\n✅ No anomalies detected. Document appears legitimate.\n\n---\n"
        
        report += f"""
## Recommendations

"""
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"""
---

## Analysis Reasoning

### Extraction Phase
{state.get('extraction_reasoning', 'N/A')}

### Verification Phase
{state.get('verification_reasoning', 'N/A')}

### Anomaly Detection Phase
{state.get('anomaly_reasoning', 'N/A')}

---

*Report generated by SpendShield AI - Autonomous Fraud Detection System*
"""
        
        # Save flags to database
        thread_id = state.get('thread_id')
        for anomaly in anomalies:
            await db.save_flag(
                thread_id=thread_id,
                vendor_id=extracted_data.get('vendor_id'),
                reference_number=extracted_data.get('reference_number'),
                flag_type=anomaly['flag_type'],
                severity=anomaly['severity'],
                description=anomaly['description'],
                evidence=anomaly['evidence'],
                fraud_risk_score=fraud_risk_score
            )
        
        print(f"[REPORTER] Report generated - Risk Score: {fraud_risk_score:.1f}/100")
        
        return {
            **state,
            "fraud_risk_score": fraud_risk_score,
            "final_report": report,
            "recommendations": recommendations,
            "current_node": "reporter"
        }
        
    except Exception as e:
        print(f"[REPORTER] Error: {str(e)}")
        return {
            **state,
            "errors": [f"Report generation error: {str(e)}"],
            "current_node": "reporter"
        }


# Build the graph
def create_fraud_detection_graph():
    """Create the LangGraph workflow for fraud detection"""
    
    workflow = StateGraph(AuditState)
    
    # Add nodes
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("anomaly_detector", anomaly_detector_node)
    workflow.add_node("reporter", reporter_node)
    
    # Define edges (linear flow)
    workflow.set_entry_point("extractor")
    workflow.add_edge("extractor", "verifier")
    workflow.add_edge("verifier", "anomaly_detector")
    workflow.add_edge("anomaly_detector", "reporter")
    workflow.add_edge("reporter", END)
    
    return workflow


# Compile graph with checkpoint
def get_compiled_graph():
    """Get compiled graph with PostgreSQL checkpointing"""
    workflow = create_fraud_detection_graph()
    
    # Create PostgreSQL checkpointer
    checkpoint_conn_string = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/spendshield"
    )
    
    checkpointer = PostgresSaver.from_conn_string(checkpoint_conn_string)
    
    # Compile with checkpointer
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    
    return compiled_graph
