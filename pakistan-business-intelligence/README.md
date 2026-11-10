# Pakistan Autonomous Business & Executive Intelligence System

An autonomous, evidence-based research and data collection system engineered to discover, verify, and document authentic Pakistani companies, business enterprises, technology startups, SMEs, and listed corporations across Pakistan.

The system operates autonomously without requiring manual CSV uploads or manually entered company URLs. It pulls from legitimate public and institutional sources, executes free local verification (DNS MX and Pakistan telephone normalization), extracts executive leadership and contact details from official sources, and outputs a 12-sheet Excel workbook along with an interactive Streamlit dashboard.

---

## 📌 Key Architectural Principles

1. **Zero Fabrication & Strict Authenticity**:
   - **No dummy companies.**
   - **No fabricated executives.**
   - **No invented email addresses or guessed phone numbers.**
   - Unverified records are honestly marked as `Unavailable` or `Requires Review`.
   - Data quality strictly takes priority over raw quantity.

2. **Permitted Discovery Sources**:
   - **Tier 1 (Official & Statutory)**:
     - **Pakistan Stock Exchange (PSX)** (`dps.psx.com.pk`): Statutory directory of companies listed across 35+ industry sectors (Technology, Pharmaceuticals, Banking, Cement, Textiles, Fertilizers, Automotive, Food, Oil & Gas).
     - **Securities and Exchange Commission of Pakistan (SECP)**: Official corporate registrar records and public filings.
     - **Pakistan Software Export Board (PSEB)**: Official directory of registered IT, ITeS, and software export firms.
     - **Pakistan Software Houses Association (P@SHA)**: Apex trade body corporate member directory.
     - **Ignite National Technology Fund & National Incubation Centers (NICs)**: Startups incubated across NIC Karachi, NIC Lahore (LUMS), NIC Islamabad, NIC Peshawar, NIC Quetta, NIC Faisalabad, and NICAT.
     - **Higher Education Commission (HEC) Business Incubation Centers**: University incubators at NUST, LUMS, IBA, FAST-NUCES, UET, and GIKI.
   - **Tier 2 (Ecosystem, Chambers & Commercial Registries)**:
     - **Rozee.pk & Indeed Business Ecosystem**: Public directories of registered Pakistani employers, SMEs, and commercial businesses.
     - **Pakistani Chambers of Commerce & Industry**: Regional business directories from Karachi (KCCI), Lahore (LCCI), Islamabad (ICCI), Sialkot (SCCI), Faisalabad (FCCI), and Gujranwala (GCCI).
     - **Official Corporate Websites & Disclosures**: Leadership pages, financial reports, and official announcements.

3. **Strict Compliance Policy Regarding LinkedIn**:
   - LinkedIn may be used by the human operator for manual professional research.
   - **The system does NOT automate LinkedIn login, browsing, scrolling, clicking, messaging, profile scraping, or anti-detection evasion.**
   - The system records public LinkedIn profile URLs only when discovered legitimately on company leadership/team pages or institutional portals.

4. **Free Local Data Verification**:
   - **Emails**: Syntax validation (`email-validator`) + Live DNS MX record resolution (`dnspython`). Distinguishes between direct executive mailboxes and general company mailboxes (`info@`, `contact@`, `sales@`).
   - **Phones**: National Pakistani numbering plan validation and international normalization (`+92`) using Google's `phonenumbers` library. Supports Landlines (Karachi `021`, Lahore `042`, Islamabad `051`, etc.), Mobile numbers (`03xx`), and UANs (`111-xxx-xxx`).
   - **Websites**: SSL/HTTP connectivity checks, robots.txt compliance, and domain normalization.

---

## 🗂️ Project Directory Structure

