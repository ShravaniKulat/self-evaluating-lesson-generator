"""
Output Manager Module.
Saves final approved/rejected lessons, comprehensive JSON run reports,
and detailed markdown rejection/revision logs.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.config import OUTPUTS_DIR, DOCS_DIR
from app.models import RunRecord, RunDecision
from app.logger import SystemLogger


class OutputManager:
    def __init__(self, outputs_dir: Path = OUTPUTS_DIR, docs_dir: Path = DOCS_DIR):
        self.outputs_dir = outputs_dir
        self.docs_dir = docs_dir
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def save_run_outputs(self, record: RunRecord, final_lesson_target: Optional[Path] = None) -> dict:
        """
        Saves all run artifacts:
        1. JSON run report
        2. Markdown rejection and revision log
        3. Lesson text file
        4. docs/final_lesson.md (only if APPROVED)
        """
        run_id = record.run_id
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        report_path = self.outputs_dir / f"run_{run_id}_report.json"
        rejection_log_path = self.outputs_dir / f"run_{run_id}_rejection_log.md"
        lesson_path = self.outputs_dir / f"run_{run_id}_lesson_v{record.total_versions}.md"

        # 1. Save JSON Report
        report_dict = record.model_dump()
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        # 2. Save Markdown Rejection & Revision Log
        rejection_log_content = self._build_rejection_log(record)
        with open(rejection_log_path, "w", encoding="utf-8") as f:
            f.write(rejection_log_content)

        # 3. Save Latest Lesson
        latest_lesson_text = record.versions[-1].lesson_text if record.versions else "No lesson generated."
        with open(lesson_path, "w", encoding="utf-8") as f:
            f.write(latest_lesson_text)

        # 4. If APPROVED, save to docs/final_lesson.md as required by assessment
        docs_lesson_path = final_lesson_target or (self.docs_dir / "final_lesson.md")
        if record.status == RunDecision.APPROVED:
            header_metadata = f"""---
title: "{record.topic}"
run_id: "{record.run_id}"
approval_status: "{record.status.value}"
total_versions: {record.total_versions}
retries_used: {record.retry_count}
date_generated: "{record.created_at}"
evaluator_approval: "All 12 mandatory checkpoints passed"
---

"""
            with open(docs_lesson_path, "w", encoding="utf-8") as f:
                f.write(header_metadata + latest_lesson_text)
            SystemLogger.success(f"Final approved lesson saved to: {docs_lesson_path}")

        return {
            "report_path": str(report_path),
            "rejection_log_path": str(rejection_log_path),
            "lesson_path": str(lesson_path),
            "docs_lesson_path": str(docs_lesson_path) if record.status == RunDecision.APPROVED else None
        }

    def _build_rejection_log(self, record: RunRecord) -> str:
        """Constructs an exhaustive audit log of every attempt, failure, and revision."""
        lines = [
            f"# Rejection and Revision Audit Log: Run `{record.run_id}`",
            f"- **Topic:** {record.topic}",
            f"- **Generated At:** {record.created_at}",
            f"- **Final Decision:** `{record.status.value}`",
            f"- **Total Versions Generated:** {record.total_versions}",
            f"- **Retries Exhausted:** {record.retry_count}\n",
            "---",
            "## Version History and Evaluation Details\n"
        ]

        for v in record.versions:
            lines.append(f"### Version {v.version_number}")
            lines.append(f"- **Generated At:** {v.generated_at}")
            if v.changes_from_previous:
                lines.append(f"- **Changes from Previous:** {v.changes_from_previous}")

            if v.evaluation:
                eval_status = v.evaluation.overall_decision.value
                lines.append(f"- **Evaluation Result:** `{eval_status}` ({v.evaluation.passed_checkpoints}/{v.evaluation.total_checkpoints} passed)")
                lines.append(f"- **Summary:** {v.evaluation.evaluation_summary}\n")

                failed_cps = [cp for cp in v.evaluation.checkpoints if cp.result.value == "FAIL"]
                if failed_cps:
                    lines.append("#### Failed Checkpoints (Triggered Rejection/Revision):")
                    for cp in failed_cps:
                        lines.append(f"- **[{cp.checkpoint_id}] {cp.dimension}**")
                        lines.append(f"  - *Reason:* {cp.failure_reason}")
                        lines.append(f"  - *Evidence:* `{cp.evidence}`")
                else:
                    lines.append("#### Checkpoint Results:\nAll 12 checkpoints PASSED with full compliance.")
            else:
                lines.append("- *Evaluation not completed for this version.*")

            lines.append("\n---\n")

        return "\n".join(lines)
