"""
Unit tests for the Rubric and programmatic checkpoint checks.
"""
from app.rubric import RUBRIC_CHECKPOINTS, evaluate_lesson_programmatically
from app.models import PassFailResult


def test_rubric_structure():
    """Verify rubric has 12 distinct checkpoints across 6 dimensions."""
    assert len(RUBRIC_CHECKPOINTS) == 12
    dimensions = set(cp["dimension"] for cp in RUBRIC_CHECKPOINTS)
    assert len(dimensions) == 6
    assert "Accuracy and Grounding" in dimensions
    assert "Beginner-Friendly Language" in dimensions
    assert "Teaching Through Examples" in dimensions
    assert "Clear Explanations Without Unexplained Jargon" in dimensions
    assert "Coverage of Key Points" in dimensions
    assert "Coherent Teaching Flow" in dimensions


def test_rubric_evaluates_passing_lesson(sample_passing_lesson):
    """Test that a well-crafted lesson passes all 12 checkpoints."""
    report = evaluate_lesson_programmatically(sample_passing_lesson)
    assert report.total_checkpoints == 12
    assert report.passed_checkpoints == 12
    assert report.failed_checkpoints == 0
    assert report.overall_decision == PassFailResult.PASS
    assert report.is_approved() is True


def test_rubric_catches_jargon_failure(sample_failing_lesson):
    """Test that a jargon-heavy lesson fails the appropriate checkpoints."""
    report = evaluate_lesson_programmatically(sample_failing_lesson)
    assert report.failed_checkpoints > 0
    assert report.overall_decision == PassFailResult.FAIL
    assert report.is_approved() is False

    failed_ids = [cp.checkpoint_id for cp in report.checkpoints if cp.result == PassFailResult.FAIL]
    assert "CHK_LANG_01" in failed_ids or "CHK_JRG_01" in failed_ids
