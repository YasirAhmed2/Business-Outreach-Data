"""
Comprehensive Company Research Coordinator.
Orchestrates company authenticity verification, executive research, and contact research.
"""

from typing import Dict, Any, Tuple, List, Optional
import logging
from ..storage.models import CompanyModel, ExecutiveModel, BusinessContactModel
from ..storage.database import DatabaseManager
from ..verification.company_verification import CompanyVerifier
from .executive_research import ExecutiveResearcher
from .contact_research import ContactResearcher

logger = logging.getLogger("CompanyResearch")


class CompanyResearcher:
    """Coordinates end-to-end research of a single company candidate."""

    def __init__(
        self,
        db: DatabaseManager,
        verifier: CompanyVerifier,
        exec_researcher: ExecutiveResearcher,
        contact_researcher: ContactResearcher
    ):
        self.db = db
        self.verifier = verifier
        self.exec_researcher = exec_researcher
        self.contact_researcher = contact_researcher

    def process_candidate(self, raw_candidate: Dict[str, Any]) -> Tuple[CompanyModel, List[ExecutiveModel], List[BusinessContactModel]]:
        """
        Runs authenticity verification, leadership discovery, and contact extraction.
        Persists results to database with full traceability.
        """
        # 1. Generate stable Company ID
        company_id = self.db.get_next_company_id()

        # 2. Verify Company Authenticity
        company = self.verifier.verify_company(raw_candidate, company_id)
        self.db.insert_or_update_company(company)

        executives: List[ExecutiveModel] = []
        contacts: List[BusinessContactModel] = []

        # 3. For confirmed or documented companies, research executives & contacts
        primary_exec_id = None
        if company.review_status == "Confirmed" or company.authenticity_category in ("A", "B"):
            executives = self.exec_researcher.research_executives_for_company(
                company_id=company.company_id,
                company_name=company.company_name,
                official_website=company.official_website,
                id_generator=self.db.get_next_executive_id
            )
            for ex in executives:
                self.db.insert_or_update_executive(ex)
                if ex.is_ceo_or_founder and not primary_exec_id:
                    primary_exec_id = ex.executive_id

            contacts = self.contact_researcher.research_contacts_for_company(
                company_id=company.company_id,
                company_name=company.company_name,
                official_website=company.official_website,
                executive_id=primary_exec_id,
                id_generator=self.db.get_next_contact_id
            )
            for ct in contacts:
                self.db.insert_or_update_contact(ct)

        return company, executives, contacts
