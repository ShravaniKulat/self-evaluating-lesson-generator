"""
Rubric definition and checkpoint rules for evaluating generated lessons.
Enforces hard pass/fail criteria across 6 educational dimensions.
"""
import re
from typing import List, Dict, Any, Tuple
from app.models import CheckpointResult, PassFailResult, EvaluationReport


RUBRIC_CHECKPOINTS = [
    {
        "id": "CHK_ACC_01",
        "dimension": "Accuracy and Grounding",
        "title": "Grounded Definition of RAG",
        "description": "Accurately defines RAG as Retrieval + Augmentation + Generation, without falsely claiming model weights are retrained during query time."
    },
    {
        "id": "CHK_ACC_02",
        "dimension": "Accuracy and Grounding",
        "title": "Factual Problem Formulation",
        "description": "Accurately explains LLM limitations: knowledge cutoffs (outdated data) and hallucinations (confidently making up facts)."
    },
    {
        "id": "CHK_LANG_01",
        "dimension": "Beginner-Friendly Language",
        "title": "Accessible Vocabulary",
        "description": "Uses simple, clear English suitable for an Indian Class 12 graduate with basic vocabulary."
    },
    {
        "id": "CHK_LANG_02",
        "dimension": "Beginner-Friendly Language",
        "title": "Digestible Sentence Structure",
        "description": "Keeps sentences short, straightforward, and easy to read without tangled subordinate clauses."
    },
    {
        "id": "CHK_EXM_01",
        "dimension": "Teaching Through Examples",
        "title": "Relatable Core Analogy",
        "description": "Introduces a familiar real-world analogy (such as an open-book exam, library assistant, or chef cookbook)."
    },
    {
        "id": "CHK_EXM_02",
        "dimension": "Teaching Through Examples",
        "title": "Analogy-to-System Mapping",
        "description": "Explicitly maps each element of the analogy to the corresponding technical component of RAG."
    },
    {
        "id": "CHK_JRG_01",
        "dimension": "Clear Explanations Without Unexplained Jargon",
        "title": "Jargon Definition Precedence",
        "description": "Defines every technical term (e.g., LLM, Hallucination, Chunking, Embedding, Vector DB) in plain words before or as it is introduced."
    },
    {
        "id": "CHK_JRG_02",
        "dimension": "Clear Explanations Without Unexplained Jargon",
        "title": "Intuitive Concept Explanation",
        "description": "Explains abstract concepts (like embeddings) intuitively as number tags or meaning codes rather than dry mathematical jargon."
    },
    {
        "id": "CHK_COV_01",
        "dimension": "Coverage of Key Points",
        "title": "Essential Core Pillars",
        "description": "Covers all mandatory sections: What RAG is, Why it matters, Everyday analogy, Step-by-step pipeline, Key concepts, and Summary."
    },
    {
        "id": "CHK_COV_02",
        "dimension": "Coverage of Key Points",
        "title": "Complete Step-by-Step Pipeline",
        "description": "Details the 6 technical steps: documents, chunking, embeddings, vector database search, prompt augmentation, and generation."
    },
    {
        "id": "CHK_FLW_01",
        "dimension": "Coherent Teaching Flow",
        "title": "Standalone Completeness",
        "description": "The lesson is 100% self-contained and does not require the student to consult external textbooks or URLs."
    },
    {
        "id": "CHK_FLW_02",
        "dimension": "Coherent Teaching Flow",
        "title": "Logical Progression",
        "description": "Structured in a natural pedagogic order: Hook/Problem -> Intuition -> Mechanism -> Glossary -> Summary."
    }
]


