"""
Professional Multi-Sheet Excel Exporter for Pakistan Business Intelligence System.
Generates output/Pakistan_Business_Intelligence.xlsx with 12 required sheets,
frozen headers, auto-filters, custom column widths, and clickable hyperlinks.
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import List, Dict, Any, Optional
import logging
from ..storage.database import DatabaseManager
from ..discovery.source_registry import SourceRegistry

logger = logging.getLogger("ExcelExporter")


class ExcelExporter:
    """Exports structured business intelligence to formatted multi-sheet Excel workbooks."""

    HEADER_FILL = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")  # Navy Blue
    HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    DATA_FONT = Font(name="Calibri", size=10)
    LINK_FONT = Font(name="Calibri", size=10, color="0000FF", underline="single")
    BORDER = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    COLUMNS = [
        "Company ID", "Company Name", "Company Type", "Industry", "City", "Province",
        "Official Website", "Company Authenticity Status", "Executive Name",
        "Executive Designation", "LinkedIn URL", "Executive Verification Status",
        "Business Email", "Email Type", "Email Verification Status", "Business Phone",
        "Phone Verification Status", "Company Source URL", "Executive Source URL",
        "Contact Source URL", "First Discovered Date", "Last Verified Date",
        "Confidence Score", "Review Status"
    ]

    def __init__(self, db: DatabaseManager, output_path: str = "output/Pakistan_Business_Intelligence.xlsx"):
        self.db = db
        self.output_path = output_path
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    def _format_worksheet(self, ws, row_count: int, col_count: int) -> None:
        """Applies header styling, borders, auto-filter, freeze panes, and auto-column widths."""
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(col_count)}{max(1, row_count)}"

        # Format header row
        for col_idx in range(1, col_count + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Format data rows & adjust column width
        for col_idx in range(1, col_count + 1):
            max_len = len(str(ws.cell(row=1, column=col_idx).value or ""))
            for row_idx in range(2, row_count + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = self.BORDER
                cell.font = self.DATA_FONT
                val = str(cell.value or "")
                if len(val) > max_len:
                    max_len = len(val)
                # Format hyperlinks
                if val.startswith("http://") or val.startswith("https://"):
                    cell.hyperlink = val
                    cell.font = self.LINK_FONT

            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

        ws.row_dimensions[1].height = 28

    def _build_flat_records(self) -> List[Dict[str, Any]]:
        """Joins companies, executives, and contacts into standardized reporting rows."""
        companies = self.db.get_all_companies(confirmed_only=False)
        flat_records = []

        for comp in companies:
            c_id = comp["company_id"]
            execs = self.db.get_executives_for_company(c_id)
            contacts = self.db.get_contacts_for_company(c_id)

            # Determine primary executive
            primary_exec = execs[0] if execs else None
            primary_contact = contacts[0] if contacts else None

            # Calculate composite confidence score
            auth_score = comp.get("authenticity_score", 0.0) or 0.0
            exec_score = primary_exec.get("verification_score", 0.0) if primary_exec else 0.0
            cont_score = primary_contact.get("confidence_score", 0.0) if primary_contact else 0.0
            composite_score = round((auth_score * 0.4) + (exec_score * 0.3) + (cont_score * 0.3), 1)

            record = {
                "Company ID": c_id,
                "Company Name": comp.get("company_name", ""),
                "Company Type": comp.get("company_type", "Private Limited"),
                "Industry": comp.get("industry", "Business"),
                "City": comp.get("city", "Pakistan"),
                "Province": comp.get("province", "Pakistan"),
                "Official Website": comp.get("official_website", ""),
                "Company Authenticity Status": comp.get("authenticity_status", "Requires review"),
                "Executive Name": primary_exec.get("name", "Unavailable") if primary_exec else "Unavailable",
                "Executive Designation": primary_exec.get("designation", "Unavailable") if primary_exec else "Unavailable",
                "LinkedIn URL": primary_exec.get("linkedin_url", "") if primary_exec else "",
                "Executive Verification Status": primary_exec.get("verification_status", "Unavailable") if primary_exec else "Unavailable",
                "Business Email": primary_contact.get("email", "") if primary_contact else "",
                "Email Type": primary_contact.get("email_type", "Unavailable") if primary_contact else "Unavailable",
                "Email Verification Status": primary_contact.get("email_verification_status", "Unavailable") if primary_contact else "Unavailable",
                "Business Phone": primary_contact.get("phone", "") if primary_contact else "",
                "Phone Verification Status": primary_contact.get("phone_verification_status", "Unavailable") if primary_contact else "Unavailable",
                "Company Source URL": comp.get("source_url", ""),
                "Executive Source URL": primary_exec.get("source_url", "") if primary_exec else "",
                "Contact Source URL": primary_contact.get("contact_source_url", "") if primary_contact else "",
                "First Discovered Date": comp.get("first_discovered_at", ""),
                "Last Verified Date": comp.get("last_verified_at", ""),
                "Confidence Score": composite_score,
                "Review Status": comp.get("review_status", "Requires Review"),
                "raw_exec": primary_exec,
                "raw_contact": primary_contact,
                "raw_comp": comp
            }
            flat_records.append(record)

        return flat_records

    def export_workbook(self, target_filepath: Optional[str] = None) -> str:
        """
        Creates and writes all 12 sheets required by the specification:
        1. All Companies
        2. Verified Companies
        3. CEOs and Founders
        4. Other Decision Makers
        5. Direct Executive Contacts
        6. General Business Contacts
        7. Missing Contact Information
        8. Requires Manual Review
        9. Duplicate Records
        10. Data Quality Report
        11. Source Register
        12. Batch Processing Report
        """
        output_file = target_filepath or self.output_path
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        records = self._build_flat_records()

        # Helper to populate sheet
        def write_standard_sheet(title: str, rows_data: List[Dict[str, Any]]):
            ws = wb.create_sheet(title=title)
            ws.append(self.COLUMNS)
            for r in rows_data:
                ws.append([r.get(col, "") for col in self.COLUMNS])
            self._format_worksheet(ws, len(rows_data) + 1, len(self.COLUMNS))

        # 1. All Companies
        write_standard_sheet("All Companies", records)

        # 2. Verified Companies (Category A and B / Confirmed)
        verified_recs = [r for r in records if r["Review Status"] == "Confirmed"]
        write_standard_sheet("Verified Companies", verified_recs)

        # 3. CEOs and Founders
        ceo_recs = [
            r for r in records
            if r["raw_exec"] and r["raw_exec"].get("is_ceo_or_founder") == 1
        ]
        write_standard_sheet("CEOs and Founders", ceo_recs)

        # 4. Other Decision Makers
        other_exec_recs = [
            r for r in records
            if r["raw_exec"] and r["raw_exec"].get("is_ceo_or_founder") == 0 and r["Executive Name"] != "Unavailable"
        ]
        write_standard_sheet("Other Decision Makers", other_exec_recs)

        # 5. Direct Executive Contacts
        direct_contact_recs = [
            r for r in records
            if r["Email Type"] == "Direct executive email"
        ]
        write_standard_sheet("Direct Executive Contacts", direct_contact_recs)

        # 6. General Business Contacts
        general_contact_recs = [
            r for r in records
            if r["Email Type"] == "General company email" or r["Business Phone"]
        ]
        write_standard_sheet("General Business Contacts", general_contact_recs)

        # 7. Missing Contact Information (Honest reporting)
        missing_contact_recs = [
            r for r in records
            if not r["Business Email"] and not r["Business Phone"]
        ]
        write_standard_sheet("Missing Contact Information", missing_contact_recs)

        # 8. Requires Manual Review (Category C)
        review_recs = [r for r in records if r["Review Status"] == "Requires Review"]
        write_standard_sheet("Requires Manual Review", review_recs)

        # 9. Duplicate Records (Filtered out or resolved)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies WHERE review_status = 'Duplicate'")
            dup_rows = [dict(r) for r in cursor.fetchall()]
        dup_sheet_recs = [r for r in records if r["Review Status"] == "Duplicate"]
        write_standard_sheet("Duplicate Records", dup_sheet_recs)

        # 10. Data Quality Report
        ws_dq = wb.create_sheet(title="Data Quality Report")
        stats = self.db.get_system_stats()
        dq_headers = ["Metric", "Value", "Quality Assessment", "Standard"]
        ws_dq.append(dq_headers)
        ws_dq.append(["Total Authentic Companies Discovered", stats["total_discovered"], "High Confidence", "SECP/PSX/P@SHA/Chambers"])
        ws_dq.append(["Confirmed Companies (Category A & B)", stats["confirmed_companies"], "Corroborated / Documented", "Score >= 50%"])
        ws_dq.append(["Officially Corroborated (Category A)", stats["officially_corroborated"], "Highest Rigor", "Regulatory Cross-Check"])
        ws_dq.append(["Officially Documented (Category B)", stats["officially_documented"], "Direct Website / Institutional Listing", "Official Source"])
        ws_dq.append(["Companies Requiring Review (Category C)", stats["requires_review_companies"], "Pending Corroboration", "Isolated Reference"])
        ws_dq.append(["Decision Makers / Executives Identified", stats["total_executives"], "Published Leadership", "Official Leadership Only"])
        ws_dq.append(["CEOs and Founders Identified", stats["total_ceos"], "Executive Leadership", "PSX Disclosures / Team Pages"])
        ws_dq.append(["Published Business Emails Discovered", stats["published_emails"], "DNS MX Verified", "Free Local MX Verification"])
        ws_dq.append(["Direct Executive Emails", stats["direct_emails"], "Executive Mailboxes", "Personal Corporate Mailbox"])
        ws_dq.append(["Published Business Phones Verified", stats["published_phones"], "Normalized Pakistan Formats (+92)", "Phonenumbers PK Standard"])
        ws_dq.append(["Failed / Unreachable Websites Logged", stats["failed_records"], "Documented Exclusions", "Failed Records Log"])
        self._format_worksheet(ws_dq, 12, 4)

        # 11. Source Register
        ws_src = wb.create_sheet(title="Source Register")
        src_headers = ["Source ID", "Source Name", "Source Type", "Tier", "Official Base URL", "Authority Scope"]
        ws_src.append(src_headers)
        for s in SourceRegistry.get_all_sources():
            ws_src.append([s.source_id, s.source_name, s.source_type, f"Tier {s.tier}", s.base_url, s.description])
        self._format_worksheet(ws_src, len(SourceRegistry.SOURCES) + 1, len(src_headers))

        # 12. Batch Processing Report
        ws_batch = wb.create_sheet(title="Batch Processing Report")
        batch_headers = ["Batch #", "Start Index", "End Index", "Processed", "Confirmed Added", "Duplicates Skipped", "Failed", "Processed Timestamp", "Checkpoint File"]
        ws_batch.append(batch_headers)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM batch_progress ORDER BY batch_number ASC")
            batch_rows = cursor.fetchall()
            for b in batch_rows:
                ws_batch.append([
                    b["batch_number"], b["batch_start_index"], b["batch_end_index"],
                    b["companies_processed"], b["confirmed_added"], b["duplicates_skipped"],
                    b["failed_count"], b["processed_at"], b["checkpoint_excel_path"]
                ])
        self._format_worksheet(ws_batch, len(batch_rows) + 1, len(batch_headers))

        wb.save(output_file)
        logger.info(f"Successfully generated 12-sheet Excel workbook at {output_file}")
        return output_file
