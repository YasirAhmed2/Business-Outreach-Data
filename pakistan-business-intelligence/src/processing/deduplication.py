"""
Deduplication and Entity Resolution Engine for Pakistan Business Intelligence System.
"""

import re
from urllib.parse import urlparse
from typing import Optional, Tuple


class DeduplicationEngine:
    """Provides normalization and duplicate detection across companies and contacts."""

    LEGAL_SUFFIXES = [
        r"\bprivate\s+limited\b",
        r"\bpvt\s*\.?\s*ltd\b",
        r"\blimited\b",
        r"\bltd\b",
        r"\binc\b",
        r"\bcorp\b",
        r"\bcorporation\b",
        r"\bllc\b",
        r"\bcompany\b",
        r"\bco\b",
    ]

    @classmethod
    def normalize_company_name(cls, name: str) -> str:
        """
        Normalizes company names by lowercasing, removing legal designations, and stripping punctuation.
        Example: 'Systems Limited' -> 'systems'
        """
        if not name:
            return ""
        norm = name.strip().lower()
        # Remove parenthetical details
        norm = re.sub(r"\(.*?\)", "", norm)
        # Remove common corporate suffixes
        for suffix in cls.LEGAL_SUFFIXES:
            norm = re.sub(suffix, "", norm, flags=re.IGNORECASE)
        # Remove special characters
        norm = re.sub(r"[^\w\s]", "", norm)
        # Collapse whitespace
        norm = " ".join(norm.split())
        return norm

    @classmethod
    def normalize_domain(cls, url_or_domain: str) -> str:
        """
        Extracts and normalizes domain from URL or string.
        Example: 'https://www.systemsltd.com/about' -> 'systemsltd.com'
        """
        if not url_or_domain:
            return ""
        raw = url_or_domain.strip().lower()
        if not raw.startswith("http://") and not raw.startswith("https://"):
            raw = "https://" + raw
        try:
            parsed = urlparse(raw)
            domain = parsed.netloc or parsed.path
            domain = domain.split(":")[0]  # remove port
            if domain.startswith("www."):
                domain = domain[4:]
            return domain.strip()
        except Exception:
            return ""

    @classmethod
    def is_same_company(cls, name1: str, domain1: str, name2: str, domain2: str) -> bool:
        """Checks if two records represent the exact same company."""
        nd1 = cls.normalize_domain(domain1)
        nd2 = cls.normalize_domain(domain2)
        if nd1 and nd2 and nd1 == nd2:
            return True

        nn1 = cls.normalize_company_name(name1)
        nn2 = cls.normalize_company_name(name2)
        if nn1 and nn2 and nn1 == nn2:
            return True

        return False
