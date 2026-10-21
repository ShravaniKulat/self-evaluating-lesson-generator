# Architecture Document: Self-Evaluating Lesson Content Generator

## 1. System Overview

The **Self-Evaluating Lesson Content Generator** is an autonomous agentic pipeline designed to produce high-quality, verified educational content tailored for beginners (specifically Indian Class 12 graduates with basic English vocabulary and no prior AI background).

Unlike naive generation scripts that output unverified text, this system enforces an autonomous **Generate → Evaluate → Regenerate → Ship** closed-loop feedback cycle with hard pass/fail checkpoints, strict retry termination, and persistent learning memory.

```mermaid
flowchart TD
    A[User Input: Topic] --> B[Input Handler & Config]
    B --> C[Memory Manager: Load Prior Insights]
    C --> D[Lesson Generator: Version 1]
    D --> E[Rubric Evaluator: 6 Dimensions / 12 Checkpoints]
    E --> F{All Checkpoints Passed?}
    F -- YES --> G[Final Decision: APPROVED]
    G --> H[Output Manager: Ship docs/final_lesson.md]
    G --> I[Save Run to SQLite & JSON Memory]
    F -- NO --> J{Retries < Max Retries (2)?}
    J -- YES --> K[Feedback Builder: Compile Actionable Fixes]
    K --> L[Memory: Log Failure Pattern]
    L --> M[Regenerate Revised Lesson: Version N+1]
    M --> E
    J -- NO --> N[Final Decision: REJECTED]
    N --> O[Save Rejection Audit Log & Terminal Record]
```

---

## 2. Component Breakdown & Responsibilities

| Component | Module | Key Responsibility |
| :--- | :--- | :--- |
| **Input Handler & Config** | `app/config.py`, `app/main.py` | Validates target topic, audience configuration, file paths, model API keys, and execution flags (`--mock`, `--demo-error`). |
| **Lesson Generator** | `app/generator.py` | Generates initial standalone lessons and targeted revisions. Injects ground-truth references (`data/references.md`) and prior failure learnings. Supports both live LLM APIs (OpenAI/compatible) and a deterministic internal pedagogical engine. |
| **Rubric Evaluator** | `app/evaluator.py`, `app/rubric.py` | Strictly audits lesson text against 12 checkpoints across 6 pedagogical dimensions. Returns structured `EvaluationReport` with verbatim evidence and actionable failure reasons. |
| **Feedback Builder** | `app/feedback.py` | Analyzes failed checkpoints, extracts actionable repair directives, and computes character/line diffs between successive versions. |
| **Workflow Orchestrator** | `app/orchestrator.py` | Coordinates the full autonomous loop: generation, evaluation, feedback dispatch, retry termination (max 2 retries = 3 versions max), and terminal outcome resolution (`APPROVED`, `REJECTED`, `ERROR`). |
| **Persistent Memory Manager** | `app/memory.py` | Manages two-tier persistent storage: SQLite (`data/history.db`) for run trajectories and checkpoint audits; structured JSON (`data/memory.json`) for reusable failure patterns and learning insights. |
| **Logging & Presentation** | `app/logger.py` | Renders terminal output with Rich tables, checkpoint statuses, colored progress steps, and decision banners with cross-platform Windows charmap safety. |
| **Output Manager** | `app/output.py` | Persists JSON run reports (`outputs/`), markdown rejection audit logs, and writes the official approved lesson to `docs/final_lesson.md`. |

---

## 3. The 6-Dimension Rubric Design

The system enforces a **hard approval gate**: there is zero partial credit. If 11 checkpoints pass and 1 fails, the lesson is rejected and must be regenerated.

1. **Accuracy and Grounding**
   - `CHK_ACC_01`: Grounded Definition of RAG (Retrieval + Augmentation + Generation; no false claims of weight retraining during query time).
   - `CHK_ACC_02`: Factual Problem Formulation (Correctly attributes knowledge cutoff / staleness and hallucinations).
2. **Beginner-Friendly Language**
   - `CHK_LANG_01`: Accessible Vocabulary (Avoids academic or obscure terminology; tailored for Indian Class 12).
   - `CHK_LANG_02`: Digestible Sentence Structure (Sentences under 32 words; no tangled subordinate clauses).
3. **Teaching Through Examples**
   - `CHK_EXM_01`: Relatable Core Analogy (Open-book exam vs closed-book exam).
   - `CHK_EXM_02`: Analogy-to-System Mapping (Explicit 1-to-1 mapping of analogy parts to retriever, vector store, and generator).
4. **Clear Explanations Without Unexplained Jargon**
   - `CHK_JRG_01`: Jargon Definition Precedence (Terms like LLM, Chunking, Embedding, Vector DB defined before use).
   - `CHK_JRG_02`: Intuitive Concept Explanation (Embeddings explained intuitively as meaning codes / number tags).
5. **Coverage of Key Points**
   - `CHK_COV_01`: Essential Pillars Covered (What, Why, Analogy, How, Key terms glossary, Summary).
   - `CHK_COV_02`: Complete Step-by-Step Pipeline (Documents, Chunking, Embeddings, Vector Database, Prompt Augmentation, Generation).
6. **Coherent Teaching Flow**
   - `CHK_FLW_01`: Standalone Completeness (Self-contained; no external links or books required).
   - `CHK_FLW_02`: Logical Progression (Hook/Problem → Concept → Analogy → Mechanics → Summary).

---

## 4. Key Architectural Decisions

### 1. Separation of Generation and Evaluation
A generator prompted to write content cannot objectively critique its own blind spots. Separating the Evaluator into an isolated module with its own prompt, ground-truth reference document (`data/references.md`), and strict validation schema prevents confirmation bias.

### 2. Hard Pass/Fail Gates (No Soft Scores)
Averaging numeric scores (e.g., "7.8/10") creates a dangerous false impression: a lesson could receive 80% while containing a critical factual error or confusing jargon. Hard binary gates ensure that every mandatory pedagogical requirement is verified before shipping.

### 3. Bounded Retry Policy
To prevent runaway API costs and infinite loops, the orchestrator enforces an immutable limit of 2 retries (maximum 3 generated versions: V1, V2, V3). If Version 3 fails, the pipeline transitions to `REJECTED`.

### 4. Hybrid Persistent Memory
- **SQLite (`data/history.db`):** Relational, queryable run tracking, storing timestamps, versions, checkpoint results, and diffs.
- **JSON (`data/memory.json`):** Human-inspectable, lightweight store for recurring failure patterns and learning insights injected into prompts for future runs.
