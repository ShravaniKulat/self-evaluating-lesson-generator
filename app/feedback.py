"""
Feedback Builder.
Analyzes failed checkpoints from an EvaluationReport and compiles precise,
actionable instructions for the Lesson Generator to revise the lesson.
"""
import difflib
from typing import List, Tuple
from app.models import EvaluationReport, PassFailResult, CheckpointResult


class FeedbackBuilder:
    @staticmethod
    def build_feedback(report: EvaluationReport) -> str:
        """
        Extracts all failed checkpoints and composes structured, prioritized instructions.
        """
        failed_checkpoints: List[CheckpointResult] = [
            cp for cp in report.checkpoints if cp.result == PassFailResult.FAIL
        ]

        if not failed_checkpoints:
            return "No failed checkpoints found. The lesson meets all mandatory criteria."

        feedback_sections = []
        feedback_sections.append(f"### Rejection Summary: {len(failed_checkpoints)} Checkpoint(s) Failed")
        feedback_sections.append("The lesson cannot be approved until every one of the following items is corrected:\n")

        for idx, cp in enumerate(failed_checkpoints, 1):
            feedback_sections.append(
                f"{idx}. **Checkpoint [{cp.checkpoint_id}] - {cp.dimension}**\n"
                f"   - **Failure Reason:** {cp.failure_reason}\n"
                f"   - **Problematic Area / Evidence:** \"{cp.evidence}\"\n"
                f"   - **Action Required:** Make sure this requirement is explicitly and clearly fulfilled in the revised text.\n"
            )

        feedback_sections.append(
            "CRITICAL: Do not remove or weaken any previously passing sections. "
            "Focus specifically on repairing the flagged defects while preserving simplicity for a beginner."
        )

        return "\n".join(feedback_sections)

    @staticmethod
    def compute_diff_summary(previous_text: str, current_text: str) -> str:
        """
        Summarizes changes made between previous and current lesson versions.
        """
        prev_lines = previous_text.splitlines()
        curr_lines = current_text.splitlines()

        matcher = difflib.SequenceMatcher(None, prev_lines, curr_lines)
        added_lines = 0
        removed_lines = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                removed_lines += (i2 - i1)
                added_lines += (j2 - j1)
            elif tag == 'delete':
                removed_lines += (i2 - i1)
            elif tag == 'insert':
                added_lines += (j2 - j1)

        diff_summary = (
            f"Revision changes: {added_lines} lines added/modified, "
            f"{removed_lines} lines removed/modified across {len(curr_lines)} total lines."
        )
        return diff_summary
