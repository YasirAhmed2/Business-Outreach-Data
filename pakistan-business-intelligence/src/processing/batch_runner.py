"""
Autonomous Batch Runner for Pakistan Business Intelligence System.
Executes batch processing in configurable chunks (default: 50 companies per batch),
commits data to SQLite, saves Excel checkpoints, logs failed records, and supports pause/resume.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, List
from ..storage.database import DatabaseManager
from ..storage.models import FailedRecordModel, current_iso_time
from ..discovery.company_discovery import CompanyDiscoveryEngine
from ..discovery.source_registry import SourceRegistry
from ..verification.company_verification import CompanyVerifier
from ..verification.email_verification import EmailVerifier
from ..verification.phone_verification import PhoneVerifier
from ..research.executive_research import ExecutiveResearcher
from ..research.contact_research import ContactResearcher
from ..research.company_research import CompanyResearcher
from ..extraction.website_extractor import WebsiteExtractor
from ..processing.deduplication import DeduplicationEngine
from ..processing.checkpoint_manager import CheckpointManager
from ..processing.resume_manager import ResumeManager
from ..export.excel_exporter import ExcelExporter

logger = logging.getLogger("BatchRunner")


class BatchRunner:
    """Manages autonomous batch processing runs."""

    def __init__(self, config: Dict[str, Any], db: DatabaseManager):
        self.config = config
        self.db = db
        self.batch_size = config.get("targets", {}).get("batch_size", 50)
        self.total_target = config.get("targets", {}).get("total_companies_target", 1000)
        self.timeout = config.get("processing", {}).get("request_timeout_seconds", 15)
        self.user_agent = config.get("processing", {}).get("user_agent", "")

        # Initialize subcomponents
        self.extractor = WebsiteExtractor(timeout=self.timeout, user_agent=self.user_agent)
        self.email_verifier = EmailVerifier(timeout=config.get("verification", {}).get("mx_lookup_timeout_seconds", 5))
        self.phone_verifier = PhoneVerifier()
        self.company_verifier = CompanyVerifier(timeout=self.timeout, user_agent=self.user_agent)

        self.exec_researcher = ExecutiveResearcher(self.extractor)
        self.contact_researcher = ContactResearcher(self.extractor, self.email_verifier, self.phone_verifier)
        self.company_researcher = CompanyResearcher(self.db, self.company_verifier, self.exec_researcher, self.contact_researcher)

        self.discovery_engine = CompanyDiscoveryEngine(self.config)
        self.checkpoint_manager = CheckpointManager(self.db, self.config.get("paths", {}).get("checkpoints_dir", "output/checkpoints"))
        self.resume_manager = ResumeManager(self.db)
        self.exporter = ExcelExporter(self.db, self.config.get("paths", {}).get("excel_output", "output/Pakistan_Business_Intelligence.xlsx"))

        # Register all sources in database
        for src in SourceRegistry.get_all_sources():
            self.db.register_source(src)

    def run_pipeline(
        self,
        target_limit: Optional[int] = None,
        resume: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes discovery and research in batches of 50.
        Emits progress updates to progress_callback.
        """
        limit = target_limit or self.total_target
        job_id = f"JOB-{int(time.time())}"

        logger.info(f"Starting batch execution job {job_id} with target: {limit}")

        # Check resume state
        resume_state = self.resume_manager.get_resume_state()
        start_batch_num = resume_state["next_batch_number"] if resume else 1
        processed_candidates_count = resume_state["last_end_index"] if resume else 0

        # Discover candidate businesses
        all_candidates = self.discovery_engine.discover_all_candidates(target_limit=limit)
        total_discovered = len(all_candidates)
        logger.info(f"Discovered pool of {total_discovered} authentic businesses across Pakistan.")

        # If resuming, slice candidates from the last processed index
        remaining_candidates = all_candidates[processed_candidates_count:]
        current_batch_idx = start_batch_num

        total_confirmed_in_job = 0
        total_duplicates_in_job = 0
        total_failed_in_job = 0

        # Process in chunks of batch_size
        for i in range(0, len(remaining_candidates), self.batch_size):
            batch_slice = remaining_candidates[i:i + self.batch_size]
            batch_num = current_batch_idx
            start_idx = processed_candidates_count + i
            end_idx = start_idx + len(batch_slice)

            batch_confirmed = 0
            batch_duplicates = 0
            batch_failed = 0

            logger.info(f"Executing Batch {batch_num} (items {start_idx + 1} to {end_idx})...")

            for raw_cand in batch_slice:
                name = raw_cand.get("company_name", "")
                website = raw_cand.get("official_website", "")
                domain = DeduplicationEngine.normalize_domain(website)
                norm_name = DeduplicationEngine.normalize_company_name(name)

                # Check duplicate
                existing = self.db.get_company_by_domain_or_name(domain, norm_name)
                if existing:
                    logger.debug(f"Skipping duplicate company: {name}")
                    batch_duplicates += 1
                    total_duplicates_in_job += 1
                    continue

                try:
                    comp, execs, contacts = self.company_researcher.process_candidate(raw_cand)
                    if comp.review_status == "Confirmed":
                        batch_confirmed += 1
                        total_confirmed_in_job += 1
                except Exception as e:
                    logger.error(f"Error researching company {name}: {e}")
                    batch_failed += 1
                    total_failed_in_job += 1
                    self.db.record_failed(FailedRecordModel(
                        company_name=name,
                        attempted_url=website,
                        failure_stage="research",
                        error_reason=str(e),
                        source_url=raw_cand.get("source_url", ""),
                        attempted_at=current_iso_time()
                    ))

            # Export Excel checkpoint for this batch
            ckpt_excel = f"output/checkpoints/checkpoint_batch_{batch_num:02d}.xlsx"
            try:
                self.exporter.export_workbook(ckpt_excel)
            except Exception as e:
                logger.warning(f"Could not export batch excel checkpoint: {e}")

            # Save batch progress to database
            self.checkpoint_manager.save_batch_checkpoint(
                job_id=job_id,
                batch_number=batch_num,
                start_idx=start_idx,
                end_idx=end_idx,
                processed_count=len(batch_slice),
                confirmed_count=batch_confirmed,
                duplicates_count=batch_duplicates,
                failed_count=batch_failed,
                excel_path=ckpt_excel,
                notes=f"Batch {batch_num} completed successfully"
            )

            current_batch_idx += 1

            if progress_callback:
                progress_callback({
                    "job_id": job_id,
                    "batch_number": batch_num,
                    "processed": end_idx,
                    "total_pool": total_discovered,
                    "confirmed": total_confirmed_in_job,
                    "duplicates": total_duplicates_in_job,
                    "failed": total_failed_in_job
                })

        # Generate final main Excel export
        final_excel_path = self.exporter.export_workbook()

        stats = self.db.get_system_stats()
        logger.info(f"Pipeline finished! Final output: {final_excel_path}. Total confirmed: {stats['confirmed_companies']}")

        return {
            "job_id": job_id,
            "final_excel": final_excel_path,
            "stats": stats,
            "total_batches_run": current_batch_idx - start_batch_num
        }
