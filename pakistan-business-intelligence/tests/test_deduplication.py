"""
Unit tests for deduplication and entity normalization.
"""

from src.processing.deduplication import DeduplicationEngine


def test_normalize_company_name():
    assert DeduplicationEngine.normalize_company_name("Systems Limited") == "systems"
    assert DeduplicationEngine.normalize_company_name("10Pearls Private Limited") == "10pearls"
    assert DeduplicationEngine.normalize_company_name("Engro Corp.") == "engro"
    assert DeduplicationEngine.normalize_company_name("Arbisoft (Pvt) Ltd.") == "arbisoft"


def test_normalize_domain():
    assert DeduplicationEngine.normalize_domain("https://www.systemsltd.com/about-us") == "systemsltd.com"
    assert DeduplicationEngine.normalize_domain("http://netsoltech.com") == "netsoltech.com"
    assert DeduplicationEngine.normalize_domain("www.sadapay.pk") == "sadapay.pk"


def test_is_same_company():
    assert DeduplicationEngine.is_same_company(
        "Systems Limited", "https://www.systemsltd.com",
        "Systems Ltd", "systemsltd.com"
    )
    assert not DeduplicationEngine.is_same_company(
        "Systems Limited", "https://www.systemsltd.com",
        "NetSol Technologies", "https://www.netsoltech.com"
    )
