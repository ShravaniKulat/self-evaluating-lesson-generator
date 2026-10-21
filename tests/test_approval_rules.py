"""
Tests for Hard Approval Rules and preventing false approvals (Test D).
"""
from app.models import EvaluationReport, CheckpointResult, PassFailResult
from app.rubric import RUBRIC_CHECKPOINTS


def test_test_d_no_false_approval_single_failure():
    """
    Test D: No false approval.
    When 11 mandatory checkpoints PASS and exactly 1 checkpoint FAILS,
    the lesson MUST NOT be approved.
    """
    checkpoints = []
    for idx, cp in enumerate(RUBRIC_CHECKPOINTS):
        if idx == 0:
            # Inject single failure in CHK_ACC_01
            checkpoints.append(CheckpointResult(
                checkpoint_id=cp["id"],
                dimension=cp["dimension"],
                result=PassFailResult.FAIL,
                evidence="Unsupported claim detected in introduction.",
                failure_reason="Claim contradicts ground truth reference."
            ))
        else:
            checkpoints.append(CheckpointResult(
                checkpoint_id=cp["id"],
                dimension=cp["dimension"],
                result=PassFailResult.PASS,
                evidence=f"Valid evidence for {cp['title']}.",
                failure_reason=None
            ))

    report = EvaluationReport(
        overall_decision=PassFailResult.FAIL,
        total_checkpoints=12,
        passed_checkpoints=11,
        failed_checkpoints=1,
        evaluation_summary="11 checkpoints passed, 1 failed.",
        checkpoints=checkpoints
    )

    # Verify hard approval rule: is_approved() must strictly be False
    assert report.is_approved() is False
    assert report.overall_decision == PassFailResult.FAIL


def test_test_d_no_false_approval_even_if_overall_decision_claimed_pass():
    """
    Test D: Even if a malformed model output marks overall_decision as PASS
    while having 1 failed checkpoint, is_approved() enforces hard failure.
    """
    checkpoints = []
    for idx, cp in enumerate(RUBRIC_CHECKPOINTS):
        res = PassFailResult.FAIL if idx == 5 else PassFailResult.PASS
        checkpoints.append(CheckpointResult(
            checkpoint_id=cp["id"],
            dimension=cp["dimension"],
            result=res,
            evidence="Evidence excerpt",
            failure_reason="Missing element" if res == PassFailResult.FAIL else None
        ))

    report = EvaluationReport(
        overall_decision=PassFailResult.PASS,  # Erroneous optimistic claim
        total_checkpoints=12,
        passed_checkpoints=11,
        failed_checkpoints=1,
        evaluation_summary="Falsely claimed pass",
        checkpoints=checkpoints
    )

    # is_approved() must guard against this and return False
    assert report.is_approved() is False
