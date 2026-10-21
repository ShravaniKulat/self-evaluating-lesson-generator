"""
Rubric Evaluator Module.
Evaluates generated lessons against the hard pass/fail rubric across 6 dimensions.
Enforces strict validation: malformed or incomplete outputs are never treated as approvals.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from app.config import (
    EVALUATION_PROMPT_FILE, REFERENCES_FILE, OPENAI_API_KEY,
    OPENAI_BASE_URL, DEFAULT_MODEL
)
from app.models import EvaluationReport, PassFailResult, CheckpointResult
from app.rubric import evaluate_lesson_programmatically, RUBRIC_CHECKPOINTS
from app.logger import SystemLogger


class RubricEvaluator:
    def __init__(self, model_name: str = DEFAULT_MODEL, use_mock: bool = False):
        self.model_name = model_name
        self.use_mock = use_mock or not bool(OPENAI_API_KEY)
        self.references_text = self._load_file(REFERENCES_FILE)
        self.eval_prompt_template = self._load_file(EVALUATION_PROMPT_FILE)

        self.client = None
        if not self.use_mock and OPENAI_API_KEY:
            try:
                from openai import OpenAI
                kwargs = {"api_key": OPENAI_API_KEY}
                if OPENAI_BASE_URL:
                    kwargs["base_url"] = OPENAI_BASE_URL
                self.client = OpenAI(**kwargs)
            except Exception as e:
                SystemLogger.warning(f"Could not initialize OpenAI evaluator client ({e}). Using programmatic validator.")
                self.use_mock = True

    def _load_file(self, path: Path) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            SystemLogger.error(f"Error loading {path}: {e}")
            return ""

    def evaluate(self, lesson_text: str) -> EvaluationReport:
        """
        Evaluates a lesson against the 6 dimensions / 12 checkpoints.
        Validates output structure strictly; malformed outputs result in rejection.
        """
        if not self.use_mock and self.client:
            try:
                return self._evaluate_with_llm(lesson_text)
            except Exception as e:
                SystemLogger.warning(f"LLM evaluation failed or produced invalid format ({e}). Falling back to programmatic evaluator.")
                return evaluate_lesson_programmatically(lesson_text)
        else:
            return evaluate_lesson_programmatically(lesson_text)

    def _evaluate_with_llm(self, lesson_text: str) -> EvaluationReport:
        """Invokes LLM with strict JSON formatting and parses result into EvaluationReport."""
        prompt = self.eval_prompt_template.format(
            references=self.references_text,
            lesson_text=lesson_text
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict, impartial educational quality auditor. Output ONLY valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        raw_content = response.choices[0].message.content
        return self.validate_and_parse_evaluation(raw_content)

    @staticmethod
    def validate_and_parse_evaluation(raw_json_str: str) -> EvaluationReport:
        """
        Strictly parses and validates JSON string into EvaluationReport.
        Rejects malformed, incomplete, or corrupted outputs.
        """
        try:
            data = json.loads(raw_json_str)
        except json.JSONDecodeError as err:
            raise ValueError(f"Evaluator output is not valid JSON: {err}")

        # Validate required fields
        required_keys = ["overall_decision", "total_checkpoints", "passed_checkpoints", "failed_checkpoints", "checkpoints"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Malformed evaluator output: missing required field '{key}'")

        # Parse using Pydantic model
        report = EvaluationReport(**data)

        # Enforce consistency: overall_decision must be FAIL if any checkpoint failed
        if report.failed_checkpoints > 0 and report.overall_decision == PassFailResult.PASS:
            report.overall_decision = PassFailResult.FAIL

        # Verify all checkpoints from rubric are evaluated
        if len(report.checkpoints) < len(RUBRIC_CHECKPOINTS):
            raise ValueError(
                f"Incomplete evaluation: Expected {len(RUBRIC_CHECKPOINTS)} checkpoints, but received {len(report.checkpoints)}"
            )

        return report
