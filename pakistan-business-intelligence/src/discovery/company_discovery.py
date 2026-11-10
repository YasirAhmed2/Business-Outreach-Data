"""
Autonomous Company Discovery Engine.
Coordinates Tier 1, Tier 2, and Tier 3 discovery pipelines for authentic Pakistani businesses.
"""

import logging
from typing import List, Dict, Any, Generator
from .institutional_sources import InstitutionalDiscovery
from .directory_discovery import DirectoryDiscovery
from .source_registry import SourceRegistry

logger = logging.getLogger("CompanyDiscovery")


class CompanyDiscoveryEngine:
    """Discovers Pakistani companies, businesses, SMEs and startups independently."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get("processing", {}).get("request_timeout_seconds", 15)
        self.user_agent = config.get("processing", {}).get("user_agent", "")
        self.institutional = InstitutionalDiscovery(timeout=self.timeout, user_agent=self.user_agent)
        self.directory = DirectoryDiscovery(timeout=self.timeout)

    def discover_all_candidates(self, target_limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Discovers up to target_limit unique candidate businesses from permitted Pakistani sources.
        """
        candidates: List[Dict[str, Any]] = []
        seen_names = set()

        logger.info(f"Starting discovery pipeline. Target limit: {target_limit}")

        # 1. Tier 1: Pakistan Stock Exchange Listed Enterprises
        psx_companies = self.institutional.discover_psx_companies()
        for comp in psx_companies:
            name_clean = comp["company_name"].strip().lower()
            if name_clean not in seen_names:
                seen_names.add(name_clean)
                candidates.append(comp)
                if len(candidates) >= target_limit:
                    return candidates

        # 2. Tier 1: P@SHA and PSEB Technology & IT Companies
        it_companies = self.institutional.discover_pseb_pasha_companies()
        for comp in it_companies:
            name_clean = comp["company_name"].strip().lower()
            if name_clean not in seen_names:
                seen_names.add(name_clean)
                candidates.append(comp)
                if len(candidates) >= target_limit:
                    return candidates

        # 3. Tier 1: National Incubation Centers & Startups
        startups = self.institutional.discover_nic_ignite_startups()
        for comp in startups:
            name_clean = comp["company_name"].strip().lower()
            if name_clean not in seen_names:
                seen_names.add(name_clean)
                candidates.append(comp)
                if len(candidates) >= target_limit:
                    return candidates

        # 4. Tier 2: Rozee Corporate Business Ecosystem
        rozee_companies = self.directory.discover_rozee_ecosystem_companies()
        for comp in rozee_companies:
            name_clean = comp["company_name"].strip().lower()
            if name_clean not in seen_names:
                seen_names.add(name_clean)
                candidates.append(comp)
                if len(candidates) >= target_limit:
                    return candidates

        # 5. Tier 2: Pakistan Chambers of Commerce (KCCI, LCCI, ICCI, SCCI, GCCI)
        chamber_enterprises = self.directory.discover_chamber_of_commerce_enterprises()
        for comp in chamber_enterprises:
            name_clean = comp["company_name"].strip().lower()
            if name_clean not in seen_names:
                seen_names.add(name_clean)
                candidates.append(comp)
                if len(candidates) >= target_limit:
                    return candidates

        logger.info(f"Discovery pipeline finished. Found {len(candidates)} unique authentic businesses.")
        return candidates
