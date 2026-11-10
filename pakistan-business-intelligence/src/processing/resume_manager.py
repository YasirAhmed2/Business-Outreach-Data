"""
Resume Manager for Pakistan Business Intelligence System.
Inspects database state and checkpoints to enable seamless resumption without restarting work.
"""

from typing import Tuple, Optional, Dict, Any
import logging
from ..storage.database import DatabaseManager

logger = logging.getLogger("ResumeManager")


class ResumeManager:
    """Detects previous run progress and calculates resume parameters."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_resume_state(self) -> Dict[str, Any]:
        """
        Determines the last processed batch number, count of processed companies,
        and whether existing state is present.
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(batch_number), MAX(batch_end_index) FROM batch_progress")
            row = cursor.fetchone()
            last_batch = row[0] or 0
            last_end_idx = row[1] or 0

            cursor.execute("SELECT COUNT(*) FROM companies")
            companies_count = cursor.fetchone()[0]

            can_resume = (last_batch > 0 or companies_count > 0)

            return {
                "can_resume": can_resume,
                "last_batch_number": last_batch,
                "next_batch_number": last_batch + 1,
                "last_end_index": last_end_idx,
                "total_companies_in_db": companies_count
            }
