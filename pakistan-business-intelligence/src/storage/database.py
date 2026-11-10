"""
SQLite Database manager for Pakistan Business Intelligence System.
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from .models import (
    CompanyModel,
    ExecutiveModel,
    BusinessContactModel,
    SourceModel,
    VerificationHistoryModel,
    BatchProgressModel,
    FailedRecordModel,
    current_iso_time,
)


class DatabaseManager:
    """Manages SQLite schema, records, relationships and transactions."""

    def __init__(self, db_path: str = "database/pakistan_business_intelligence.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        """Create all tables with appropriate indexes and constraints."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Companies Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                company_type TEXT DEFAULT 'Private Limited',
                industry TEXT,
                city TEXT,
                province TEXT,
                country TEXT DEFAULT 'Pakistan',
                official_website TEXT,
                normalized_domain TEXT,
                authenticity_status TEXT DEFAULT 'Requires review',
                authenticity_category TEXT DEFAULT 'C',
                authenticity_score REAL DEFAULT 0.0,
                secp_registered INTEGER DEFAULT 0,
                secp_registration_no TEXT,
                stock_symbol TEXT,
                source_url TEXT,
                discovery_source TEXT,
                first_discovered_at TEXT,
                last_verified_at TEXT,
                review_status TEXT DEFAULT 'Requires Review',
                notes TEXT
            );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_normalized_name ON companies(normalized_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(normalized_domain);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_auth_cat ON companies(authenticity_category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_review_stat ON companies(review_status);")

            # 2. Executives Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS executives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                executive_id TEXT UNIQUE NOT NULL,
                company_id TEXT NOT NULL,
                name TEXT NOT NULL,
                designation TEXT NOT NULL,
                normalized_role TEXT DEFAULT 'Other',
                is_ceo_or_founder INTEGER DEFAULT 0,
                linkedin_url TEXT,
                verification_status TEXT DEFAULT 'Unavailable',
                verification_score REAL DEFAULT 0.0,
                source_url TEXT,
                evidence_text TEXT,
                first_discovered_at TEXT,
                last_verified_at TEXT,
                is_current INTEGER DEFAULT 1,
                FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
            );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_executives_company_id ON executives(company_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_executives_role ON executives(normalized_role);")

            # 3. Business Contacts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id TEXT UNIQUE NOT NULL,
                company_id TEXT NOT NULL,
                executive_id TEXT,
                email TEXT,
                email_type TEXT DEFAULT 'Unavailable',
                email_verification_status TEXT DEFAULT 'Unavailable',
                email_mx_host TEXT,
                phone TEXT,
                normalized_phone TEXT,
                phone_type TEXT DEFAULT 'Unavailable',
                phone_verification_status TEXT DEFAULT 'Unavailable',
                contact_source_url TEXT,
                evidence_snippet TEXT,
                confidence_score REAL DEFAULT 0.0,
                first_discovered_at TEXT,
                last_verified_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
                FOREIGN KEY (executive_id) REFERENCES executives(executive_id) ON DELETE SET NULL
            );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON business_contacts(company_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_email ON business_contacts(email);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_phone ON business_contacts(phone);")

            # 4. Sources Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT UNIQUE NOT NULL,
                source_name TEXT NOT NULL,
                source_type TEXT,
                tier INTEGER DEFAULT 1,
                base_url TEXT,
                description TEXT,
                is_official INTEGER DEFAULT 1,
                records_count INTEGER DEFAULT 0,
                last_accessed_at TEXT
            );
            """)

            # 5. Verification History Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                verification_type TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT,
                score REAL,
                evidence_details TEXT,
                verified_at TEXT
            );
            """)

            # 6. Discovery Jobs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS discovery_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'running',
                target_count INTEGER DEFAULT 1000,
                discovered_count INTEGER DEFAULT 0,
                confirmed_count INTEGER DEFAULT 0,
                requires_review_count INTEGER DEFAULT 0,
                start_time TEXT,
                end_time TEXT,
                config_json TEXT
            );
            """)

            # 7. Batch Progress Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                batch_number INTEGER NOT NULL,
                batch_start_index INTEGER,
                batch_end_index INTEGER,
                companies_processed INTEGER,
                confirmed_added INTEGER,
                duplicates_skipped INTEGER,
                failed_count INTEGER,
                checkpoint_excel_path TEXT,
                processed_at TEXT,
                notes TEXT
            );
            """)

            # 8. Failed Records Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS failed_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                attempted_url TEXT,
                failure_stage TEXT,
                error_reason TEXT,
                source_url TEXT,
                attempted_at TEXT
            );
            """)

            conn.commit()

    def get_next_company_id(self) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM companies")
            count = cursor.fetchone()[0]
            return f"PK-COMP-{count + 1:04d}"

    def get_next_executive_id(self) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM executives")
            count = cursor.fetchone()[0]
            return f"PK-EXEC-{count + 1:04d}"

    def get_next_contact_id(self) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM business_contacts")
            count = cursor.fetchone()[0]
            return f"PK-CONT-{count + 1:04d}"

    def insert_or_update_company(self, company: CompanyModel) -> str:
        """Insert company or update if existing by company_id, preserving history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT company_id, authenticity_status, authenticity_score FROM companies WHERE company_id = ?", (company.company_id,))
            row = cursor.fetchone()

            if row:
                old_status = row["authenticity_status"]
                cursor.execute("""
                UPDATE companies SET
                    company_name = ?,
                    normalized_name = ?,
                    company_type = ?,
                    industry = ?,
                    city = ?,
                    province = ?,
                    country = ?,
                    official_website = ?,
                    normalized_domain = ?,
                    authenticity_status = ?,
                    authenticity_category = ?,
                    authenticity_score = ?,
                    secp_registered = ?,
                    secp_registration_no = ?,
                    stock_symbol = ?,
                    source_url = ?,
                    discovery_source = ?,
                    last_verified_at = ?,
                    review_status = ?,
                    notes = ?
                WHERE company_id = ?
                """, (
                    company.company_name,
                    company.normalized_name,
                    company.company_type,
                    company.industry,
                    company.city,
                    company.province,
                    company.country,
                    company.official_website,
                    company.normalized_domain,
                    company.authenticity_status,
                    company.authenticity_category,
                    company.authenticity_score,
                    company.secp_registered,
                    company.secp_registration_no,
                    company.stock_symbol,
                    company.source_url,
                    company.discovery_source,
                    company.last_verified_at,
                    company.review_status,
                    company.notes,
                    company.company_id,
                ))

                if old_status != company.authenticity_status:
                    self.record_verification_history(
                        "company",
                        company.company_id,
                        "status_update",
                        old_status,
                        company.authenticity_status,
                        company.authenticity_score,
                        f"Updated company details from source: {company.discovery_source}"
                    )
            else:
                cursor.execute("""
                INSERT INTO companies (
                    company_id, company_name, normalized_name, company_type, industry,
                    city, province, country, official_website, normalized_domain,
                    authenticity_status, authenticity_category, authenticity_score,
                    secp_registered, secp_registration_no, stock_symbol, source_url,
                    discovery_source, first_discovered_at, last_verified_at, review_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    company.company_id, company.company_name, company.normalized_name,
                    company.company_type, company.industry, company.city, company.province,
                    company.country, company.official_website, company.normalized_domain,
                    company.authenticity_status, company.authenticity_category, company.authenticity_score,
                    company.secp_registered, company.secp_registration_no, company.stock_symbol,
                    company.source_url, company.discovery_source, company.first_discovered_at,
                    company.last_verified_at, company.review_status, company.notes
                ))
            conn.commit()
            return company.company_id

    def insert_or_update_executive(self, executive: ExecutiveModel) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT executive_id, designation, verification_status FROM executives WHERE executive_id = ?", (executive.executive_id,))
            row = cursor.fetchone()

            if row:
                old_status = row["verification_status"]
                cursor.execute("""
                UPDATE executives SET
                    company_id = ?,
                    name = ?,
                    designation = ?,
                    normalized_role = ?,
                    is_ceo_or_founder = ?,
                    linkedin_url = ?,
                    verification_status = ?,
                    verification_score = ?,
                    source_url = ?,
                    evidence_text = ?,
                    last_verified_at = ?,
                    is_current = ?
                WHERE executive_id = ?
                """, (
                    executive.company_id, executive.name, executive.designation,
                    executive.normalized_role, executive.is_ceo_or_founder, executive.linkedin_url,
                    executive.verification_status, executive.verification_score, executive.source_url,
                    executive.evidence_text, executive.last_verified_at, executive.is_current,
                    executive.executive_id
                ))
                if old_status != executive.verification_status:
                    self.record_verification_history(
                        "executive", executive.executive_id, "executive_verification",
                        old_status, executive.verification_status, executive.verification_score,
                        f"Executive {executive.name} ({executive.designation}) verification updated"
                    )
            else:
                cursor.execute("""
                INSERT INTO executives (
                    executive_id, company_id, name, designation, normalized_role,
                    is_ceo_or_founder, linkedin_url, verification_status, verification_score,
                    source_url, evidence_text, first_discovered_at, last_verified_at, is_current
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    executive.executive_id, executive.company_id, executive.name, executive.designation,
                    executive.normalized_role, executive.is_ceo_or_founder, executive.linkedin_url,
                    executive.verification_status, executive.verification_score, executive.source_url,
                    executive.evidence_text, executive.first_discovered_at, executive.last_verified_at,
                    executive.is_current
                ))
            conn.commit()
            return executive.executive_id

    def insert_or_update_contact(self, contact: BusinessContactModel) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT contact_id, email, phone FROM business_contacts WHERE contact_id = ?", (contact.contact_id,))
            row = cursor.fetchone()

            if row:
                cursor.execute("""
                UPDATE business_contacts SET
                    company_id = ?,
                    executive_id = ?,
                    email = ?,
                    email_type = ?,
                    email_verification_status = ?,
                    email_mx_host = ?,
                    phone = ?,
                    normalized_phone = ?,
                    phone_type = ?,
                    phone_verification_status = ?,
                    contact_source_url = ?,
                    evidence_snippet = ?,
                    confidence_score = ?,
                    last_verified_at = ?,
                    is_active = ?
                WHERE contact_id = ?
                """, (
                    contact.company_id, contact.executive_id, contact.email, contact.email_type,
                    contact.email_verification_status, contact.email_mx_host, contact.phone,
                    contact.normalized_phone, contact.phone_type, contact.phone_verification_status,
                    contact.contact_source_url, contact.evidence_snippet, contact.confidence_score,
                    contact.last_verified_at, contact.is_active, contact.contact_id
                ))
            else:
                cursor.execute("""
                INSERT INTO business_contacts (
                    contact_id, company_id, executive_id, email, email_type,
                    email_verification_status, email_mx_host, phone, normalized_phone,
                    phone_type, phone_verification_status, contact_source_url, evidence_snippet,
                    confidence_score, first_discovered_at, last_verified_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contact.contact_id, contact.company_id, contact.executive_id, contact.email,
                    contact.email_type, contact.email_verification_status, contact.email_mx_host,
                    contact.phone, contact.normalized_phone, contact.phone_type,
                    contact.phone_verification_status, contact.contact_source_url, contact.evidence_snippet,
                    contact.confidence_score, contact.first_discovered_at, contact.last_verified_at,
                    contact.is_active
                ))
            conn.commit()
            return contact.contact_id

    def register_source(self, source: SourceModel) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO sources (
                source_id, source_name, source_type, tier, base_url, description,
                is_official, records_count, last_accessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source.source_id, source.source_name, source.source_type, source.tier,
                source.base_url, source.description, source.is_official, source.records_count,
                source.last_accessed_at
            ))
            conn.commit()

    def record_verification_history(self, entity_type: str, entity_id: str, verification_type: str,
                                    old_status: str, new_status: str, score: float, evidence_details: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO verification_history (
                entity_type, entity_id, verification_type, old_status, new_status, score, evidence_details, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_type, entity_id, verification_type, old_status, new_status, score, evidence_details, current_iso_time()
            ))
            conn.commit()

    def record_batch_progress(self, progress: BatchProgressModel) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO batch_progress (
                job_id, batch_number, batch_start_index, batch_end_index,
                companies_processed, confirmed_added, duplicates_skipped, failed_count,
                checkpoint_excel_path, processed_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                progress.job_id, progress.batch_number, progress.batch_start_index, progress.batch_end_index,
                progress.companies_processed, progress.confirmed_added, progress.duplicates_skipped,
                progress.failed_count, progress.checkpoint_excel_path, progress.processed_at, progress.notes
            ))
            conn.commit()

    def record_failed(self, failed: FailedRecordModel) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO failed_records (
                company_name, attempted_url, failure_stage, error_reason, source_url, attempted_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                failed.company_name, failed.attempted_url, failed.failure_stage,
                failed.error_reason, failed.source_url, failed.attempted_at
            ))
            conn.commit()

    def get_company_by_domain_or_name(self, domain: str, normalized_name: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if domain:
                cursor.execute("SELECT * FROM companies WHERE normalized_domain = ? LIMIT 1", (domain,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
            if normalized_name:
                cursor.execute("SELECT * FROM companies WHERE normalized_name = ? LIMIT 1", (normalized_name,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
            return None

    def get_all_companies(self, confirmed_only: bool = False) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if confirmed_only:
                cursor.execute("SELECT * FROM companies WHERE review_status = 'Confirmed' ORDER BY id ASC")
            else:
                cursor.execute("SELECT * FROM companies ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_executives_for_company(self, company_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM executives WHERE company_id = ? ORDER BY is_ceo_or_founder DESC, id ASC", (company_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_contacts_for_company(self, company_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM business_contacts WHERE company_id = ? ORDER BY id ASC", (company_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_system_stats(self) -> Dict[str, Any]:
        """Aggregate high-level metrics for dashboard and reports."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            stats = {}

            cursor.execute("SELECT COUNT(*) FROM companies")
            stats["total_discovered"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM companies WHERE review_status = 'Confirmed'")
            stats["confirmed_companies"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM companies WHERE authenticity_category = 'A'")
            stats["officially_corroborated"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM companies WHERE authenticity_category = 'B'")
            stats["officially_documented"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM companies WHERE review_status = 'Requires Review'")
            stats["requires_review_companies"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM executives")
            stats["total_executives"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM executives WHERE is_ceo_or_founder = 1")
            stats["total_ceos"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM business_contacts WHERE email IS NOT NULL AND email != ''")
            stats["published_emails"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM business_contacts WHERE email_type = 'Direct executive email'")
            stats["direct_emails"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM business_contacts WHERE phone IS NOT NULL AND phone != ''")
            stats["published_phones"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM failed_records")
            stats["failed_records"] = cursor.fetchone()[0]

            cursor.execute("SELECT MAX(batch_number) FROM batch_progress")
            max_batch = cursor.fetchone()[0]
            stats["current_batch"] = max_batch if max_batch else 0

            return stats
