"""
Free Local Email Verification Engine.
Performs syntax validation, domain validation, and live DNS MX record lookups via dnspython.
Distinguishes direct executive mailboxes from general business mailboxes.
"""

import dns.resolver
from email_validator import validate_email, EmailNotValidError
from typing import Dict, Any, Tuple, Optional
import logging
from .quality_scoring import QualityScorer

logger = logging.getLogger("EmailVerification")


class EmailVerifier:
    """Verifies email addresses without sending emails or using paid services."""

    GENERAL_PREFIXES = {
        "info", "contact", "support", "sales", "hello", "help", "admin",
        "inquiries", "inquiry", "hr", "careers", "jobs", "press", "media",
        "billing", "accounts", "legal", "general", "office", "marketing"
    }

    def __init__(self, timeout: int = 5):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = timeout
        self.mx_cache: Dict[str, Optional[str]] = {}

    def check_dns_mx(self, domain: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if domain has valid DNS MX records. Caches results to prevent repeated queries.
        """
        if not domain:
            return False, None
        domain = domain.lower().strip()
        if domain in self.mx_cache:
            host = self.mx_cache[domain]
            return host is not None, host

        try:
            answers = self.resolver.resolve(domain, "MX")
            if answers:
                primary_mx = str(answers[0].exchange).rstrip(".")
                self.mx_cache[domain] = primary_mx
                return True, primary_mx
        except Exception:
            # Fallback check for A record if MX is absent (RFC 5321 allows A fallback)
            try:
                a_answers = self.resolver.resolve(domain, "A")
                if a_answers:
                    primary_ip = str(a_answers[0])
                    self.mx_cache[domain] = primary_ip
                    return True, primary_ip
            except Exception:
                pass

        self.mx_cache[domain] = None
        return False, None

    def verify_email(
        self,
        raw_email: str,
        company_domain: str = "",
        from_official_page: bool = True
    ) -> Dict[str, Any]:
        """
        Executes syntax, domain, and DNS MX record verification.
        Returns detailed verification metadata and confidence score.
        """
        if not raw_email:
            return {
                "email": None,
                "is_valid": False,
                "email_type": "Unavailable",
                "verification_status": "Unavailable",
                "mx_host": None,
                "confidence_score": 0.0,
                "reason": "No email provided"
            }

        try:
            # 1. Syntax & deliverability check
            valid = validate_email(raw_email, check_deliverability=False)
            normalized_email = valid.normalized
            email_domain = valid.domain.lower()
            username = normalized_email.split("@")[0].lower()
            syntax_valid = True
        except EmailNotValidError as e:
            return {
                "email": raw_email,
                "is_valid": False,
                "email_type": "Unavailable",
                "verification_status": "Invalid Format",
                "mx_host": None,
                "confidence_score": 0.0,
                "reason": f"Syntax error: {str(e)}"
            }

        # 2. DNS MX Check
        has_mx, mx_host = self.check_dns_mx(email_domain)

        # 3. Check if company domain matches
        is_company_match = bool(company_domain and (company_domain in email_domain or email_domain in company_domain))

        # 4. Direct Executive vs General Email
        is_general = any(username == pfx or username.startswith(f"{pfx}.") or username.startswith(f"{pfx}-") for pfx in self.GENERAL_PREFIXES)
        is_direct = (not is_general) and ("." in username or "_" in username or len(username) >= 5)

        # 5. Score Quality
        score, email_type, status, reason = QualityScorer.score_email_confidence(
            syntax_valid=syntax_valid,
            domain_has_mx=has_mx,
            is_direct_executive_email=is_direct,
            is_company_domain_match=is_company_match,
            from_official_contact_page=from_official_page
        )

        return {
            "email": normalized_email,
            "is_valid": syntax_valid and has_mx,
            "email_type": email_type,
            "verification_status": status,
            "mx_host": mx_host,
            "confidence_score": score,
            "reason": reason
        }