```text
pakistan-business-intelligence/
├── main.py                     # Primary CLI runner (discovery, resume, export, report)
├── config.yaml                 # System settings, sources, batch sizes, timeouts
├── requirements.txt            # Python dependencies (openpyxl, dnspython, phonenumbers, etc.)
├── README.md                   # Full operational and setup documentation
├── src/
│   ├── discovery/
│   │   ├── institutional_sources.py  # PSX, PSEB, P@SHA, SECP, Ignite NICs
│   │   ├── directory_discovery.py    # Rozee, Chambers (KCCI, LCCI, SCCI), Portfolios
│   │   ├── company_discovery.py      # Unified discovery orchestrator
│   │   └── source_registry.py        # Authoritative source definitions & metadata
│   ├── research/
│   │   ├── company_research.py       # Candidate research pipeline coordinator
│   │   ├── executive_research.py     # Leadership discovery & statutory filings
│   │   └── contact_research.py       # Email & phone research + verification
│   ├── extraction/
│   │   ├── website_extractor.py      # Safe crawler with subpage discovery
│   │   ├── leadership_extractor.py   # Team/leadership page parsing & card extraction
│   │   └── contact_extractor.py      # Regex & HTML parsing for PK emails & phones
│   ├── verification/
│   │   ├── company_verification.py   # Authenticity classification (Category A, B, C)
│   │   ├── executive_verification.py # Title matching (CEO, Founder, MD, CTO, COO)
│   │   ├── email_verification.py     # Syntax + DNS MX record lookups
│   │   ├── phone_verification.py     # Pakistani (+92) phone normalization
│   │   └── quality_scoring.py        # Transparent 0-100 quality scoring
│   ├── processing/
│   │   ├── batch_runner.py           # 50-company batch runner with checkpoints
│   │   ├── deduplication.py          # Corporate name and domain deduplication
│   │   ├── checkpoint_manager.py     # SQLite and JSON checkpoint tracking
│   │   └── resume_manager.py         # Safe interruption & resume coordinator
│   ├── storage/
│   │   ├── database.py               # SQLite DatabaseManager with full schema
│   │   └── models.py                 # Dataclasses (Company, Executive, Contact, etc.)
│   ├── export/
│   │   ├── excel_exporter.py         # 12-sheet Excel generator with openpyxl styling
│   │   └── report_generator.py       # Quality and geographic summary generator
│   └── dashboard/
│       └── app.py                    # Streamlit web dashboard
├── database/
│   └── pakistan_business_intelligence.db  # Relational SQLite database
├── output/
│   ├── Pakistan_Business_Intelligence.xlsx # Master 12-sheet deliverable
│   └── checkpoints/                        # Batch checkpoint workbooks
├── logs/
│   └── system.log                    # Diagnostic log traces
└── tests/                            # Automated test suite (13 passing pytest tests)
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11 or higher
- Git

### 1. Clone or Open Workspace
```bash
cd "D:\Business outreach data\pakistan-business-intelligence"
```

### 2. Create and Activate Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Required Dependencies
All required libraries are free and open-source:
```bash
pip install -r requirements.txt
```

---

## 💻 How to Execute the System

### 1. Run Discovery with Target Quota
You can specify the number of authentic companies to discover and verify:

```bash
# Discover 20 companies (initial verification test)
python main.py --target 20

# Discover 100 companies
python main.py --target 100

# Discover 500 companies
python main.py --target 500

# Discover full target of 1,000 authentic companies
python main.py --target 1000
```

### 2. Resuming Interrupted Runs
The system automatically saves progress after every batch of 50 companies into SQLite and Excel checkpoints. If a run is paused or interrupted, simply rerun:
```bash
python main.py --target 1000
```
The `ResumeManager` will detect existing records and pick up at the exact batch where it stopped.

### 3. Fresh Discovery Run
To bypass resume and restart fresh:
```bash
python main.py --target 100 --fresh
```

### 4. Export Excel Workbook
To compile or refresh the 12-sheet Excel deliverable at any time from the SQLite database:
```bash
python main.py --export
```
Output is saved to `output/Pakistan_Business_Intelligence.xlsx`.

### 5. Generate Console Quality Report
```bash
python main.py --report
```

### 6. Launch the Local Streamlit Dashboard
```bash
python main.py --dashboard
# or directly:
streamlit run src/dashboard/app.py
```
Open your browser at `http://localhost:8501` to view live KPI cards, interactive tables, charts, and trigger runs.

