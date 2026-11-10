"""
Quality scoring engine for companies, executives, emails, phones, and sources.
All scores are explainable and derived strictly from objective verification evidence.
"""

from typing import Dict, Any, Tuple
from datetime import datetime, timezone


class QualityScorer:
    """Computes transparent, evidence-based quality scores from 0.0 to 100.0."""

    @staticmethod
    def score_company_authenticity(
        has_official_source: bool,
        has_independent_corroboration: bool,
        is_secp_or_psx_registered: bool,
        is_pasha_or_pseb_member: bool,
        is_nic_or_university_incubated: bool,
        website_reachable: bool,
        has_pakistan_city: bool,
        has_pakistan_tld_or_address: bool
    ) -> Tuple[float, str, str, str]:
        """
        Returns:
            (score, authenticity_category, authenticity_status, reason)
        """
        score = 0.0
        reasons = []

        if is_secp_or_psx_registered:
            score += 40.0
            reasons.append("Authoritative statutory/regulatory listing (SECP/PSX)")
        elif is_pasha_or_pseb_member or is_nic_or_university_incubated:
            score += 35.0
            reasons.append("Recognized national institutional directory (P@SHA/PSEB/NIC/HEC)")
        elif has_official_source:
            score += 25.0
            reasons.append("Documented business directory source")

        if website_reachable:
            score += 25.0
            reasons.append("Active and reachable official domain")

        if has_independent_corroboration:
            score += 20.0
            reasons.append("Cross-verified with independent external source")

        if has_pakistan_city:
            score += 10.0
            reasons.append("Verified physical presence in Pakistani city")

        if has_pakistan_tld_or_address:
            score += 5.0
            reasons.append(".pk domain or Pakistani address documented")

        # Category Determination
        if has_independent_corroboration and (is_secp_or_psx_registered or is_pasha_or_pseb_member or (website_reachable and score >= 70)):
            category = "A"
            status = "Officially corroborated"
        elif (has_official_source or website_reachable) and score >= 50:
            category = "B"
            status = "Officially documented"
        else:
            category = "C"
            status = "Requires review"

        return min(100.0, score), category, status, "; ".join(reasons)

    @staticmethod
    def score_executive_identity(
        name_present: bool,
        designation_present: bool,
        is_c_level_or_founder: bool,
        from_official_leadership_page: bool,
        from_annual_report_or_filing: bool,
        linkedin_corroborated: bool
    ) -> Tuple[float, str, str]:
        """
        Returns:
            (score, verification_status, reason)
        """
        if not name_present or not designation_present:
            return 0.0, "Unavailable", "No executive name or designation found"

        score = 20.0
        reasons = ["Name and designation present"]

        if is_c_level_or_founder:
            score += 15.0
            reasons.append("Standard executive decision-maker role")

        if from_annual_report_or_filing:
            score += 40.0
            reasons.append("Published in official regulatory filing/annual report")
        elif from_official_leadership_page:
            score += 35.0
            reasons.append("Published on official company leadership/team page")

        if linkedin_corroborated:
            score += 15.0
            reasons.append("Official company link to professional profile")

        if score >= 75:
            status = "Confirmed"
        elif score >= 50:
            status = "Documented"
        else:
            status = "Requires Review"

        return min(100.0, score), status, "; ".join(reasons)

    @staticmethod
    def score_email_confidence(
        syntax_valid: bool,
        domain_has_mx: bool,
        is_direct_executive_email: bool,
        is_company_domain_match: bool,
        from_official_contact_page: bool
    ) -> Tuple[float, str, str, str]:
        """
        Returns:
            (score, email_type, email_verification_status, reason)
        """
        if not syntax_valid:
            return 0.0, "Unavailable", "Invalid Format", "Failed email syntax validation"

        score = 25.0
        reasons = ["Passed syntax validation"]

        if domain_has_mx:
            score += 35.0
            reasons.append("Domain has live DNS MX records")
            mx_status = "MX Confirmed"
        else:
            mx_status = "Failed MX"
            reasons.append("DNS MX lookup failed")

        if is_company_domain_match:
            score += 20.0
            reasons.append("Matches company official domain")

        if from_official_contact_page:
            score += 10.0
            reasons.append("Extracted directly from official website/contact page")

        if is_direct_executive_email:
            score += 10.0
            email_type = "Direct executive email"
            reasons.append("Executive personal/direct corporate mailbox")
        else:
            email_type = "General company email"
            reasons.append("General business contact mailbox (info/contact/support)")

        return min(100.0, score), email_type, mx_status, "; ".join(reasons)

    @staticmethod
    def score_phone_confidence(
        is_valid_pk_phone: bool,
        is_landline: bool,
        is_mobile_or_uan: bool,
        from_official_contact_page: bool
    ) -> Tuple[float, str, str, str]:
        """
        Returns:
            (score, phone_type, phone_verification_status, reason)
        """
        if not is_valid_pk_phone:
            return 0.0, "Unavailable", "Invalid Format", "Failed Pakistan phone validation (+92)"

        score = 40.0
        reasons = ["Valid Pakistan phone number (+92 format)"]

        if is_landline:
            phone_type = "Company Landline"
            score += 30.0
            reasons.append("Verified city landline area code")
        elif is_mobile_or_uan:
            phone_type = "Business Mobile / UAN"
            score += 25.0
            reasons.append("Verified mobile prefix or UAN")
        else:
            phone_type = "Business Phone"
            score += 15.0

        if from_official_contact_page:
            score += 20.0
            reasons.append("Directly published on official contact page")

        return min(100.0, score), phone_type, "Valid PK Phone", "; ".join(reasons)
