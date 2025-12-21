"""
Database initialization and management for SpendShield AI
Uses PGlite-compatible PostgreSQL for vendor and expenditure tracking
"""

import os
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import json


class Database:
    """Database manager for SpendShield AI"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/spendshield"
        )
        self.pool: Optional[ConnectionPool] = None
    
    async def initialize(self):
        """Initialize connection pool and create tables"""
        # Create connection pool
        self.pool = ConnectionPool(
            self.connection_string,
            min_size=2,
            max_size=10,
            kwargs={"row_factory": dict_row}
        )
        
        # Create tables
        await self.create_tables()
        
        # Seed initial data
        await self.seed_data()
    
    async def create_tables(self):
        """Create database tables if they don't exist"""
        
        vendors_table = """
        CREATE TABLE IF NOT EXISTS vendors (
            vendor_id VARCHAR(50) PRIMARY KEY,
            vendor_name VARCHAR(255) NOT NULL,
            registration_date DATE NOT NULL,
            business_type VARCHAR(100),
            contact_email VARCHAR(255),
            contact_phone VARCHAR(50),
            address TEXT,
            tax_id VARCHAR(50),
            risk_score FLOAT DEFAULT 0.0,
            total_contracts INTEGER DEFAULT 0,
            total_value DECIMAL(15, 2) DEFAULT 0.0,
            is_blacklisted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_vendor_name ON vendors(vendor_name);
        CREATE INDEX IF NOT EXISTS idx_risk_score ON vendors(risk_score);
        """
        
        past_expenditures_table = """
        CREATE TABLE IF NOT EXISTS past_expenditures (
            expenditure_id SERIAL PRIMARY KEY,
            vendor_id VARCHAR(50) REFERENCES vendors(vendor_id),
            document_type VARCHAR(50) NOT NULL,
            reference_number VARCHAR(100) UNIQUE NOT NULL,
            transaction_date DATE NOT NULL,
            amount DECIMAL(15, 2) NOT NULL,
            item_description TEXT,
            quantity INTEGER,
            unit_price DECIMAL(15, 2),
            approval_authority VARCHAR(255),
            department VARCHAR(255),
            fiscal_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_vendor_expenditure ON past_expenditures(vendor_id);
        CREATE INDEX IF NOT EXISTS idx_reference_number ON past_expenditures(reference_number);
        CREATE INDEX IF NOT EXISTS idx_transaction_date ON past_expenditures(transaction_date);
        CREATE INDEX IF NOT EXISTS idx_item_description ON past_expenditures(item_description);
        """
        
        flags_table = """
        CREATE TABLE IF NOT EXISTS flags (
            flag_id SERIAL PRIMARY KEY,
            thread_id VARCHAR(100) NOT NULL,
            vendor_id VARCHAR(50),
            reference_number VARCHAR(100),
            flag_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            description TEXT NOT NULL,
            evidence JSONB,
            fraud_risk_score FLOAT,
            flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed BOOLEAN DEFAULT FALSE,
            reviewer_notes TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_thread_id ON flags(thread_id);
        CREATE INDEX IF NOT EXISTS idx_flag_type ON flags(flag_type);
        CREATE INDEX IF NOT EXISTS idx_severity ON flags(severity);
        CREATE INDEX IF NOT EXISTS idx_flagged_at ON flags(flagged_at);
        """
        
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(vendors_table)
                await cur.execute(past_expenditures_table)
                await cur.execute(flags_table)
                await conn.commit()
    
    async def seed_data(self):
        """Seed database with sample data for testing"""
        
        # Check if data already exists
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) as count FROM vendors")
                result = await cur.fetchone()
                if result and result['count'] > 0:
                    return  # Data already seeded
        
        # Sample vendors
        vendors = [
            {
                'vendor_id': 'VND001',
                'vendor_name': 'Reliable Office Supplies Inc',
                'registration_date': '2020-01-15',
                'business_type': 'Office Supplies',
                'contact_email': 'contact@reliableoffice.com',
                'contact_phone': '+1-555-0101',
                'address': '123 Business St, Commerce City, ST 12345',
                'tax_id': 'TAX-001-2020',
                'risk_score': 0.1,
                'total_contracts': 45,
                'total_value': 250000.00,
                'is_blacklisted': False
            },
            {
                'vendor_id': 'VND002',
                'vendor_name': 'TechPro Solutions',
                'registration_date': '2019-06-20',
                'business_type': 'IT Services',
                'contact_email': 'info@techpro.com',
                'contact_phone': '+1-555-0202',
                'address': '456 Tech Ave, Silicon Valley, ST 54321',
                'tax_id': 'TAX-002-2019',
                'risk_score': 0.2,
                'total_contracts': 30,
                'total_value': 500000.00,
                'is_blacklisted': False
            },
            {
                'vendor_id': 'VND003',
                'vendor_name': 'Budget Furniture Co',
                'registration_date': '2021-03-10',
                'business_type': 'Furniture',
                'contact_email': 'sales@budgetfurniture.com',
                'contact_phone': '+1-555-0303',
                'address': '789 Furniture Blvd, Hometown, ST 67890',
                'tax_id': 'TAX-003-2021',
                'risk_score': 0.3,
                'total_contracts': 20,
                'total_value': 150000.00,
                'is_blacklisted': False
            },
            {
                'vendor_id': 'VND004',
                'vendor_name': 'Shady Enterprises LLC',
                'registration_date': '2024-11-01',
                'business_type': 'General Supplies',
                'contact_email': 'contact@shadyent.com',
                'contact_phone': None,
                'address': None,
                'tax_id': 'TAX-004-2024',
                'risk_score': 0.8,
                'total_contracts': 2,
                'total_value': 75000.00,
                'is_blacklisted': False
            }
        ]
        
        # Sample past expenditures
        expenditures = [
            # Reliable Office Supplies - Historical data
            {
                'vendor_id': 'VND001',
                'document_type': 'invoice',
                'reference_number': 'INV-2023-001',
                'transaction_date': '2023-01-15',
                'amount': 40000.00,
                'item_description': 'Office supplies - paper, pens, folders',
                'quantity': 1000,
                'unit_price': 40.00,
                'approval_authority': 'John Smith',
                'department': 'Administration',
                'fiscal_year': 2023
            },
            {
                'vendor_id': 'VND001',
                'document_type': 'invoice',
                'reference_number': 'INV-2023-045',
                'transaction_date': '2023-06-20',
                'amount': 38000.00,
                'item_description': 'Office supplies - paper, pens, folders',
                'quantity': 1000,
                'unit_price': 38.00,
                'approval_authority': 'Jane Doe',
                'department': 'Administration',
                'fiscal_year': 2023
            },
            {
                'vendor_id': 'VND001',
                'document_type': 'invoice',
                'reference_number': 'INV-2024-012',
                'transaction_date': '2024-02-10',
                'amount': 42000.00,
                'item_description': 'Office supplies - paper, pens, folders',
                'quantity': 1000,
                'unit_price': 42.00,
                'approval_authority': 'John Smith',
                'department': 'Administration',
                'fiscal_year': 2024
            },
            # TechPro Solutions
            {
                'vendor_id': 'VND002',
                'document_type': 'invoice',
                'reference_number': 'INV-2023-078',
                'transaction_date': '2023-08-15',
                'amount': 120000.00,
                'item_description': 'IT consulting services',
                'quantity': 1,
                'unit_price': 120000.00,
                'approval_authority': 'CTO Office',
                'department': 'IT',
                'fiscal_year': 2023
            },
            # Budget Furniture
            {
                'vendor_id': 'VND003',
                'document_type': 'invoice',
                'reference_number': 'INV-2023-090',
                'transaction_date': '2023-09-01',
                'amount': 25000.00,
                'item_description': 'Office desks and chairs',
                'quantity': 50,
                'unit_price': 500.00,
                'approval_authority': 'Facilities Manager',
                'department': 'Facilities',
                'fiscal_year': 2023
            }
        ]
        
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                # Insert vendors
                for vendor in vendors:
                    await cur.execute("""
                        INSERT INTO vendors (
                            vendor_id, vendor_name, registration_date, business_type,
                            contact_email, contact_phone, address, tax_id, risk_score,
                            total_contracts, total_value, is_blacklisted
                        ) VALUES (
                            %(vendor_id)s, %(vendor_name)s, %(registration_date)s, %(business_type)s,
                            %(contact_email)s, %(contact_phone)s, %(address)s, %(tax_id)s, %(risk_score)s,
                            %(total_contracts)s, %(total_value)s, %(is_blacklisted)s
                        )
                    """, vendor)
                
                # Insert expenditures
                for exp in expenditures:
                    await cur.execute("""
                        INSERT INTO past_expenditures (
                            vendor_id, document_type, reference_number, transaction_date,
                            amount, item_description, quantity, unit_price,
                            approval_authority, department, fiscal_year
                        ) VALUES (
                            %(vendor_id)s, %(document_type)s, %(reference_number)s, %(transaction_date)s,
                            %(amount)s, %(item_description)s, %(quantity)s, %(unit_price)s,
                            %(approval_authority)s, %(department)s, %(fiscal_year)s
                        )
                    """, exp)
                
                await conn.commit()
    
    async def get_vendor_by_name(self, vendor_name: str) -> Optional[Dict[str, Any]]:
        """Get vendor information by name (case-insensitive)"""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM vendors WHERE vendor_name ILIKE %s",
                    (f"%{vendor_name}%",)
                )
                return await cur.fetchone()
    
    async def get_vendor_by_id(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        """Get vendor information by ID"""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM vendors WHERE vendor_id = %s",
                    (vendor_id,)
                )
                return await cur.fetchone()
    
    async def get_historical_avg_price(self, item_description: str, months: int = 24) -> Optional[Dict[str, Any]]:
        """Get historical average price for similar items"""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT 
                        AVG(unit_price) as avg_price,
                        MIN(unit_price) as min_price,
                        MAX(unit_price) as max_price,
                        COUNT(*) as transaction_count
                    FROM past_expenditures
                    WHERE item_description ILIKE %s
                    AND transaction_date >= CURRENT_DATE - INTERVAL '%s months'
                """, (f"%{item_description}%", months))
                return await cur.fetchone()
    
    async def get_vendor_transactions(self, vendor_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions for a vendor"""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT * FROM past_expenditures
                    WHERE vendor_id = %s
                    ORDER BY transaction_date DESC
                    LIMIT %s
                """, (vendor_id, limit))
                return await cur.fetchall()
    
    async def check_duplicate_reference(self, reference_number: str) -> Optional[Dict[str, Any]]:
        """Check if reference number already exists"""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM past_expenditures WHERE reference_number = %s",
                    (reference_number,)
                )
                return await cur.fetchone()
    
    async def save_flag(self, thread_id: str, vendor_id: Optional[str], 
                       reference_number: Optional[str], flag_type: str,
                       severity: str, description: str, evidence: Dict[str, Any],
                       fraud_risk_score: float):
        """Save an anomaly flag to the database"""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO flags (
                        thread_id, vendor_id, reference_number, flag_type,
                        severity, description, evidence, fraud_risk_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    thread_id, vendor_id, reference_number, flag_type,
                    severity, description, json.dumps(evidence), fraud_risk_score
                ))
                await conn.commit()
    
    async def get_flags_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all flags for a specific thread"""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM flags WHERE thread_id = %s ORDER BY flagged_at DESC",
                    (thread_id,)
                )
                return await cur.fetchall()
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()


# Global database instance
db = Database()
