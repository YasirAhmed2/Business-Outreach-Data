"""
Unit tests for SQLite database manager.
"""

import os
import pytest
import tempfile
from src.storage.database import DatabaseManager
from src.storage.models import CompanyModel, ExecutiveModel, BusinessContactModel


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "test.db")
    db = DatabaseManager(db_file)
    yield db
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass


def test_database_initialization(temp_db):
    stats = temp_db.get_system_stats()
    assert stats["total_discovered"] == 0
    assert stats["confirmed_companies"] == 0


def test_insert_and_query_company(temp_db):
    c_id = temp_db.get_next_company_id()
    comp = CompanyModel(
        company_id=c_id,
        company_name="Lucky Cement Limited",
        normalized_name="lucky cement",
        company_type="Public Listed",
        industry="Cement",
        city="Karachi",
        province="Sindh",
        official_website="https://www.lucky-cement.com",
        normalized_domain="lucky-cement.com",
        authenticity_status="Officially corroborated",
        authenticity_category="A",
        authenticity_score=90.0,
        review_status="Confirmed"
    )
    temp_db.insert_or_update_company(comp)

    retrieved = temp_db.get_company_by_domain_or_name("lucky-cement.com", "lucky cement")
    assert retrieved is not None
    assert retrieved["company_name"] == "Lucky Cement Limited"

    stats = temp_db.get_system_stats()
    assert stats["total_discovered"] == 1
    assert stats["confirmed_companies"] == 1


def test_executive_and_contact_relations(temp_db):
    c_id = temp_db.get_next_company_id()
    comp = CompanyModel(
        company_id=c_id,
        company_name="NetSol Technologies",
        normalized_name="netsol technologies",
        official_website="https://www.netsoltech.com",
        normalized_domain="netsoltech.com",
        review_status="Confirmed"
    )
    temp_db.insert_or_update_company(comp)

    e_id = temp_db.get_next_executive_id()
    exec_m = ExecutiveModel(
        executive_id=e_id,
        company_id=c_id,
        name="Salim Ghauri",
        designation="Chief Executive Officer",
        is_ceo_or_founder=1,
        verification_status="Confirmed"
    )
    temp_db.insert_or_update_executive(exec_m)

    ct_id = temp_db.get_next_contact_id()
    contact = BusinessContactModel(
        contact_id=ct_id,
        company_id=c_id,
        executive_id=e_id,
        email="contact@netsoltech.com",
        phone="+92 42 111-444-666"
    )
    temp_db.insert_or_update_contact(contact)

    execs = temp_db.get_executives_for_company(c_id)
    contacts = temp_db.get_contacts_for_company(c_id)

    assert len(execs) == 1
    assert execs[0]["name"] == "Salim Ghauri"
    assert len(contacts) == 1
    assert contacts[0]["email"] == "contact@netsoltech.com"
