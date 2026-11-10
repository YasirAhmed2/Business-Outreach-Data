"""
Contact Extraction Engine for Pakistan Business Intelligence System.
Extracts published email addresses and Pakistani telephone numbers from web pages.
"""

import re
from typing import List, Dict, Any, Set
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("ContactExtractor")


class ContactExtractor:
    """Extracts published contact information with Pakistani context."""

    EMAIL_REGEX = re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    )

    # Pakistani telephone patterns: Landlines (021, 042, 051, 041, 052, 055, 091), Mobiles (+92 3xx, 03xx), UAN (111)
    PHONE_REGEX = re.compile(
        r"(?:(?:\+92|0092|0)\s*[\(-]?(?:[2-9]\d{1,2}|3\d{2})[\)-]?\s*[\d\s-]{6,10})|(?:\b111[-.\s]?\d{3}[-.\s]?\d{3}\b)"
    )

    IGNORE_EMAIL_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js"
    }

    IGNORE_EMAIL_PREFIXES = {
        "example", "sample", "test", "yourname", "username", "domain", "email"
    }

    @classmethod
    def extract_emails(cls, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """Extracts email addresses from page body, footers, and mailto links."""
        found_emails: List[Dict[str, Any]] = []
        if not soup:
            return found_emails

        seen: Set[str] = set()

        # 1. Check mailto links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().startswith("mailto:"):
                raw_email = href[7:].split("?")[0].strip().lower()
                if cls._is_valid_candidate_email(raw_email) and raw_email not in seen:
                    seen.add(raw_email)
                    found_emails.append({
                        "email": raw_email,
                        "source_url": page_url,
                        "context": a_tag.get_text(strip=True) or "mailto link"
                    })

        # 2. Check full page text
        page_text = soup.get_text(separator=" ", strip=True)
        for match in cls.EMAIL_REGEX.finditer(page_text):
            raw_email = match.group(0).strip().lower().rstrip(".,;:")
            if cls._is_valid_candidate_email(raw_email) and raw_email not in seen:
                seen.add(raw_email)
                # Grab surrounding 50 characters as evidence
                start = max(0, match.start() - 25)
                end = min(len(page_text), match.end() + 25)
                snippet = page_text[start:end].strip()
                found_emails.append({
                    "email": raw_email,
                    "source_url": page_url,
                    "context": snippet
                })

        return found_emails

    @classmethod
    def extract_phones(cls, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """Extracts Pakistani telephone numbers and UANs."""
        found_phones: List[Dict[str, Any]] = []
        if not soup:
            return found_phones

        seen: Set[str] = set()

        # 1. Check tel links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().startswith("tel:"):
                raw_phone = href[4:].split("?")[0].strip()
                clean_digits = re.sub(r"[^\d+]", "", raw_phone)
                if len(clean_digits) >= 8 and raw_phone not in seen:
                    seen.add(raw_phone)
                    found_phones.append({
                        "phone": raw_phone,
                        "source_url": page_url,
                        "context": a_tag.get_text(strip=True) or "tel link"
                    })

        # 2. Check full text
        page_text = soup.get_text(separator=" ", strip=True)
        for match in cls.PHONE_REGEX.finditer(page_text):
            raw_phone = match.group(0).strip()
            # Clean up trailing punctuation
            raw_phone = raw_phone.rstrip(".,;:-")
            digits_only = re.sub(r"\D", "", raw_phone)
            # Must look like a real Pakistani phone (at least 9 digits, e.g. 021-34567890 or 0300-1234567 or UAN 111-xxx-xxx)
            if (len(digits_only) >= 9 or (digits_only.startswith("111") and len(digits_only) == 9)) and raw_phone not in seen:
                seen.add(raw_phone)
                start = max(0, match.start() - 25)
                end = min(len(page_text), match.end() + 25)
                snippet = page_text[start:end].strip()
                found_phones.append({
                    "phone": raw_phone,
                    "source_url": page_url,
                    "context": snippet
                })

        return found_phones

    @classmethod
    def _is_valid_candidate_email(cls, email: str) -> bool:
        if not email or "@" not in email:
            return False
        for ext in cls.IGNORE_EMAIL_EXTENSIONS:
            if email.endswith(ext):
                return False
        prefix = email.split("@")[0].lower()
        if prefix in cls.IGNORE_EMAIL_PREFIXES:
            return False
        return True
