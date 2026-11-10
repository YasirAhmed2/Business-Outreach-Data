"""
Unit tests for data models and structures.
"""

import pytest
from src.storage.models import (
    CompanyModel,
    ExecutiveModel,
    BusinessContactModel,
    SourceModel,
    current_iso_time
)


def test_company_model():
    company = CompanyModel(
        company_id="PK-COMP-0001",
        company_name="Systems Limited",
        normalized_name="systems",
        company_type="Public Listed",
        industry="Technology",
        city="Lahore",
        province="Punjab",
        country="Pakistan",
        official_website="https://www.systemsltd.com",
        normalized_domain="systemsltd.com",
        authenticity_status="Officially corroborated",
        authenticity_category="A",
        authenticity_score=95.0,
        secp_registered=1,
        stock_symbol="SYS"
    )
    d = company.to_dict()
    assert d["company_id"] == "PK-COMP-0001"
    assert d["company_name"] == "Systems Limited"
    assert d["stock_symbol"] == "SYS"
    assert d["country"] == "Pakistan"


def test_executive_model():
    exec_mod = ExecutiveModel(
        executive_id="PK-EXEC-0001",
        company_id="PK-COMP-0001",
        name="Asif Peer",
        designation="Chief Executive Officer",
        normalized_role="CEO",
        is_ceo_or_founder=1,
        linkedin_url="https://www.linkedin.com/in/asifpeer",
        verification_status="Confirmed",
        verification_score=90.0
    )
    d = exec_mod.to_dict()
    assert d["name"] == "Asif Peer"
    assert d["is_ceo_or_founder"] == 1
    assert d["verification_status"] == "Confirmed"


def test_business_contact_model():
    contact = BusinessContactModel(
        contact_id="PK-CONT-0001",
        company_id="PK-COMP-0001",
        email="info@systemsltd.com",
        email_type="General company email",
        email_verification_status="MX Confirmed",
        phone="+92 42 111-797-836",
        phone_verification_status="Valid PK Phone",
        confidence_score=85.0
    )
    d = contact.to_dict()
    assert d["email"] == "info@systemsltd.com"
    assert d["phone_verification_status"] == "Valid PK Phone"
