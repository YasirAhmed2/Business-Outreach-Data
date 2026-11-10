"""
Source Registry for Pakistan Business Intelligence System.
Maintains institutional, regulatory, and public business directories.
"""

from typing import Dict, List, Any
from ..storage.models import SourceModel, current_iso_time


class SourceRegistry:
    """Registry of permitted and authoritative business discovery sources in Pakistan."""

    SOURCES: List[Dict[str, Any]] = [
        # Tier 1: Official Statutory, Regulatory & Institutional Sources
        {
            "source_id": "SRC-PSX-LISTED",
            "source_name": "Pakistan Stock Exchange (PSX) Listed Companies",
            "source_type": "official_regulatory",
            "tier": 1,
            "base_url": "https://www.psx.com.pk",
            "description": "Official statutory registry of companies listed on Pakistan Stock Exchange spanning 35+ sectors including Technology, Pharmaceuticals, Banking, Textiles, Engineering, and Cement.",
            "is_official": 1
        },
        {
            "source_id": "SRC-SECP-PUBLIC",
            "source_name": "Securities and Exchange Commission of Pakistan (SECP)",
            "source_type": "official_regulatory",
            "tier": 1,
            "base_url": "https://www.secp.gov.pk",
            "description": "Official company registrar of Pakistan. Public statutory records of incorporated entities, certified NBFCs, and public companies.",
            "is_official": 1
        },
        {
            "source_id": "SRC-PSEB-DIR",
            "source_name": "Pakistan Software Export Board (PSEB)",
            "source_type": "official_institutional",
            "tier": 1,
            "base_url": "https://pseb.org.pk",
            "description": "Government body under Ministry of IT & Telecom promoting and registering IT/ITeS companies, call centers, and software exporters in Pakistan.",
            "is_official": 1
        },
        {
            "source_id": "SRC-PASHA-MEM",
            "source_name": "Pakistan Software Houses Association (P@SHA)",
            "source_type": "industry_association",
            "tier": 1,
            "base_url": "https://pasha.org.pk",
            "description": "Apex trade body representing Pakistan's IT and IT-enabled services industry with verified corporate members across major cities.",
            "is_official": 1
        },
        {
            "source_id": "SRC-IGNITE-NIC",
            "source_name": "Ignite National Technology Fund & National Incubation Centers",
            "source_type": "official_incubator",
            "tier": 1,
            "base_url": "https://ignite.org.pk",
            "description": "Ministry of IT funded incubator network (NIC Karachi, NIC Lahore LUMS, NIC Islamabad, NIC Peshawar, NIC Quetta, NIC Faisalabad, NICAT).",
            "is_official": 1
        },
        {
            "source_id": "SRC-UNIV-INCUB",
            "source_name": "University Business Incubation Centers (HEC/BICs)",
            "source_type": "academic_incubator",
            "tier": 1,
            "base_url": "https://hec.gov.pk",
            "description": "Official Higher Education Commission recognized university incubation centers (LUMS, NUST, IBA, FAST-NUCES, UET, GIKI).",
            "is_official": 1
        },

        # Tier 2: Official Business Ecosystem Sources & Chambers
        {
            "source_id": "SRC-ROZEE-DIR",
            "source_name": "Rozee.pk Verified Business & Employer Directory",
            "source_type": "business_ecosystem",
            "tier": 2,
            "base_url": "https://www.rozee.pk",
            "description": "Pakistan's largest employment and corporate employer directory containing thousands of authentic registered Pakistani businesses and SMEs.",
            "is_official": 1
        },
        {
            "source_id": "SRC-CHAMBERS-PK",
            "source_name": "Pakistan Chambers of Commerce & Industry (FPCCI, KCCI, LCCI, ICCI)",
            "source_type": "chamber_directory",
            "tier": 2,
            "base_url": "https://fpcci.org.pk",
            "description": "Federation of Pakistan Chambers of Commerce & Industry and regional chambers (Karachi, Lahore, Islamabad, Sialkot, Faisalabad).",
            "is_official": 1
        },
        {
            "source_id": "SRC-STARTUP-PORTFOLIOS",
            "source_name": "Pakistani Venture & Startup Ecosystem Portfolios",
            "source_type": "venture_portfolio",
            "tier": 2,
            "base_url": "https://invest2innovate.com",
            "description": "Publicly announced funded startups and institutional venture portfolios (i2i, Fatima Gobi, SOSV, Zayn Capital).",
            "is_official": 1
        },
        {
            "source_id": "SRC-ENTERPRISE-WEB",
            "source_name": "Official Corporate Websites & Annual Reports",
            "source_type": "company_direct",
            "tier": 2,
            "base_url": "https://official-websites.pk",
            "description": "Direct official corporate portals, leadership directories, and published financial disclosures.",
            "is_official": 1
        }
    ]

    @classmethod
    def get_all_sources(cls) -> List[SourceModel]:
        return [
            SourceModel(
                source_id=s["source_id"],
                source_name=s["source_name"],
                source_type=s["source_type"],
                tier=s["tier"],
                base_url=s["base_url"],
                description=s["description"],
                is_official=s["is_official"],
                last_accessed_at=current_iso_time()
            )
            for s in cls.SOURCES
        ]

    @classmethod
    def get_source_by_id(cls, source_id: str) -> Dict[str, Any]:
        for s in cls.SOURCES:
            if s["source_id"] == source_id:
                return s
        return {}
