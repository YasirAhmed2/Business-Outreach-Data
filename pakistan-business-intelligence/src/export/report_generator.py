"""
Report Generator for Pakistan Business Intelligence System.
Produces comprehensive statistical, geographic, and quality analysis summaries.
"""

from typing import Dict, Any, List
from ..storage.database import DatabaseManager


class ReportGenerator:
    """Generates markdown and dictionary reports of discovery and verification state."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def generate_summary_dict(self) -> Dict[str, Any]:
        """Calculates detailed analytics from the database."""
        stats = self.db.get_system_stats()
        companies = self.db.get_all_companies(confirmed_only=False)

        cities_count = {}
        industries_count = {}
        for c in companies:
            city = c.get("city", "Other") or "Other"
            cities_count[city] = cities_count.get(city, 0) + 1

            ind = c.get("industry", "Other") or "Other"
            industries_count[ind] = industries_count.get(ind, 0) + 1

        return {
            "stats": stats,
            "cities_breakdown": dict(sorted(cities_count.items(), key=lambda item: item[1], reverse=True)),
            "industries_breakdown": dict(sorted(industries_count.items(), key=lambda item: item[1], reverse=True)),
        }

    def generate_markdown_report(self) -> str:
        """Formats an executive summary report in Markdown."""
        data = self.generate_summary_dict()
        stats = data["stats"]
        cities = data["cities_breakdown"]
        industries = data["industries_breakdown"]

        md = f"""# Pakistan Business & Executive Intelligence Report

## 1. Executive Summary
- **Total Authentic Companies Discovered:** {stats['total_discovered']}
- **Confirmed Authentic Companies (Cat A & B):** {stats['confirmed_companies']}
  - *Officially Corroborated (Category A):* {stats['officially_corroborated']}
  - *Officially Documented (Category B):* {stats['officially_documented']}
- **Companies Requiring Manual Review (Category C):** {stats['requires_review_companies']}
- **Decision Makers / Executives Identified:** {stats['total_executives']}
- **CEOs and Founders Identified:** {stats['total_ceos']}
- **Published Business Emails Discovered:** {stats['published_emails']}
  - *Direct Executive Mailboxes:* {stats['direct_emails']}
- **Published Phone Numbers Verified (+92):** {stats['published_phones']}

## 2. Top Geographic Hubs (Pakistan)
"""
        for city, count in list(cities.items())[:10]:
            md += f"- **{city}:** {count} businesses\n"

        md += "\n## 3. Major Industry Sectors\n"
        for ind, count in list(industries.items())[:10]:
            md += f"- **{ind}:** {count} companies\n"

        md += "\n## 4. Rigorous Quality Standards\n"
        md += "- Free local DNS MX validation conducted on email domains.\n"
        md += "- National Pakistani numbering plan (+92) validated via `phonenumbers`.\n"
        md += "- Zero synthetic or fabricated records permitted.\n"

        return md
