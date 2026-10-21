"""
Unit tests for the Rubric Evaluator, response parsing, and error catching (Tests F & G).
"""
import pytest
from app.evaluator import RubricEvaluator
from app.models import PassFailResult


def test_test_g_invalid_evaluator_response_malformed_json():
    """Test G: Evaluator raises error on malformed JSON and never treats it as approval."""
    malformed_json = "{ 'overall_decision': 'PASS', not_valid_json: true }"
    with pytest.raises(ValueError, match="not valid JSON"):
        RubricEvaluator.validate_and_parse_evaluation(malformed_json)


def test_test_g_invalid_evaluator_response_missing_fields():
    """Test G: Evaluator raises error if mandatory report fields are missing."""
    incomplete_json = '{"overall_decision": "PASS"}'
    with pytest.raises(ValueError, match="missing required field"):
        RubricEvaluator.validate_and_parse_evaluation(incomplete_json)


def test_test_g_invalid_evaluator_response_insufficient_checkpoints():
    """Test G: Evaluator raises error if fewer than 12 checkpoints are returned."""
    partial_json = '''{
        "overall_decision": "PASS",
        "total_checkpoints": 1,
        "passed_checkpoints": 1,
        "failed_checkpoints": 0,
        "evaluation_summary": "Incomplete report",
        "checkpoints": [
            {
                "checkpoint_id": "CHK_ACC_01",
                "dimension": "Accuracy and Grounding",
                "result": "PASS",
                "evidence": "Good RAG definition",
                "failure_reason": null
            }
        ]
    }'''
    with pytest.raises(ValueError, match="Incomplete evaluation"):
        RubricEvaluator.validate_and_parse_evaluation(partial_json)


def test_test_f_deliberate_error_demonstration(sample_fact_error_lesson):
    """
    Test F: Deliberate error demonstration.
    Controlled error stating RAG retrains model weights dynamically must be caught by evaluator,
    flagged as CHK_ACC_01 failure, and prevented from approval.
    """
    evaluator = RubricEvaluator(use_mock=True)
    report = evaluator.evaluate(sample_fact_error_lesson)

    assert report.is_approved() is False
    assert report.overall_decision == PassFailResult.FAIL

    acc_cp = next((cp for cp in report.checkpoints if cp.checkpoint_id == "CHK_ACC_01"), None)
    assert acc_cp is not None
    assert acc_cp.result == PassFailResult.FAIL
    assert "retrain" in acc_cp.failure_reason.lower()
