"""
Executive Verification Engine for Pakistan Business Intelligence System.
Validates executive names, roles, leadership designations, and public professional links.
"""

from typing import Dict, Any, Tuple
from ..storage.models import ExecutiveModel, current_iso_time
from .quality_scoring import QualityScorer


class ExecutiveVerifier:
    """Verifies executive identity and corporate authority."""

    @staticmethod
    def verify_executive(
        raw_executive: Dict[str, Any],
        executive_id: str,
        company_id: str
    ) -> ExecutiveModel:
        """
        Validates executive name and role, and scores identity confidence.
        """
        name = raw_executive.get("name", "").strip()
        designation = raw_executive.get("designation", "").strip()
        role = raw_executive.get("normalized_role", "Other").strip()
        linkedin_url = raw_executive.get("linkedin_url")
        source_url = raw_executive.get("source_url", "")
        evidence = raw_executive.get("evidence_text", "")

        is_ceo_or_founder = int(
            role in ("CEO", "Founder", "Co-Founder", "Managing Director") or
            "ceo" in designation.lower() or
            "chief executive" in designation.lower() or
            "founder" in designation.lower() or
            "managing director" in designation.lower()
        )

        score, status, reason = QualityScorer.score_executive_identity(
            name_present=bool(name),
            designation_present=bool(designation),
            is_c_level_or_founder=bool(is_ceo_or_founder),
            from_official_leadership_page=bool(source_url),
            from_annual_report_or_filing=bool("filing" in source_url or "report" in source_url or "psx" in source_url),
            linkedin_corroborated=bool(linkedin_url)
        )

        return ExecutiveModel(
            executive_id=executive_id,
            company_id=company_id,
            name=name,
            designation=designation,
            normalized_role=role,
            is_ceo_or_founder=is_ceo_or_founder,
            linkedin_url=linkedin_url,
            verification_status=status,
            verification_score=score,
            source_url=source_url,
            evidence_text=evidence or reason,
            first_discovered_at=current_iso_time(),
            last_verified_at=current_iso_time(),
            is_current=1
        )
