"""
Pydantic data models for the lesson generator, rubric evaluator, and orchestrator.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PassFailResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class RunDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class CheckpointResult(BaseModel):
    checkpoint_id: str = Field(..., description="Unique identifier for the checkpoint, e.g. CHK_ACC_01")
    dimension: str = Field(..., description="Rubric dimension, e.g. Accuracy and Grounding")
    result: PassFailResult = Field(..., description="Explicit PASS or FAIL")
    evidence: str = Field(..., description="Verbatim evidence or specific excerpt from the lesson")
    failure_reason: Optional[str] = Field(None, description="Clear, actionable explanation if failed")


class EvaluationReport(BaseModel):
    overall_decision: PassFailResult = Field(..., description="PASS if all checkpoints pass, else FAIL")
    total_checkpoints: int = Field(..., description="Total number of evaluated checkpoints")
    passed_checkpoints: int = Field(..., description="Number of passed checkpoints")
    failed_checkpoints: int = Field(..., description="Number of failed checkpoints")
    evaluation_summary: str = Field(..., description="High-level evaluation narrative")
    checkpoints: List[CheckpointResult] = Field(default_factory=list, description="List of individual checkpoint results")

    def is_approved(self) -> bool:
        """Enforces hard approval rule: All mandatory checkpoints must pass."""
        return (
            self.overall_decision == PassFailResult.PASS
            and self.failed_checkpoints == 0
            and len(self.checkpoints) > 0
            and all(c.result == PassFailResult.PASS for c in self.checkpoints)
        )


class LessonVersion(BaseModel):
    version_number: int
    lesson_text: str
    generated_at: str
    prompt_used: Optional[str] = None
    evaluation: Optional[EvaluationReport] = None
    changes_from_previous: Optional[str] = None


class FailurePattern(BaseModel):
    pattern_id: str
    dimension: str
    issue: str
    guidance: str


class RunInsight(BaseModel):
    run_id: str
    timestamp: str
    topic: str
    failed_checkpoints: List[str]
    insight: str
    applied_correction: str


class RunRecord(BaseModel):
    run_id: str
    topic: str
    created_at: str
    status: RunDecision
    total_versions: int
    retry_count: int
    versions: List[LessonVersion] = Field(default_factory=list)
    failure_patterns_identified: List[str] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)
    error_details: Optional[str] = None
