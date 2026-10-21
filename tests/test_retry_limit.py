"""
Unit tests for retry limits and exhausted failure termination (Test C).
"""
from unittest.mock import MagicMock
from app.orchestrator import WorkflowOrchestrator
from app.generator import LessonGenerator
from app.evaluator import RubricEvaluator
from app.models import EvaluationReport, PassFailResult, CheckpointResult, RunDecision


def test_test_c_repeated_failure_exhausts_retries(temp_workspace):
    """
    Test C: Repeated failure.
    When all generated versions fail the rubric, the system must:
    - Stop after exactly two regeneration attempts (3 versions total: V1, V2, V3).
    - Set final decision to REJECTED.
    - Never enter an infinite loop.
    """
    memory = temp_workspace["memory"]
    output_mgr = temp_workspace["output_mgr"]

    # Mock generator returning failing lesson text repeatedly
    mock_generator = LessonGenerator(use_mock=True)
    mock_generator.generate_initial_lesson = MagicMock(return_value="Failing text v1")
    mock_generator.regenerate_lesson = MagicMock(side_effect=["Failing text v2", "Failing text v3"])

    # Failing evaluation report
    failing_report = EvaluationReport(
        overall_decision=PassFailResult.FAIL,
        total_checkpoints=12,
        passed_checkpoints=10,
        failed_checkpoints=2,
        evaluation_summary="Fails mandatory checkpoints",
        checkpoints=[
            CheckpointResult(
                checkpoint_id=f"CHK_{i}",
                dimension="Coverage of Key Points",
                result=PassFailResult.FAIL if i in (1, 2) else PassFailResult.PASS,
                evidence="Incomplete section",
                failure_reason="Missing key explanation" if i in (1, 2) else None
            )
            for i in range(1, 13)
        ]
    )

    mock_evaluator = RubricEvaluator(use_mock=True)
    mock_evaluator.evaluate = MagicMock(return_value=failing_report)

    orchestrator = WorkflowOrchestrator(
        generator=mock_generator,
        evaluator=mock_evaluator,
        memory=memory,
        output_manager=output_mgr,
        max_retries=2
    )

    record = orchestrator.run_pipeline(topic="Introduction to RAG")

    # Assertions
    assert record.status == RunDecision.REJECTED
    assert record.retry_count == 2
    assert record.total_versions == 3
    assert len(record.versions) == 3

    # Verify regenerate was called exactly twice
    assert mock_generator.regenerate_lesson.call_count == 2