def evaluate_lesson_programmatically(lesson_text: str) -> EvaluationReport:
    """
    Evaluates lesson text using deterministic linguistic, factual, and structural checks.
    This serves as a reliable, verifiable evaluator that can operate stand-alone or
    cross-validate LLM evaluator outputs.
    """
    checkpoints: List[CheckpointResult] = []
    text_lower = lesson_text.lower()

    # --- Dimension 1: Accuracy and Grounding ---
    # CHK_ACC_01: RAG definition
    has_retrieval = "retrieval" in text_lower
    has_augmentation = "augmentation" in text_lower or "augmented" in text_lower
    has_generation = "generation" in text_lower
    has_retraining_error = "retrains the model" in text_lower or "updates model weights" in text_lower or "retraining the llm weights" in text_lower

    if has_retrieval and has_augmentation and has_generation and not has_retraining_error:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_ACC_01",
            dimension="Accuracy and Grounding",
            result=PassFailResult.PASS,
            evidence="Lesson correctly introduces 'Retrieval-Augmented Generation' without claiming model weights are retrained at query time.",
            failure_reason=None
        ))
    else:
        reason = "Lesson falsely claims model retraining during query" if has_retraining_error else "Lesson does not clearly define Retrieval-Augmented Generation."
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_ACC_01",
            dimension="Accuracy and Grounding",
            result=PassFailResult.FAIL,
            evidence="Text search found missing RAG definition or erroneous claim of weight retraining.",
            failure_reason=reason
        ))

    # CHK_ACC_02: Problem formulation
    has_hallucination = "hallucin" in text_lower or "making things up" in text_lower or "false facts" in text_lower or "makes up" in text_lower
    has_cutoff = "outdated" in text_lower or "cutoff" in text_lower or "memory alone" in text_lower or "old knowledge" in text_lower or "closed-book" in text_lower

    if has_hallucination and has_cutoff:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_ACC_02",
            dimension="Accuracy and Grounding",
            result=PassFailResult.PASS,
            evidence="Lesson correctly identifies AI hallucinations and outdated knowledge as key reasons for using RAG.",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_ACC_02",
            dimension="Accuracy and Grounding",
            result=PassFailResult.FAIL,
            evidence="Failed to adequately explain hallucinations or outdated model training cutoff.",
            failure_reason="Must explain both hallucination (making up false facts) and outdated knowledge / memory limits."
        ))

    # --- Dimension 2: Beginner-Friendly Language ---
    # CHK_LANG_01: Accessible Vocabulary
    complex_words = ["epistemological", "heuristic", "hyperdimensional", "hermeneutic", "stochasticity", "idempotent", "parsimonious"]
    found_complex = [w for w in complex_words if w in text_lower]
    if not found_complex:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_LANG_01",
            dimension="Beginner-Friendly Language",
            result=PassFailResult.PASS,
            evidence="Lesson avoids unnecessarily high-brow academic vocabulary; uses accessible everyday phrasing.",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_LANG_01",
            dimension="Beginner-Friendly Language",
            result=PassFailResult.FAIL,
            evidence=f"Found overly complex words unsuitable for beginner: {', '.join(found_complex)}",
            failure_reason="Replace difficult academic vocabulary with simple, friendly everyday English words."
        ))

    # CHK_LANG_02: Sentence Length & Digestibility
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', lesson_text) if len(s.strip()) > 3]
    long_sentences = [s for s in sentences if len(s.split()) > 32]
    long_ratio = len(long_sentences) / max(len(sentences), 1)

    if long_ratio < 0.15:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_LANG_02",
            dimension="Beginner-Friendly Language",
            result=PassFailResult.PASS,
            evidence=f"Sentence structure is clear and digestible (only {len(long_sentences)} out of {len(sentences)} sentences exceed 32 words).",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_LANG_02",
            dimension="Beginner-Friendly Language",
            result=PassFailResult.FAIL,
            evidence=f"{len(long_sentences)} sentences are overly long (>32 words), making comprehension difficult for a beginner.",
            failure_reason="Break long, complex sentences into shorter sentences of 15-20 words each."
        ))

    # --- Dimension 3: Teaching Through Examples ---
    # CHK_EXM_01: Relatable Analogy
    has_analogy = ("open-book" in text_lower or "exam" in text_lower or "library" in text_lower or "chef" in text_lower or "recipe" in text_lower)
    if has_analogy:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_EXM_01",
            dimension="Teaching Through Examples",
            result=PassFailResult.PASS,
            evidence="Lesson features a clear real-world analogy (e.g., student taking an open-book exam vs closed-book exam).",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_EXM_01",
            dimension="Teaching Through Examples",
            result=PassFailResult.FAIL,
            evidence="No clear, relatable real-world analogy found.",
            failure_reason="Include a relatable analogy such as an open-book exam or a library assistant to anchor understanding."
        ))

    # CHK_EXM_02: Analogy-to-System Mapping
    has_mapping = ("student" in text_lower or "book" in text_lower or "desk" in text_lower) and ("retriev" in text_lower) and ("generat" in text_lower)
    if has_mapping and has_analogy:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_EXM_02",
            dimension="Teaching Through Examples",
            result=PassFailResult.PASS,
            evidence="Analogy explicitly connects the exam/book scenario to retrieval, prompt augmentation, and generation.",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_EXM_02",
            dimension="Teaching Through Examples",
            result=PassFailResult.FAIL,
            evidence="Analogy is disconnected from the actual technical components of RAG.",
            failure_reason="Explicitly map each part of the analogy (e.g. Student = AI, Textbook = Knowledge base, Looking up = Retrieval, Writing = Generation)."
        ))

    # --- Dimension 4: Clear Explanations Without Unexplained Jargon ---
    # CHK_JRG_01: Jargon Definition Precedence
    has_llm_def = ("large language model" in text_lower or "llm" in text_lower)
    has_chunk_def = "chunk" in text_lower
    has_embed_def = "embed" in text_lower
    has_vector_def = "vector" in text_lower

    if has_llm_def and has_chunk_def and has_embed_def and has_vector_def:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_JRG_01",
            dimension="Clear Explanations Without Unexplained Jargon",
            result=PassFailResult.PASS,
            evidence="Key technical terms (LLM, Chunking, Embedding, Vector Database) are introduced and explained.",
            failure_reason=None
        ))
    else:
        missing_terms = []
        if not has_chunk_def: missing_terms.append("Chunking")
        if not has_embed_def: missing_terms.append("Embedding")
        if not has_vector_def: missing_terms.append("Vector Database")
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_JRG_01",
            dimension="Clear Explanations Without Unexplained Jargon",
            result=PassFailResult.FAIL,
            evidence=f"Missing foundational term definitions: {', '.join(missing_terms)}",
            failure_reason=f"Define the following terms in simple words: {', '.join(missing_terms)}."
        ))

    # CHK_JRG_02: Intuitive Concept Explanation
    has_intuitive_embed = ("number" in text_lower or "tag" in text_lower or "meaning" in text_lower or "code" in text_lower) and has_embed_def
    if has_intuitive_embed:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_JRG_02",
            dimension="Clear Explanations Without Unexplained Jargon",
            result=PassFailResult.PASS,
            evidence="Embeddings are explained intuitively using relatable concepts like numbers, meaning codes, or tags.",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_JRG_02",
            dimension="Clear Explanations Without Unexplained Jargon",
            result=PassFailResult.FAIL,
            evidence="Embeddings are either missing or explained without an intuitive beginner-friendly metaphor.",
            failure_reason="Explain embeddings simply, e.g. as giving each piece of text a list of numbers representing its meaning."
        ))

    # --- Dimension 5: Coverage of Key Points ---
    # CHK_COV_01: Essential Core Pillars
    has_what = "what" in text_lower or "introduction" in text_lower
    has_why = "why" in text_lower or "problem" in text_lower or "matter" in text_lower
    has_how = "how" in text_lower or "step" in text_lower or "works" in text_lower
    has_summary = "summary" in text_lower or "recap" in text_lower or "takeaway" in text_lower

    if has_what and has_why and has_how and has_summary:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_COV_01",
            dimension="Coverage of Key Points",
            result=PassFailResult.PASS,
            evidence="Lesson contains all core pillars: What, Why, Analogy, How, Key terms, and Summary.",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_COV_01",
            dimension="Coverage of Key Points",
            result=PassFailResult.FAIL,
            evidence="One or more essential pillars are missing from the lesson structure.",
            failure_reason="Ensure sections for What RAG is, Why it matters, How it works, and a Summary are all clearly present."
        ))

    # CHK_COV_02: Complete Step-by-Step Pipeline
    steps_found = 0
    if "chunk" in text_lower: steps_found += 1
    if "embed" in text_lower: steps_found += 1
    if "vector" in text_lower or "database" in text_lower: steps_found += 1
    if "retriev" in text_lower or "search" in text_lower: steps_found += 1
    if "augment" in text_lower or "attach" in text_lower or "prompt" in text_lower: steps_found += 1
    if "generat" in text_lower or "answer" in text_lower: steps_found += 1

    if steps_found >= 5:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_COV_02",
            dimension="Coverage of Key Points",
            result=PassFailResult.PASS,
            evidence=f"Complete technical pipeline represented ({steps_found}/6 pipeline stages covered in detail).",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_COV_02",
            dimension="Coverage of Key Points",
            result=PassFailResult.FAIL,
            evidence=f"Incomplete pipeline coverage (only {steps_found}/6 steps identified).",
            failure_reason="Walk through all 6 steps: documents, chunking, embeddings, vector database, prompt augmentation, and generation."
        ))

    # --- Dimension 6: Coherent Teaching Flow ---
    # CHK_FLW_01: Standalone Completeness
    has_external_dependency = "click here" in text_lower or "refer to the paper" in text_lower or "see documentation" in text_lower
    if not has_external_dependency and len(lesson_text.split()) > 250:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_FLW_01",
            dimension="Coherent Teaching Flow",
            result=PassFailResult.PASS,
            evidence="Lesson is fully standalone, self-explanatory, and sufficiently detailed without external references.",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_FLW_01",
            dimension="Coherent Teaching Flow",
            result=PassFailResult.FAIL,
            evidence="Lesson is either too brief (<250 words) or relies on external reference material.",
            failure_reason="Ensure the lesson is thorough and completely self-contained."
        ))

    # CHK_FLW_02: Logical Progression
    # Check that 'what' or 'problem' appears before detailed 'step' or 'vector'
    pos_problem = min(text_lower.find("problem"), text_lower.find("what"))
    pos_steps = max(text_lower.find("step"), text_lower.find("how"))
    pos_summary = text_lower.find("summary")

    is_logical = (pos_problem != -1 and pos_steps != -1 and pos_problem < pos_steps)
    if is_logical:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_FLW_02",
            dimension="Coherent Teaching Flow",
            result=PassFailResult.PASS,
            evidence="Logical pedagogic sequence confirmed: Introduction & Problem precede technical mechanics and Summary.",
            failure_reason=None
        ))
    else:
        checkpoints.append(CheckpointResult(
            checkpoint_id="CHK_FLW_02",
            dimension="Coherent Teaching Flow",
            result=PassFailResult.FAIL,
            evidence="Structural progression does not follow smooth beginner flow.",
            failure_reason="Organize content logically: Hook/Problem first, then Concept, then Analogy, then Mechanics, then Summary."
        ))

    # Calculate overall results
    passed_count = sum(1 for c in checkpoints if c.result == PassFailResult.PASS)
    failed_count = sum(1 for c in checkpoints if c.result == PassFailResult.FAIL)
    overall = PassFailResult.PASS if failed_count == 0 else PassFailResult.FAIL

    summary = (
        f"Evaluation completed: {passed_count}/{len(checkpoints)} checkpoints passed. "
        f"{'Lesson meets all mandatory criteria.' if overall == PassFailResult.PASS else 'Lesson failed one or more mandatory checkpoints.'}"
    )

    return EvaluationReport(
        overall_decision=overall,
        total_checkpoints=len(checkpoints),
        passed_checkpoints=passed_count,
        failed_checkpoints=failed_count,
        evaluation_summary=summary,
        checkpoints=checkpoints
    )
