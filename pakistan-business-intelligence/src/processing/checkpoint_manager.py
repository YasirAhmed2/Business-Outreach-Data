"""
Checkpoint Manager for Pakistan Business Intelligence System.
Saves intermediate batch states, tracks batch indexes, and creates rollback/checkpoint points.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ..storage.models import BatchProgressModel, current_iso_time
from ..storage.database import DatabaseManager

logger = logging.getLogger("CheckpointManager")


class CheckpointManager:
    """Manages checkpoints and batch state persistence."""

    def __init__(self, db: DatabaseManager, checkpoints_dir: str = "output/checkpoints"):
        self.db = db
        self.checkpoints_dir = checkpoints_dir
        os.makedirs(self.checkpoints_dir, exist_ok=True)

    def save_batch_checkpoint(
        self,
        job_id: str,
        batch_number: int,
        start_idx: int,
        end_idx: int,
        processed_count: int,
        confirmed_count: int,
        duplicates_count: int,
        failed_count: int,
        excel_path: str = "",
        notes: str = ""
    ) -> BatchProgressModel:
        """Records batch completion into SQLite and writes metadata checkpoint file."""
        progress = BatchProgressModel(
            job_id=job_id,
            batch_number=batch_number,
            batch_start_index=start_idx,
            batch_end_index=end_idx,
            companies_processed=processed_count,
            confirmed_added=confirmed_count,
            duplicates_skipped=duplicates_count,
            failed_count=failed_count,
            checkpoint_excel_path=excel_path,
            processed_at=current_iso_time(),
            notes=notes
        )

        self.db.record_batch_progress(progress)

        # Write JSON checkpoint file
        ckpt_file = os.path.join(self.checkpoints_dir, f"batch_{batch_number:03d}_checkpoint.json")
        try:
            with open(ckpt_file, "w", encoding="utf-8") as f:
                json.dump(progress.to_dict(), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write JSON checkpoint file {ckpt_file}: {e}")

        logger.info(f"Batch {batch_number} checkpoint saved. Processed: {processed_count}, Confirmed: {confirmed_count}")
        return progress
