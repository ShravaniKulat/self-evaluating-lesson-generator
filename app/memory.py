"""
Persistent Memory Manager.
Uses SQLite for persistent run history and structured JSON for reusable learning insights.
Survives application restarts and provides historical context to future runs.
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import SQLITE_DB_PATH, MEMORY_FILE
from app.models import (
    RunRecord, LessonVersion, EvaluationReport, CheckpointResult,
    PassFailResult, RunDecision
)


class MemoryManager:
    def __init__(self, db_path: Path = SQLITE_DB_PATH, json_path: Path = MEMORY_FILE):
        self.db_path = db_path
        self.json_path = json_path
        self._init_sqlite()
        self._init_json()

    def _init_sqlite(self):
        """Initializes SQLite tables for persistent run and version storage."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_versions INTEGER NOT NULL,
                    retry_count INTEGER NOT NULL,
                    error_details TEXT
                )
            """)
            # Lesson versions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lesson_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    lesson_text TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    changes_from_previous TEXT,
                    overall_decision TEXT,
                    passed_checkpoints INTEGER,
                    failed_checkpoints INTEGER,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
            """)
            # Checkpoint results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoint_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    result TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    failure_reason TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
            """)
            conn.commit()

    def _init_json(self):
        """Ensures the JSON memory file exists with valid structure."""
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.json_path.exists():
            initial_data = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "repeated_failure_patterns": [],
                "run_insights": []
            }
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    # --- SQLite Run Storage ---

    def save_run(self, record: RunRecord):
        """Persists a complete run, including all versions and evaluation checkpoints."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Insert or replace run
            cursor.execute("""
                INSERT OR REPLACE INTO runs 
                (run_id, topic, created_at, status, total_versions, retry_count, error_details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record.run_id,
                record.topic,
                record.created_at,
                record.status.value,
                record.total_versions,
                record.retry_count,
                record.error_details
            ))

            # Delete any prior versions for this run to avoid duplicates on update
            cursor.execute("DELETE FROM lesson_versions WHERE run_id = ?", (record.run_id,))
            cursor.execute("DELETE FROM checkpoint_evaluations WHERE run_id = ?", (record.run_id,))

            for v in record.versions:
                decision_val = v.evaluation.overall_decision.value if v.evaluation else None
                passed_val = v.evaluation.passed_checkpoints if v.evaluation else None
                failed_val = v.evaluation.failed_checkpoints if v.evaluation else None

                cursor.execute("""
                    INSERT INTO lesson_versions
                    (run_id, version_number, lesson_text, generated_at, changes_from_previous,
                     overall_decision, passed_checkpoints, failed_checkpoints)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.run_id,
                    v.version_number,
                    v.lesson_text,
                    v.generated_at,
                    v.changes_from_previous,
                    decision_val,
                    passed_val,
                    failed_val
                ))

                if v.evaluation and v.evaluation.checkpoints:
                    for cp in v.evaluation.checkpoints:
                        cursor.execute("""
                            INSERT INTO checkpoint_evaluations
                            (run_id, version_number, checkpoint_id, dimension, result, evidence, failure_reason)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record.run_id,
                            v.version_number,
                            cp.checkpoint_id,
                            cp.dimension,
                            cp.result.value,
                            cp.evidence,
                            cp.failure_reason
                        ))
            conn.commit()

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        """Loads a run record by ID from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
            run_row = cursor.fetchone()
            if not run_row:
                return None

            cursor.execute("SELECT * FROM lesson_versions WHERE run_id = ? ORDER BY version_number ASC", (run_id,))
            version_rows = cursor.fetchall()

            versions: List[LessonVersion] = []
            for v_row in version_rows:
                v_num = v_row["version_number"]
                cursor.execute("""
                    SELECT * FROM checkpoint_evaluations 
                    WHERE run_id = ? AND version_number = ?
                """, (run_id, v_num))
                cp_rows = cursor.fetchall()

                checkpoints = [
                    CheckpointResult(
                        checkpoint_id=cp["checkpoint_id"],
                        dimension=cp["dimension"],
                        result=PassFailResult(cp["result"]),
                        evidence=cp["evidence"],
                        failure_reason=cp["failure_reason"]
                    )
                    for cp in cp_rows
                ]

                evaluation = None
                if v_row["overall_decision"]:
                    evaluation = EvaluationReport(
                        overall_decision=PassFailResult(v_row["overall_decision"]),
                        total_checkpoints=len(checkpoints),
                        passed_checkpoints=v_row["passed_checkpoints"] or 0,
                        failed_checkpoints=v_row["failed_checkpoints"] or 0,
                        evaluation_summary=f"Stored evaluation for version {v_num}",
                        checkpoints=checkpoints
                    )

                versions.append(LessonVersion(
                    version_number=v_num,
                    lesson_text=v_row["lesson_text"],
                    generated_at=v_row["generated_at"],
                    changes_from_previous=v_row["changes_from_previous"],
                    evaluation=evaluation
                ))

            return RunRecord(
                run_id=run_row["run_id"],
                topic=run_row["topic"],
                created_at=run_row["created_at"],
                status=RunDecision(run_row["status"]),
                total_versions=run_row["total_versions"],
                retry_count=run_row["retry_count"],
                versions=versions,
                error_details=run_row["error_details"]
            )

    def list_runs(self) -> List[Dict[str, Any]]:
        """Lists metadata of all stored runs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT run_id, topic, created_at, status, total_versions, retry_count FROM runs ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    # --- JSON Reusable Insights Storage ---

    def load_json_memory(self) -> Dict[str, Any]:
        """Loads the JSON persistent memory."""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"repeated_failure_patterns": [], "run_insights": []}

    def save_json_memory(self, data: Dict[str, Any]):
        """Persists the JSON memory."""
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def record_run_insight(self, run_id: str, topic: str, failed_checkpoints: List[str], insight: str, correction: str):
        """Records a new learned insight from a run into JSON memory."""
        data = self.load_json_memory()
        insights = data.get("run_insights", [])
        insights.append({
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "topic": topic,
            "failed_checkpoints": failed_checkpoints,
            "insight": insight,
            "applied_correction": correction
        })
        data["run_insights"] = insights
        self.save_json_memory(data)

    def record_failure_pattern(self, pattern_id: str, dimension: str, issue: str, guidance: str):
        """Stores a general failure pattern and corrective guidance."""
        data = self.load_json_memory()
        patterns = data.get("repeated_failure_patterns", [])
        # Check if already exists
        existing = next((p for p in patterns if p.get("pattern_id") == pattern_id), None)
        if existing:
            existing["guidance"] = guidance
            existing["issue"] = issue
        else:
            patterns.append({
                "pattern_id": pattern_id,
                "dimension": dimension,
                "issue": issue,
                "guidance": guidance
            })
        data["repeated_failure_patterns"] = patterns
        self.save_json_memory(data)

    def get_prior_learnings_prompt_text(self) -> str:
        """Formats stored failure patterns and recent insights for LLM prompt injection."""
        data = self.load_json_memory()
        patterns = data.get("repeated_failure_patterns", [])
        insights = data.get("run_insights", [])

        if not patterns and not insights:
            return "No historical failures recorded yet. Follow the general guidelines strictly."

        lines = ["### Historical Pitfalls to Avoid:"]
        for p in patterns:
            lines.append(f"- **{p.get('dimension')}**: {p.get('issue')} → **Guidance:** {p.get('guidance')}")

        if insights:
            lines.append("\n### Key Insights from Recent Runs:")
            # Take last 3 insights
            for ins in insights[-3:]:
                lines.append(f"- From Run `{ins.get('run_id')}`: {ins.get('insight')} (Correction: {ins.get('applied_correction')})")

        return "\n".join(lines)
