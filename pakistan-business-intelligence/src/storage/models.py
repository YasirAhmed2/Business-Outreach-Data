"""
Data models and structure definitions for Pakistan Business Intelligence System.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


def current_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CompanyModel:
    company_id: str
    company_name: str
    normalized_name: str
    company_type: str = "Private Limited"
    industry: str = "Technology"
    city: str = "Karachi"
    province: str = "Sindh"
    country: str = "Pakistan"
    official_website: str = ""
    normalized_domain: str = ""
    authenticity_status: str = "Requires review"  # Officially corroborated | Officially documented | Requires review
    authenticity_category: str = "C"  # A, B, C
    authenticity_score: float = 0.0
    secp_registered: int = 0
    secp_registration_no: Optional[str] = None
    stock_symbol: Optional[str] = None
    source_url: str = ""
    discovery_source: str = ""
    first_discovered_at: str = field(default_factory=current_iso_time)
    last_verified_at: str = field(default_factory=current_iso_time)
    review_status: str = "Requires Review"  # Confirmed | Requires Review | Rejected | Duplicate
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutiveModel:
    executive_id: str
    company_id: str
    name: str
    designation: str
    normalized_role: str = "Other"  # CEO | Founder | Managing Director | CTO | COO | CIO | Other
    is_ceo_or_founder: int = 0
    linkedin_url: Optional[str] = None
    verification_status: str = "Unavailable"  # Confirmed | Documented | Requires Review | Unavailable
    verification_score: float = 0.0
    source_url: str = ""
    evidence_text: str = ""
    first_discovered_at: str = field(default_factory=current_iso_time)
    last_verified_at: str = field(default_factory=current_iso_time)
    is_current: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessContactModel:
    contact_id: str
    company_id: str
    executive_id: Optional[str] = None
    email: Optional[str] = None
    email_type: str = "Unavailable"  # Direct executive email | General company email | Unverified email | Unavailable
    email_verification_status: str = "Unavailable"  # MX Confirmed | Syntax Validated | Failed MX | Unverified | Unavailable
    email_mx_host: Optional[str] = None
    phone: Optional[str] = None
    normalized_phone: Optional[str] = None
    phone_type: str = "Unavailable"  # Company Landline | Business Mobile | UAN | Toll Free | Unavailable
    phone_verification_status: str = "Unavailable"  # Valid PK Phone | Invalid Format | Unverified | Unavailable
    contact_source_url: str = ""
    evidence_snippet: str = ""
    confidence_score: float = 0.0
    first_discovered_at: str = field(default_factory=current_iso_time)
    last_verified_at: str = field(default_factory=current_iso_time)
    is_active: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SourceModel:
    source_id: str
    source_name: str
    source_type: str
    tier: int
    base_url: str
    description: str
    is_official: int = 1
    records_count: int = 0
    last_accessed_at: str = field(default_factory=current_iso_time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationHistoryModel:
    entity_type: str  # company | executive | email | phone
    entity_id: str
    verification_type: str
    old_status: str
    new_status: str
    score: float
    evidence_details: str
    verified_at: str = field(default_factory=current_iso_time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BatchProgressModel:
    job_id: str
    batch_number: int
    batch_start_index: int
    batch_end_index: int
    companies_processed: int
    confirmed_added: int
    duplicates_skipped: int
    failed_count: int
    checkpoint_excel_path: str = ""
    processed_at: str = field(default_factory=current_iso_time)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FailedRecordModel:
    company_name: str
    attempted_url: str
    failure_stage: str
    error_reason: str
    source_url: str
    attempted_at: str = field(default_factory=current_iso_time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
