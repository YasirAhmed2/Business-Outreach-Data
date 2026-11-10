"""
Company Verification Engine for Pakistan Business Intelligence System.
Performs evidence-based verification of company existence, active domain reachability,
geographic presence in Pakistan, and statutory/institutional compliance.
"""

import requests
import logging
from typing import Dict, Any, Tuple, Optional
from urllib.robotparser import RobotFileParser
from ..storage.models import CompanyModel, current_iso_time
from ..processing.deduplication import DeduplicationEngine
from .quality_scoring import QualityScorer

logger = logging.getLogger("CompanyVerification")


class CompanyVerifier:
    """Verifies discovered companies against authenticity criteria."""

    PAKISTANI_CITIES_MAP = {
        "karachi": ("Karachi", "Sindh"),
        "lahore": ("Lahore", "Punjab"),
        "islamabad": ("Islamabad", "Islamabad Capital Territory"),
        "rawalpindi": ("Rawalpindi", "Punjab"),
        "faisalabad": ("Faisalabad", "Punjab"),
        "peshawar": ("Peshawar", "Khyber Pakhtunkhwa"),
        "haripur": ("Haripur", "Khyber Pakhtunkhwa"),
        "abbottabad": ("Abbottabad", "Khyber Pakhtunkhwa"),
        "sialkot": ("Sialkot", "Punjab"),
        "gujranwala": ("Gujranwala", "Punjab"),
        "multan": ("Multan", "Punjab"),
        "hyderabad": ("Hyderabad", "Sindh"),
        "quetta": ("Quetta", "Balochistan"),
        "sargodha": ("Sargodha", "Punjab"),
        "bahawalpur": ("Bahawalpur", "Punjab"),
        "sukkur": ("Sukkur", "Sindh"),
        "gujrat": ("Gujrat", "Punjab"),
        "sheikhupura": ("Sheikhupura", "Punjab"),
        "jhelum": ("Jhelum", "Punjab"),
        "hub": ("Hub", "Balochistan"),
        "nowshera": ("Nowshera", "Khyber Pakhtunkhwa"),
    }

    def __init__(self, timeout: int = 12, user_agent: str = ""):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (Pakistan-Business-Research/1.0)"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def check_website_reachability(self, website_url: str) -> Tuple[bool, str]:
        """
        Tests if the company's official domain is live and reachable.
        Returns: (is_reachable, final_url)
        """
        if not website_url:
            return False, ""
        
        target = website_url.strip()
        if not target.startswith("http://") and not target.startswith("https://"):
            target = "https://" + target

        try:
            resp = self.session.head(target, timeout=self.timeout, allow_redirects=True)
            if resp.status_code < 400:
                return True, resp.url
            # Retry with GET in case HEAD is blocked
            resp = self.session.get(target, timeout=self.timeout, stream=True)
            return resp.status_code < 400, resp.url
        except Exception:
            # Fallback to http if https failed
            if target.startswith("https://"):
                try:
                    fallback = "http://" + target[8:]
                    resp = self.session.get(fallback, timeout=self.timeout, stream=True)
                    return resp.status_code < 400, resp.url
                except Exception:
                    pass
            return False, target

    def normalize_geographic_location(self, city_hint: str) -> Tuple[str, str]:
        """Maps Pakistani city name to standardized (City, Province)."""
        if not city_hint:
            return "Karachi", "Sindh"  # Default commercial hub
        clean = city_hint.strip().lower()
        for key, (city, prov) in self.PAKISTANI_CITIES_MAP.items():
            if key in clean:
                return city, prov
        return city_hint.title(), "Pakistan"

    def verify_company(self, raw_candidate: Dict[str, Any], company_id: str) -> CompanyModel:
        """
        Evaluates raw candidate data, executes reachability and geographical checks,
        and scores authenticity.
        """
        name = raw_candidate.get("company_name", "").strip()
        norm_name = DeduplicationEngine.normalize_company_name(name)
        website = raw_candidate.get("official_website", "").strip()
        domain = DeduplicationEngine.normalize_domain(website)

        city_hint = raw_candidate.get("city", "")
        city, province = self.normalize_geographic_location(city_hint)

        is_secp_psx = bool(raw_candidate.get("is_secp_or_psx_registered") or raw_candidate.get("stock_symbol"))
        is_pasha_pseb = bool(raw_candidate.get("is_pasha_or_pseb_member"))
        is_incubated = bool(raw_candidate.get("is_nic_or_university_incubated"))
        has_official_source = bool(raw_candidate.get("discovery_source"))

        website_reachable, final_url = self.check_website_reachability(website)
        if final_url:
            website = final_url
            domain = DeduplicationEngine.normalize_domain(final_url)

        has_pk_tld_or_address = domain.endswith(".pk") or "pakistan" in city.lower() or "sindh" in province.lower() or "punjab" in province.lower()

        score, category, status, reason = QualityScorer.score_company_authenticity(
            has_official_source=has_official_source,
            has_independent_corroboration=is_secp_psx or (website_reachable and is_pasha_pseb),
            is_secp_or_psx_registered=is_secp_psx,
            is_pasha_or_pseb_member=is_pasha_pseb,
            is_nic_or_university_incubated=is_incubated,
            website_reachable=website_reachable,
            has_pakistan_city=bool(city),
            has_pakistan_tld_or_address=has_pk_tld_or_address
        )

        review_status = "Confirmed" if category in ("A", "B") else "Requires Review"

        return CompanyModel(
            company_id=company_id,
            company_name=name,
            normalized_name=norm_name,
            company_type=raw_candidate.get("company_type", "Private Limited"),
            industry=raw_candidate.get("industry", "Business & Technology"),
            city=city,
            province=province,
            country="Pakistan",
            official_website=website,
            normalized_domain=domain,
            authenticity_status=status,
            authenticity_category=category,
            authenticity_score=score,
            secp_registered=1 if is_secp_psx else 0,
            secp_registration_no=raw_candidate.get("secp_registration_no"),
            stock_symbol=raw_candidate.get("stock_symbol"),
            source_url=raw_candidate.get("source_url", ""),
            discovery_source=raw_candidate.get("discovery_source", "Public Business Registry"),
            first_discovered_at=current_iso_time(),
            last_verified_at=current_iso_time(),
            review_status=review_status,
            notes=reason
        )
