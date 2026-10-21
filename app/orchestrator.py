"""
Orchestrator Module.
Controls the autonomous workflow:
INPUT → GENERATE → EVALUATE → REGENERATE IF NECESSARY → FINAL DECISION → OUTPUT AND LOGS
Enforces hard pass/fail rules, bounded retries (max 2 retries, 3 versions), and persistent memory updates.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.config import DEFAULT_TOPIC, MAX_RETRIES
from app.models import (
    RunRecord, LessonVersion, EvaluationReport, RunDecision,
    PassFailResult
)
from app.generator import LessonGenerator
from app.evaluator import RubricEvaluator
from app.feedback import FeedbackBuilder
from app.memory import MemoryManager
from app.logger import SystemLogger
from app.output import OutputManager


class WorkflowOrchestrator:
    def __init__(
        self,
        generator: Optional[LessonGenerator] = None,
        evaluator: Optional[RubricEvaluator] = None,
        memory: Optional[MemoryManager] = None,
        output_manager: Optional[OutputManager] = None,
        max_retries: int = MAX_RETRIES
    ):
        self.generator = generator or LessonGenerator()
        self.evaluator = evaluator or RubricEvaluator()
        self.memory = memory or MemoryManager()
        self.output_manager = output_manager or OutputManager()
        self.max_retries = max_retries

    def run_pipeline(
        self,
        topic: str = DEFAULT_TOPIC,
        inject_flaw: Optional[str] = None
    ) -> RunRecord:
        """
        Executes the full autonomous quality-control pipeline.
        Returns the persistent RunRecord with all versions, evaluations, and decision.
        """
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        start_time = datetime.now(timezone.utc).isoformat()

        SystemLogger.banner(
            f"Self-Evaluating Lesson Generator",
            f"Topic: {topic} | Run ID: {run_id}"
        )

        record = RunRecord(
            run_id=run_id,
            topic=topic,
            created_at=start_time,
            status=RunDecision.ERROR,  # Default until determined
            total_versions=0,
            retry_count=0,
            versions=[]
        )

        try:
            # Step 1: Memory Retrieval
            SystemLogger.step(1, "Memory Retrieval", "Loading prior failure patterns and learned insights...")
            prior_learnings = self.memory.get_prior_learnings_prompt_text()
            SystemLogger.info("Prior learning context loaded successfully.")

            # Step 2: Initial Generation (Version 1)
            SystemLogger.step(2, "Initial Generation", "Generating initial lesson draft (Version 1)...")
            v1_text = self.generator.generate_initial_lesson(
                topic=topic,
                prior_learnings=prior_learnings,
                inject_flaw=inject_flaw
            )

            # Step 3: Initial Evaluation
            SystemLogger.step(3, "Rubric Evaluation", "Evaluating Version 1 against all 12 checkpoints...")
            v1_eval = self.evaluator.evaluate(v1_text)
            SystemLogger.render_evaluation_report(v1_eval, version=1)

            v1_record = LessonVersion(
                version_number=1,
                lesson_text=v1_text,
                generated_at=datetime.now(timezone.utc).isoformat(),
                changes_from_previous=None,
                evaluation=v1_eval
            )
            record.versions.append(v1_record)
            record.total_versions = 1

            # Step 4: Decision or Regeneration Loop
            current_eval = v1_eval
            current_text = v1_text
            retry_count = 0

            while not current_eval.is_approved() and retry_count < self.max_retries:
                retry_count += 1
                version_num = retry_count + 1

                SystemLogger.step(
                    4,
                    f"Regeneration Attempt {retry_count} of {self.max_retries}",
                    f"Version {version_num - 1} failed checkpoints. Compiling feedback and regenerating..."
                )

                # Formulate actionable feedback
                feedback_text = FeedbackBuilder.build_feedback(current_eval)
                SystemLogger.warning(f"Rejection Feedback compiled:\n{feedback_text}")

                # Regenerate with feedback and prior learnings
                revised_text = self.generator.regenerate_lesson(
                    topic=topic,
                    failed_lesson_text=current_text,
                    evaluator_feedback=feedback_text,
                    prior_learnings=prior_learnings
                )

                # Track diff
                diff_summary = FeedbackBuilder.compute_diff_summary(current_text, revised_text)
                SystemLogger.info(diff_summary)

                # Re-evaluate revised lesson from scratch
                SystemLogger.info(f"Re-evaluating revised lesson (Version {version_num})...")
                revised_eval = self.evaluator.evaluate(revised_text)
                SystemLogger.render_evaluation_report(revised_eval, version=version_num)

                # Record version
                v_record = LessonVersion(
                    version_number=version_num,
                    lesson_text=revised_text,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    changes_from_previous=diff_summary,
                    evaluation=revised_eval
                )
                record.versions.append(v_record)
                record.total_versions = version_num
                record.retry_count = retry_count

                current_text = revised_text
                current_eval = revised_eval

            # Step 5: Final Terminal Decision
            if current_eval.is_approved():
                record.status = RunDecision.APPROVED
                SystemLogger.render_decision(RunDecision.APPROVED, retry_count, run_id)
            else:
                record.status = RunDecision.REJECTED
                SystemLogger.render_decision(RunDecision.REJECTED, retry_count, run_id)

            # Step 6: Learning and Persistent Memory Update
            self._update_persistent_memory(record)

            # Step 7: Output Persistence
            saved_paths = self.output_manager.save_run_outputs(record)
            SystemLogger.info(f"Run report persisted to: {saved_paths['report_path']}")
            SystemLogger.info(f"Audit log persisted to: {saved_paths['rejection_log_path']}")

            return record

        except Exception as e:
            SystemLogger.error(f"Fatal operational exception in workflow: {e}")
            record.status = RunDecision.ERROR
            record.error_details = str(e)
            self.memory.save_run(record)
            self.output_manager.save_run_outputs(record)
            SystemLogger.render_decision(RunDecision.ERROR, record.retry_count, run_id)
            return record

    def _update_persistent_memory(self, record: RunRecord):
        """Saves run to SQLite and records new learning insights into JSON memory."""
        # 1. SQLite Storage
        self.memory.save_run(record)

        # 2. Extract recurring failures to update JSON memory
        all_failed_cps = []
        for v in record.versions:
            if v.evaluation:
                failed = [cp.checkpoint_id for cp in v.evaluation.checkpoints if cp.result == PassFailResult.FAIL]
                all_failed_cps.extend(failed)

        if all_failed_cps:
            insight_msg = f"Observed {len(all_failed_cps)} checkpoint failures during run."
            correction_msg = (
                "Reinforce early jargon definitions and explicit analogy-to-system mappings in initial generation."
            )
            self.memory.record_run_insight(
                run_id=record.run_id,
                topic=record.topic,
                failed_checkpoints=list(set(all_failed_cps)),
                insight=insight_msg,
                correction=correction_msg
            )
