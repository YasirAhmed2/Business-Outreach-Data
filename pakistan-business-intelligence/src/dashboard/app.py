"""
Streamlit Local Dashboard for Pakistan Business Intelligence System.
Displays authentic metrics, live database records, source registers, failed logs,
and triggers batch runs and Excel exports.
"""

import os
import sys
import yaml
import pandas as pd
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.storage.database import DatabaseManager
from src.processing.batch_runner import BatchRunner
from src.export.excel_exporter import ExcelExporter
from src.export.report_generator import ReportGenerator
from src.discovery.source_registry import SourceRegistry


st.set_page_config(
    page_title="Pakistan Autonomous Business & Executive Intelligence",
    page_icon="🇵🇰",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_config():
    config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()
db_path = os.path.join(PROJECT_ROOT, config.get("paths", {}).get("database", "database/pakistan_business_intelligence.db"))
db = DatabaseManager(db_path)


# Sidebar controls
st.sidebar.title("🇵🇰 System Controls")
st.sidebar.markdown("**Autonomous Research Engine**")

target_limit = st.sidebar.number_input(
    "Target Companies Target",
    min_value=10,
    max_value=2000,
    value=config.get("targets", {}).get("total_companies_target", 1000),
    step=10
)

batch_size = st.sidebar.slider("Batch Size", min_value=10, max_value=100, value=50, step=10)

col_b1, col_b2 = st.sidebar.columns(2)
run_clicked = col_b1.button("🚀 Start Discovery", use_container_width=True)
export_clicked = col_b2.button("📥 Export Excel", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Permitted Tier 1 Sources")
st.sidebar.markdown("- 🏛️ Pakistan Stock Exchange (PSX)")
st.sidebar.markdown("- 🏢 SECP Public Registrar")
st.sidebar.markdown("- 💻 P@SHA & PSEB IT Registry")
st.sidebar.markdown("- 🚀 Ignite & National Incubation Centers")
st.sidebar.markdown("- 🏭 Pakistani Chambers of Commerce")


# Main Dashboard Header
st.title("Pakistan Autonomous Business & Executive Intelligence System")
st.markdown(
    "Evidence-based intelligence engine discovering and verifying authentic Pakistani companies, "
    "SMEs, startups, corporate decision-makers, and business contact information."
)

stats = db.get_system_stats()
target_total = target_limit
remaining = max(0, target_total - stats["confirmed_companies"])

# Row 1: Primary Metrics
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Target Goal", f"{target_total:,}")
kpi1.caption("Autonomous Discovery Target")

kpi2.metric("Authentic Discovered", f"{stats['total_discovered']:,}")
kpi2.caption("Total candidate businesses")

kpi3.metric("Confirmed Companies", f"{stats['confirmed_companies']:,}")
kpi3.caption("Category A & B verified")

kpi4.metric("Requires Review", f"{stats['requires_review_companies']:,}")
kpi4.caption("Category C pending review")

kpi5.metric("Remaining to Target", f"{remaining:,}")
kpi5.caption("Unfulfilled quota")

# Row 2: Executives & Contact Metrics
kpi6, kpi7, kpi8, kpi9, kpi10 = st.columns(5)
kpi6.metric("Executives Identified", f"{stats['total_executives']:,}")
kpi6.caption("Decision-makers found")

kpi7.metric("CEOs & Founders", f"{stats['total_ceos']:,}")
kpi7.caption("Top leadership verified")

kpi8.metric("Business Emails (MX)", f"{stats['published_emails']:,}")
kpi8.caption(f"Direct: {stats['direct_emails']}")

kpi9.metric("Phones Verified (+92)", f"{stats['published_phones']:,}")
kpi9.caption("Normalized Pakistan numbers")

kpi10.metric("Current Batch", f"Batch {stats['current_batch']}")
kpi10.caption("Checkpoint sequence")


# Discovery Action Runner
if run_clicked:
    st.info(f"Starting autonomous discovery and verification for up to {target_limit} authentic companies...")
    progress_bar = st.progress(0)
    status_text = st.empty()

    runner = BatchRunner(config, db)

    def ui_progress(prog):
        pct = min(1.0, prog["processed"] / max(1, prog["total_pool"]))
        progress_bar.progress(pct)
        status_text.markdown(
            f"**Batch {prog['batch_number']} Completed** | Processed: {prog['processed']}/{prog['total_pool']} | "
            f"Confirmed: {prog['confirmed']} | Duplicates skipped: {prog['duplicates']}"
        )

    with st.spinner("Processing batches..."):
        result = runner.run_pipeline(
            target_limit=target_limit,
            resume=True,
            progress_callback=ui_progress
        )

    st.success(f"Pipeline executed successfully! Output updated at: {result['final_excel']}")
    st.rerun()

# Export Action
if export_clicked:
    with st.spinner("Compiling multi-sheet Excel workbook..."):
        exporter = ExcelExporter(db, os.path.join(PROJECT_ROOT, config.get("paths", {}).get("excel_output", "output/Pakistan_Business_Intelligence.xlsx")))
        out_path = exporter.export_workbook()
    st.success(f"Generated 12-sheet Excel report at: {out_path}")
    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            st.download_button(
                label="📥 Download Pakistan_Business_Intelligence.xlsx",
                data=f,
                file_name="Pakistan_Business_Intelligence.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# Tabs for deeper exploration
tab_comp, tab_exec, tab_contact, tab_geo, tab_sources, tab_failed = st.tabs([
    "🏢 Verified Companies",
    "👔 Executives & Leadership",
    "📞 Contacts & Emails",
    "📍 Geographic & Sector Intelligence",
    "📚 Source Register",
    "⚠️ Failed / Review Records"
])

with tab_comp:
    st.subheader("Confirmed Pakistani Businesses & Enterprises")
    companies = db.get_all_companies(confirmed_only=False)
    if companies:
        df_comp = pd.DataFrame(companies)
        cols_show = ["company_id", "company_name", "company_type", "industry", "city", "province", "official_website", "authenticity_category", "authenticity_score", "review_status"]
        st.dataframe(df_comp[cols_show], use_container_width=True)
    else:
        st.info("No companies processed yet. Click 'Start Discovery' to begin.")

with tab_exec:
    st.subheader("Identified CEOs, Founders & Senior Executives")
    with db.get_connection() as conn:
        df_exec = pd.read_sql_query("SELECT e.*, c.company_name FROM executives e JOIN companies c ON e.company_id = c.company_id", conn)
    if not df_exec.empty:
        st.dataframe(df_exec[["company_name", "name", "designation", "normalized_role", "is_ceo_or_founder", "verification_status", "verification_score", "linkedin_url"]], use_container_width=True)
    else:
        st.info("No executive records found yet.")

with tab_contact:
    st.subheader("Published Business Emails & Pakistani Phone Numbers")
    with db.get_connection() as conn:
        df_cont = pd.read_sql_query("SELECT b.*, c.company_name FROM business_contacts b JOIN companies c ON b.company_id = c.company_id", conn)
    if not df_cont.empty:
        st.dataframe(df_cont[["company_name", "email", "email_type", "email_verification_status", "phone", "phone_type", "phone_verification_status", "confidence_score"]], use_container_width=True)
    else:
        st.info("No contact records found yet.")

with tab_geo:
    st.subheader("Geographic & Industry Analytics")
    rep = ReportGenerator(db)
    summary = rep.generate_summary_dict()

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("#### Businesses by City")
        if summary["cities_breakdown"]:
            df_cities = pd.DataFrame(list(summary["cities_breakdown"].items()), columns=["City", "Count"])
            st.bar_chart(df_cities.set_index("City"))
        else:
            st.write("No geographic data available yet.")

    with col_g2:
        st.markdown("#### Businesses by Industry")
        if summary["industries_breakdown"]:
            df_ind = pd.DataFrame(list(summary["industries_breakdown"].items()), columns=["Industry", "Count"])
            st.bar_chart(df_ind.set_index("Industry"))
        else:
            st.write("No industry data available yet.")

with tab_sources:
    st.subheader("Permitted Statutory & Institutional Sources")
    sources = SourceRegistry.get_all_sources()
    df_src = pd.DataFrame([s.to_dict() for s in sources])
    st.dataframe(df_src[["source_id", "source_name", "tier", "source_type", "base_url", "description"]], use_container_width=True)

with tab_failed:
    st.subheader("Failed / Excluded Records & Diagnostic Reasons")
    with db.get_connection() as conn:
        df_fail = pd.read_sql_query("SELECT * FROM failed_records ORDER BY id DESC", conn)
    if not df_fail.empty:
        st.dataframe(df_fail, use_container_width=True)
    else:
        st.write("No failed records recorded.")
