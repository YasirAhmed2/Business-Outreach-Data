"""
Unit tests for company, email, phone, and quality scoring verification.
"""

from src.verification.quality_scoring import QualityScorer
from src.verification.email_verification import EmailVerifier
from src.verification.phone_verification import PhoneVerifier


def test_company_quality_scorer():
    score, cat, status, reason = QualityScorer.score_company_authenticity(
        has_official_source=True,
        has_independent_corroboration=True,
        is_secp_or_psx_registered=True,
        is_pasha_or_pseb_member=False,
        is_nic_or_university_incubated=False,
        website_reachable=True,
        has_pakistan_city=True,
        has_pakistan_tld_or_address=True
    )
    assert score >= 80.0
    assert cat == "A"
    assert status == "Officially corroborated"


def test_email_verifier_syntax_and_classification():
    verifier = EmailVerifier()
    
    # Test valid syntax and general prefix
    res_gen = verifier.verify_email("info@systemsltd.com", company_domain="systemsltd.com")
    assert res_gen["is_valid"] is True
    assert res_gen["email_type"] == "General company email"

    # Test direct mailbox syntax
    res_dir = verifier.verify_email("asif.peer@systemsltd.com", company_domain="systemsltd.com")
    assert res_dir["email_type"] == "Direct executive email"

    # Test invalid email format
    res_inv = verifier.verify_email("invalid-email-address")
    assert res_inv["is_valid"] is False
    assert res_inv["verification_status"] == "Invalid Format"


def test_phone_verifier_pakistan():
    verifier = PhoneVerifier()

    # Valid Lahore landline format: 042-35870000
    res_landline = verifier.verify_and_normalize_phone("042-35870000")
    assert res_landline["is_valid"] is True
    assert res_landline["verification_status"] == "Valid PK Phone"
    assert "+92 42" in res_landline["normalized_phone"]

    # Valid Pakistani mobile: 0300-1234567
    res_mobile = verifier.verify_and_normalize_phone("03001234567")
    assert res_mobile["is_valid"] is True
    assert "+92 300" in res_mobile["normalized_phone"]

    # Valid UAN format
    res_uan = verifier.verify_and_normalize_phone("111-797-836")
    assert res_uan["is_valid"] is True
    assert "UAN" in res_uan["normalized_phone"]

    # Invalid non-Pakistani number
    res_invalid = verifier.verify_and_normalize_phone("12345")
    assert res_invalid["is_valid"] is False
