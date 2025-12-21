"""
Test script for SpendShield AI
Creates a mock invoice and tests the fraud detection workflow
"""

import asyncio
import os
from pathlib import Path

# Set environment variable for testing
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', 'test_key')
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/spendshield'

from app.db import db
from app.graph import get_compiled_graph


async def test_fraud_detection():
    """Test the fraud detection workflow with a mock invoice"""
    
    print("=" * 80)
    print("SpendShield AI - Test Fraud Detection Workflow")
    print("=" * 80)
    
    # Initialize database
    print("\n1. Initializing database...")
    await db.initialize()
    print("✅ Database initialized")
    
    # Create test invoice path
    test_invoice_path = "tests/sample_invoice.png"
    
    if not os.path.exists(test_invoice_path):
        print(f"\n⚠️  Test invoice not found at {test_invoice_path}")
        print("Please create a sample invoice image or update the path")
        return
    
    # Initialize state
    thread_id = "test-thread-001"
    initial_state = {
        "document_path": test_invoice_path,
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
    
    print(f"\n2. Starting fraud detection analysis...")
    print(f"   Thread ID: {thread_id}")
    print(f"   Document: {test_invoice_path}")
    
    # Get compiled graph
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph
    print("\n3. Processing through agent nodes...")
    
    final_state = None
    async for state in graph.astream(initial_state, config):
        node_name = list(state.keys())[0] if state else "unknown"
        node_state = state.get(node_name, {})
        current_node = node_state.get('current_node', node_name)
        
        print(f"\n   📊 Node: {current_node.upper()}")
        
        if current_node == 'extractor':
            extracted = node_state.get('extracted_data')
            if extracted:
                print(f"      Vendor: {extracted.get('vendor_name')}")
                print(f"      Amount: ${extracted.get('amount', 0):,.2f}")
                print(f"      Reference: {extracted.get('reference_number')}")
        
        elif current_node == 'verifier':
            verification = node_state.get('verification_result')
            if verification:
                print(f"      Vendor Exists: {verification.get('vendor_exists')}")
                print(f"      Risk Score: {verification.get('vendor_risk_score', 0):.2f}")
                print(f"      Historical Avg Price: ${verification.get('historical_avg_price', 0):.2f}")
        
        elif current_node == 'anomaly_detector':
            anomalies = node_state.get('anomalies', [])
            print(f"      Anomalies Found: {len(anomalies)}")
            for anomaly in anomalies:
                print(f"         - {anomaly['flag_type']}: {anomaly['severity']}")
        
        elif current_node == 'reporter':
            fraud_score = node_state.get('fraud_risk_score', 0)
            recommendations = node_state.get('recommendations', [])
            print(f"      Fraud Risk Score: {fraud_score:.1f}/100")
            print(f"      Recommendations: {len(recommendations)}")
        
        final_state = node_state
    
    # Display final report
    if final_state:
        print("\n" + "=" * 80)
        print("FINAL FRAUD RISK REPORT")
        print("=" * 80)
        print(final_state.get('final_report', 'No report generated'))
        print("=" * 80)
        
        # Check for errors
        errors = final_state.get('errors', [])
        if errors:
            print("\n⚠️  Errors encountered:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("\n✅ Analysis completed successfully!")
    
    # Close database
    await db.close()
    print("\n✅ Database connections closed")


async def test_price_inflation_scenario():
    """
    Test specific scenario: 20% price inflation detection
    This is the mock test required in Phase 3
    """
    
    print("\n" + "=" * 80)
    print("Mock Test: 20% Price Inflation Detection")
    print("=" * 80)
    
    # Initialize database
    await db.initialize()
    
    # Create mock extracted data with inflated prices
    # Historical avg for "Office supplies" is ~$40 (from seeded data)
    # We'll test with $50 (25% inflation)
    
    mock_state = {
        "document_path": "mock_invoice.png",
        "thread_id": "mock-test-inflation",
        "extracted_data": {
            "document_type": "invoice",
            "vendor_name": "Reliable Office Supplies Inc",
            "vendor_id": "VND001",
            "amount": 50000.00,
            "date": "2024-12-20",
            "line_items": [
                {
                    "item": "Office supplies - paper, pens, folders",
                    "quantity": 1000,
                    "unit_price": 50.00  # 25% above historical avg of $40
                }
            ],
            "approval_authority": "Test Manager",
            "reference_number": "INV-TEST-2024-999"
        },
        "extraction_reasoning": "Mock data for testing",
        "verification_result": None,
        "verification_reasoning": "",
        "anomalies": [],
        "anomaly_reasoning": "",
        "fraud_risk_score": 0.0,
        "final_report": "",
        "recommendations": [],
        "current_node": "extractor",
        "errors": [],
        "processing_time": 0.0
    }
    
    # Import nodes directly for testing
    from app.graph import verifier_node, anomaly_detector_node
    
    # Run verifier
    print("\n1. Running Verifier Node...")
    verified_state = await verifier_node(mock_state)
    
    verification = verified_state.get('verification_result')
    if verification:
        print(f"   ✅ Vendor Found: {verification['vendor_exists']}")
        print(f"   ✅ Historical Avg Price: ${verification['historical_avg_price']:.2f}")
    
    # Run anomaly detector
    print("\n2. Running Anomaly Detector Node...")
    anomaly_state = await anomaly_detector_node(verified_state)
    
    anomalies = anomaly_state.get('anomalies', [])
    print(f"\n   Found {len(anomalies)} anomalies:")
    
    # Check for price inflation detection
    price_inflation_found = False
    for anomaly in anomalies:
        print(f"\n   🚨 {anomaly['flag_type'].upper()}")
        print(f"      Severity: {anomaly['severity']}")
        print(f"      Description: {anomaly['description']}")
        
        if anomaly['flag_type'] == 'price_inflation':
            price_inflation_found = True
            evidence = anomaly['evidence']
            print(f"      Current Price: ${evidence['current_price']:.2f}")
            print(f"      Historical Avg: ${evidence['historical_avg_price']:.2f}")
            print(f"      Inflation: {evidence['inflation_percentage']:.1f}%")
    
    # Verify test passed
    print("\n" + "=" * 80)
    if price_inflation_found:
        print("✅ TEST PASSED: 20% price inflation correctly detected!")
    else:
        print("❌ TEST FAILED: Price inflation not detected")
    print("=" * 80)
    
    await db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--mock":
        # Run mock test
        asyncio.run(test_price_inflation_scenario())
    else:
        # Run full test
        asyncio.run(test_fraud_detection())
