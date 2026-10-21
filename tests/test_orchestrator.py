"""
Unit tests for the Workflow Orchestrator (Tests A & B).
"""
from unittest.mock import MagicMock
from app.orchestrator import WorkflowOrchestrator
from app.generator import LessonGenerator
from app.evaluator import RubricEvaluator
from app.models import (
    EvaluationReport, PassFailResult, CheckpointResult, RunDecision
)
from app.rubric import RUBRIC_CHECKPOINTS


def make_eval_report(is_pass: bool, failed_ids=None) -> EvaluationReport:
    failed_ids = failed_ids or []
    checkpoints = []
    for cp in RUBRIC_CHECKPOINTS:
        res = PassFailResult.FAIL if cp["id"] in failed_ids else PassFailResult.PASS
        checkpoints.append(CheckpointResult(
            checkpoint_id=cp["id"],
            dimension=cp["dimension"],
            result=res,
            evidence="Evidence excerpt",
            failure_reason="Failed item" if res == PassFailResult.FAIL else None
        ))
    passed_count = sum(1 for c in checkpoints if c.result == PassFailResult.PASS)
    failed_count = sum(1 for c in checkpoints if c.result == PassFailResult.FAIL)
    return EvaluationReport(
        overall_decision=PassFailResult.PASS if failed_count == 0 else PassFailResult.FAIL,
        total_checkpoints=len(checkpoints),
        passed_checkpoints=passed_count,
        failed_checkpoints=failed_count,
        evaluation_summary="Mock evaluation",
        checkpoints=checkpoints
    )


def test_test_a_successful_first_attempt(temp_workspace):
    """
    Test A: Successful first attempt.
    The first lesson passes every checkpoint.
    Expected: APPROVED, retry_count=0, total_versions=1.
    """
    memory = temp_workspace["memory"]
    output_mgr = temp_workspace["output_mgr"]

    mock_generator = LessonGenerator(use_mock=True)
    passing_report = make_eval_report(is_pass=True)

    mock_evaluator = RubricEvaluator(use_mock=True)
    mock_evaluator.evaluate = MagicMock(return_value=passing_report)

    orchestrator = WorkflowOrchestrator(
        generator=mock_generator,
        evaluator=mock_evaluator,
        memory=memory,
        output_manager=output_mgr,
        max_retries=2
    )

    record = orchestrator.run_pipeline(topic="Introduction to RAG")

    assert record.status == RunDecision.APPROVED
    assert record.retry_count == 0
    assert record.total_versions == 1
    assert len(record.versions) == 1
    assert record.versions[0].evaluation.is_approved() is True


def test_test_b_successful_regeneration(temp_workspace):
    """
    Test B: Successful regeneration.
    The first lesson fails at least one checkpoint. The revised lesson passes.
    Expected: Failure logged, regeneration occurs, final result is APPROVED.
    """
    memory = temp_workspace["memory"]
    output_mgr = temp_workspace["output_mgr"]

    mock_generator = LessonGenerator(use_mock=True)
    mock_generator.generate_initial_lesson = MagicMock(return_value="Initial draft with flaws")
    mock_generator.regenerate_lesson = MagicMock(return_value="Revised perfect lesson")

    # First evaluation fails on CHK_JRG_01
    failing_report = make_eval_report(is_pass=False, failed_ids=["CHK_JRG_01"])
    # Second evaluation passes all
    passing_report = make_eval_report(is_pass=True)

    mock_evaluator = RubricEvaluator(use_mock=True)
    mock_evaluator.evaluate = MagicMock(side_effect=[failing_report, passing_report])

    orchestrator = WorkflowOrchestrator(
        generator=mock_generator,
        evaluator=mock_evaluator,
        memory=memory,
        output_manager=output_mgr,
        max_retries=2
    )

    record = orchestrator.run_pipeline(topic="Introduction to RAG")

    assert record.status == RunDecision.APPROVED
    assert record.retry_count == 1
    assert record.total_versions == 2
    assert len(record.versions) == 2
    # Verify version 1 failed and version 2 passed
    assert record.versions[0].evaluation.is_approved() is False
    assert record.versions[1].evaluation.is_approved() is True
    # Verify diff was recorded
    assert record.versions[1].changes_from_previous is not None