---

## 📊 Excel Deliverable Structure

The output file `output/Pakistan_Business_Intelligence.xlsx` contains **12 distinct sheets**:

| Sheet # | Sheet Name | Description |
|---|---|---|
| **1** | **All Companies** | Master inventory of all discovered business entities. |
| **2** | **Verified Companies** | Only Category A & Category B companies meeting authenticity thresholds. |
| **3** | **CEOs and Founders** | Discovered Chief Executive Officers, Founders, and Managing Directors. |
| **4** | **Other Decision Makers** | CTOs, COOs, CIOs, Heads of Tech, and senior executive directors. |
| **5** | **Direct Executive Contacts** | Confirmed direct personal corporate mailboxes. |
| **6** | **General Business Contacts** | Corporate contact mailboxes (`info@`, `contact@`) and company phone lines. |
| **7** | **Missing Contact Information** | Honest register of businesses where contact info is not published. |
| **8** | **Requires Manual Review** | Category C companies flagged for operator review. |
| **9** | **Duplicate Records** | Companies merged or filtered out by domain/name normalization. |
| **10** | **Data Quality Report** | Statistical audit of authenticity tiers, MX checks, and phone validation. |
| **11** | **Source Register** | Complete directory of sources (PSX, SECP, P@SHA, NICs, Chambers). |
| **12** | **Batch Processing Report** | Execution audit of batches, timestamps, and checkpoint file paths. |

### Standard Columns Across Sheets:
1. `Company ID`
2. `Company Name`
3. `Company Type` (Public Listed, Private Limited, Startup, SME)
4. `Industry` (Tech, Banking, Textiles, Pharma, FMCG, Logistics, etc.)
5. `City` (Karachi, Lahore, Islamabad, Faisalabad, Sialkot, Gujranwala, Peshawar, Quetta)
6. `Province` (Sindh, Punjab, ICT, KP, Balochistan)
7. `Official Website` (Clickable Hyperlink)
8. `Company Authenticity Status` (Officially corroborated / Officially documented / Requires review)
9. `Executive Name`
10. `Executive Designation`
11. `LinkedIn URL` (Recorded only from official company team pages)
12. `Executive Verification Status` (Confirmed / Documented / Unavailable)
13. `Business Email`
14. `Email Type` (Direct executive email / General company email / Unavailable)
15. `Email Verification Status` (MX Confirmed / Syntax Validated / Failed MX / Unavailable)
16. `Business Phone`
17. `Phone Verification Status` (Valid PK Phone / Invalid Format / Unavailable)
18. `Company Source URL` (Clickable Link)
19. `Executive Source URL` (Clickable Link)
20. `Contact Source URL` (Clickable Link)
21. `First Discovered Date`
22. `Last Verified Date`
23. `Confidence Score` (Evidence-based 0.0 - 100.0)
24. `Review Status` (Confirmed / Requires Review / Duplicate)

---

## 🧪 Running Automated Tests

Run the test suite with pytest:
```bash
python -m pytest tests
```
Tests cover:
- Data models and serialization (`test_models.py`)
- SQLite database transactions, foreign keys, and relations (`test_database.py`)
- Deduplication and name/domain normalization (`test_deduplication.py`)
- Email DNS MX, phone (+92), and quality scoring verification (`test_verification.py`)
- Multi-sheet Excel workbook generation with 12 sheets (`test_excel_exporter.py`)

---

## 📈 Expanding the Dataset

To expand the dataset with additional sources:
1. **Add new sources in `config.yaml`**: Enable or adjust source weights and tiers.
2. **Add institutional seeds in `src/discovery/`**:
   - For stock exchange data: Edit `src/discovery/institutional_sources.py`
   - For chambers of commerce or industrial estates: Edit `src/discovery/directory_discovery.py`
3. **Execute next batch**: Run `python main.py --target <count>` to continue scaling up to 1,000+ companies.
