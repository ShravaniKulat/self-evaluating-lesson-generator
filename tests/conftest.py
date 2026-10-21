"""
Shared fixtures and test helpers.
"""
import pytest
from pathlib import Path
import tempfile
from app.models import EvaluationReport, PassFailResult, CheckpointResult
from app.memory import MemoryManager
from app.output import OutputManager
from app.generator import LessonGenerator
from app.evaluator import RubricEvaluator


import gc
import shutil

@pytest.fixture
def temp_workspace():
    """Provides temporary isolated directories for SQLite and JSON memory testing."""
    tmpdir = tempfile.mkdtemp()
    tmp_path = Path(tmpdir)
    db_path = tmp_path / "test_history.db"
    json_path = tmp_path / "test_memory.json"
    outputs_path = tmp_path / "outputs"
    docs_path = tmp_path / "docs"

    memory = MemoryManager(db_path=db_path, json_path=json_path)
    output_mgr = OutputManager(outputs_dir=outputs_path, docs_dir=docs_path)

    yield {
        "dir": tmp_path,
        "db_path": db_path,
        "json_path": json_path,
        "memory": memory,
        "output_mgr": output_mgr
    }

    # Teardown: force garbage collection to release open handles on Windows
    gc.collect()
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_passing_lesson():
    generator = LessonGenerator(use_mock=True)
    return generator._generate_engine_lesson("Introduction to RAG")


@pytest.fixture
def sample_failing_lesson():
    generator = LessonGenerator(use_mock=True)
    return generator._generate_lesson_with_unexplained_jargon("Introduction to RAG")


@pytest.fixture
def sample_fact_error_lesson():
    generator = LessonGenerator(use_mock=True)
    return generator._generate_lesson_with_factual_error("Introduction to RAG")
