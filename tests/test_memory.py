"""
Unit tests for Persistent Memory (SQLite and JSON) and reinitialization survival (Test E).
"""
from app.memory import MemoryManager
from app.models import (
    RunRecord, LessonVersion, EvaluationReport, CheckpointResult,
    PassFailResult, RunDecision
)


def test_test_e_persistent_memory_retrieval(temp_workspace):
    """
    Test E: Persistent Memory across application restarts.
    Saves a run and learning insights, re-instantiates MemoryManager,
    and verifies that all data is retrieved accurately.
    """
    memory_initial = temp_workspace["memory"]
    db_path = temp_workspace["db_path"]
    json_path = temp_workspace["json_path"]

    # 1. Create a sample run record
    cp1 = CheckpointResult(
        checkpoint_id="CHK_ACC_01",
        dimension="Accuracy and Grounding",
        result=PassFailResult.PASS,
        evidence="Clear RAG definition",
        failure_reason=None
    )
    eval_rep = EvaluationReport(
        overall_decision=PassFailResult.PASS,
        total_checkpoints=1,
        passed_checkpoints=1,
        failed_checkpoints=0,
        evaluation_summary="Passed checkpoint",
        checkpoints=[cp1]
    )
    v1 = LessonVersion(
        version_number=1,
        lesson_text="Introduction to RAG content...",
        generated_at="2026-10-21T12:00:00Z",
        changes_from_previous=None,
        evaluation=eval_rep
    )
    record = RunRecord(
        run_id="run_test_persistent_001",
        topic="Introduction to RAG (Retrieval-Augmented Generation)",
        created_at="2026-10-21T12:00:00Z",
        status=RunDecision.APPROVED,
        total_versions=1,
        retry_count=0,
        versions=[v1]
    )

    # Save run in SQLite
    memory_initial.save_run(record)

    # Save insight and failure pattern in JSON
    memory_initial.record_run_insight(
        run_id="run_test_persistent_001",
        topic=record.topic,
        failed_checkpoints=["CHK_JRG_01"],
        insight="Remember to define embedding before using it.",
        correction="Added embedding analogy to prompt."
    )
    memory_initial.record_failure_pattern(
        pattern_id="PAT_TEST",
        dimension="Clear Explanations Without Unexplained Jargon",
        issue="Technical jargon without prior definition",
        guidance="Define terms immediately upon introduction"
    )

    # 2. Simulate complete application restart by instantiating a brand-new MemoryManager
    memory_reloaded = MemoryManager(db_path=db_path, json_path=json_path)

    # 3. Verify SQLite persistence
    retrieved_run = memory_reloaded.get_run("run_test_persistent_001")
    assert retrieved_run is not None
    assert retrieved_run.run_id == "run_test_persistent_001"
    assert retrieved_run.topic == "Introduction to RAG (Retrieval-Augmented Generation)"
    assert retrieved_run.status == RunDecision.APPROVED
    assert retrieved_run.total_versions == 1
    assert len(retrieved_run.versions) == 1
    assert retrieved_run.versions[0].evaluation.passed_checkpoints == 1
    assert retrieved_run.versions[0].evaluation.checkpoints[0].checkpoint_id == "CHK_ACC_01"

    # 4. Verify JSON persistence
    json_data = memory_reloaded.load_json_memory()
    patterns = json_data.get("repeated_failure_patterns", [])
    insights = json_data.get("run_insights", [])

    assert any(p["pattern_id"] == "PAT_TEST" for p in patterns)
    assert any(i["run_id"] == "run_test_persistent_001" for i in insights)

    # 5. Verify prompt integration text
    prompt_text = memory_reloaded.get_prior_learnings_prompt_text()
    assert "PAT_TEST" in prompt_text or "Technical jargon without prior definition" in prompt_text
