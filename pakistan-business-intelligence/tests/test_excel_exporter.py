"""
Unit tests for multi-sheet Excel export.
"""

import os
import pytest
import tempfile
import openpyxl
from src.storage.database import DatabaseManager
from src.storage.models import CompanyModel, ExecutiveModel, BusinessContactModel
from src.export.excel_exporter import ExcelExporter


def test_excel_export_all_12_sheets():
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "test_excel.db")
    excel_file = os.path.join(temp_dir, "test_output.xlsx")

    db = DatabaseManager(db_file)

    # Insert verified company
    c_id = db.get_next_company_id()
    comp = CompanyModel(
        company_id=c_id,
        company_name="Systems Limited",
        normalized_name="systems",
        company_type="Public Listed",
        industry="Technology",
        city="Lahore",
        province="Punjab",
        official_website="https://www.systemsltd.com",
        authenticity_status="Officially corroborated",
        authenticity_category="A",
        review_status="Confirmed"
    )
    db.insert_or_update_company(comp)

    # Insert executive
    e_id = db.get_next_executive_id()
    ex = ExecutiveModel(
        executive_id=e_id,
        company_id=c_id,
        name="Asif Peer",
        designation="Chief Executive Officer",
        is_ceo_or_founder=1,
        verification_status="Confirmed"
    )
    db.insert_or_update_executive(ex)

    # Insert contact
    ct_id = db.get_next_contact_id()
    ct = BusinessContactModel(
        contact_id=ct_id,
        company_id=c_id,
        executive_id=e_id,
        email="info@systemsltd.com",
        email_type="General company email",
        phone="+92 42 111-797-836"
    )
    db.insert_or_update_contact(ct)

    exporter = ExcelExporter(db, excel_file)
    exported_path = exporter.export_workbook()

    assert os.path.exists(exported_path)

    wb = openpyxl.load_workbook(exported_path)
    sheet_names = wb.sheetnames

    expected_sheets = [
        "All Companies",
        "Verified Companies",
        "CEOs and Founders",
        "Other Decision Makers",
        "Direct Executive Contacts",
        "General Business Contacts",
        "Missing Contact Information",
        "Requires Manual Review",
        "Duplicate Records",
        "Data Quality Report",
        "Source Register",
        "Batch Processing Report"
    ]

    for expected in expected_sheets:
        assert expected in sheet_names, f"Missing sheet: {expected}"

    # Verify All Companies sheet has data
    ws_all = wb["All Companies"]
    assert ws_all.max_row >= 2
    assert ws_all.cell(row=2, column=2).value == "Systems Limited"

    wb.close()
