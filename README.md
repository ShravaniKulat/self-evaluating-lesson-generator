# Self-Evaluating Lesson Content Generator

> **GenAI Engineer – Content Systems Take-Home Assessment**  
> **Topic:** Introduction to RAG (Retrieval-Augmented Generation)  
> **Audience:** Indian High School Graduates (Class 12) with limited English vocabulary and zero prior AI knowledge.

---

## 1. Project Overview & Assessment Objective

The **Self-Evaluating Lesson Content Generator** is an autonomous agentic system engineered to produce, evaluate, revise, and verify beginner-friendly educational lessons. 

Unlike standard text-generation scripts that blindly output whatever an LLM returns, this system implements an autonomous **quality-control loop**:
- Generates a standalone, beginner-friendly lesson on RAG.
- Audits the lesson against a rigorous **12-checkpoint pass/fail rubric** across 6 pedagogical dimensions.
- Automatically compiles actionable feedback and regenerates flawed drafts when any check fails.
- Enforces an immutable retry limit (maximum 2 retries = 3 versions total).
- Ships the lesson to `docs/final_lesson.md` **only when all 12 checkpoints pass**.
- Persists run history, trajectory diffs, and reusable failure patterns across runs using SQLite and JSON.

---

## 2. Key Features

- **Autonomous Closed-Loop Quality Control:** Generate → Evaluate → Feedback → Regenerate → Final Decision.
- **Strict Hard Approval Gate:** Zero partial credit. If 11 checkpoints pass and 1 fails, the lesson is rejected and revised.
- **6-Dimension Rubric:** Accuracy & Grounding, Beginner-Friendly Language, Teaching Through Examples, No Unexplained Jargon, Coverage of Key Points, and Coherent Flow.
- **Dual-Tier Persistent Memory:**
  - **SQLite Database (`data/history.db`):** Permanent storage for runs, versions, checkpoint results, and trajectories.
  - **JSON Memory (`data/memory.json`):** Human-readable store for recurring failure patterns and learned insights that feed forward into future generations.
- **Dual-Mode Execution:** Full support for real LLM APIs (`gpt-4o-mini`, custom OpenAI-compatible endpoints) and a deterministic internal pedagogical engine for offline testing and evaluation.
- **Deliberate Error Demonstration:** CLI flags to inject controlled factual or jargon flaws to demonstrate error catching, rejection, and recovery.
- **Audit Trails & Diffs:** Saves comprehensive JSON run reports and markdown rejection/revision logs in `outputs/`.

---

## 3. Technology Stack

- **Language:** Python 3.13+
- **Data Validation & Schemas:** Pydantic v2
- **Terminal Presentation & Formatting:** Rich (with Windows charmap safety)
- **Database & Storage:** SQLite3 (built-in) + JSON
- **Testing Framework:** Pytest
- **Model SDK:** OpenAI Python SDK (compatible with OpenAI, Groq, Ollama, OpenRouter, Azure)
- **Environment Management:** python-dotenv

---

## 4. Project Structure

```
Self_Evaluating_Lesson Generator/
├── app/
│   ├── __init__.py           # Package initializer
│   ├── config.py             # System paths, audience settings, and defaults
│   ├── models.py             # Pydantic data models (EvaluationReport, CheckpointResult, RunRecord)
│   ├── rubric.py             # 12 checkpoints definition and programmatic validator
│   ├── generator.py          # Lesson generator (LLM API + internal pedagogical engine)
│   ├── evaluator.py          # Strict rubric evaluator with schema validation
│   ├── feedback.py           # Actionable feedback builder and diff calculator
│   ├── memory.py             # Persistent memory manager (SQLite + JSON)
│   ├── orchestrator.py       # Workflow orchestrator (autonomous loop, retries, decisions)
│   ├── logger.py             # Rich terminal logging and report presentation
│   ├── output.py             # Output artifact manager (reports, rejection logs, final lesson)
│   └── main.py               # CLI entry point
├── prompts/
│   ├── generation_prompt.md  # System prompt for initial lesson generation
│   ├── evaluation_prompt.md  # Strict evaluation rubric prompt
│   └── regeneration_prompt.md# Targeted revision prompt with failed checkpoints feedback
├── data/
│   ├── references.md         # Authoritative ground truth for RAG concepts
│   ├── memory.json           # Persistent store for failure patterns and insights
│   └── history.db            # SQLite database for persistent run and version history
├── outputs/
│   ├── .gitkeep              # Run reports and rejection audit logs stored here
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared test fixtures and temporary isolated environments
│   ├── test_rubric.py        # Rubric structure and programmatic checks
│   ├── test_evaluator.py     # Schema validation and error handling (Tests F & G)
│   ├── test_orchestrator.py  # First attempt approval and regeneration (Tests A & B)
│   ├── test_memory.py        # Persistent memory survival across restarts (Test E)
│   ├── test_retry_limit.py   # Retry ceiling and REJECTED termination (Test C)
│   └── test_approval_rules.py# Hard pass/fail gate; no false approvals (Test D)
├── docs/
│   ├── architecture.md       # Pipeline architecture and component design
│   ├── design_decisions.md   # Rationale, rubric design, and honest limitations
│   ├── final_lesson.md       # Official approved lesson generated from live run
│   └── video_demo_script.md  # 15-20 min face-visible walkthrough script
├── .env.example              # Example environment configuration
├── .gitignore                # Protects secrets, databases, and temporary build files
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Production dependencies
└── README.md                 # Complete project documentation
```

---

## 5. Prerequisites & Environment Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.13.12 on Windows)
- pip package manager

### Installation
Clone or navigate to the workspace directory:
```bash
cd "c:\Users\asus1\OneDrive\Desktop\Self_Evaluating_Lesson Generator"
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Environment Configuration (Optional)
To run with a live model API (such as OpenAI GPT-4o-mini):
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and insert your API key:
   ```ini
   OPENAI_API_KEY=sk-...
   MODEL_NAME=gpt-4o-mini
   ```
*(Note: If no API key is set, the system automatically uses its high-fidelity deterministic engine, ensuring full offline functionality).*

---

## 6. How to Run the Application

### 1. Standard End-to-End Execution
Run the autonomous pipeline on the default topic (`Introduction to RAG (Retrieval-Augmented Generation)`):
```bash
python app/main.py
```

### 2. Custom Topic
```bash
python app/main.py --topic "Introduction to Large Language Models"
```

### 3. Demonstrate Error Catching and Autonomous Retry
Inject a deliberate factual error (e.g., claiming RAG retrains model weights at query time) to see the evaluator catch it, reject Version 1, compile feedback, and regenerate Version 2:
```bash
python app/main.py --demo-error fact_error
```

### 4. Inspect Historical Runs
View all runs stored in the persistent SQLite database:
```bash
python app/main.py --list-runs
```

### 5. Inspect a Specific Run
```bash
python app/main.py --inspect-run <RUN_ID>
```

### 6. Inspect Persistent Memory & Insights
View repeated failure patterns and learned insights stored in `data/memory.json`:
```bash
python app/main.py --inspect-memory
```

---

## 7. How to Run Automated Tests

The test suite validates all requirements (Tests A through G) using isolated fixtures:

```bash
python -m pytest -v
```

### Test Suite Mapping:
- **Test A (`tests/test_orchestrator.py`):** Successful first attempt (`APPROVED`, 0 retries).
- **Test B (`tests/test_orchestrator.py`):** Successful regeneration (fails V1, passes V2 -> `APPROVED`).
- **Test C (`tests/test_retry_limit.py`):** Repeated failure exhausts max retries -> `REJECTED`.
- **Test D (`tests/test_approval_rules.py`):** No false approval when 1 checkpoint fails out of 12.
- **Test E (`tests/test_memory.py`):** Persistent memory survives application restart.
- **Test F (`tests/test_evaluator.py`):** Controlled factual error caught and rejected by evaluator.
- **Test G (`tests/test_evaluator.py`):** Malformed/incomplete evaluator JSON rejected.

---

## 8. Outputs and Inspection

When a pipeline executes, all artifacts are saved to `outputs/`:
- **JSON Run Report (`outputs/run_<RUN_ID>_report.json`):** Full trajectory containing all versions, prompts, checkpoint results, and diff summaries.
- **Audit Log (`outputs/run_<RUN_ID>_rejection_log.md`):** Detailed audit trail of failed attempts, evaluator reasons, and revision diffs.
- **Official Final Lesson (`docs/final_lesson.md`):** When approved, the final passing lesson is written directly to `docs/final_lesson.md` with complete YAML metadata headers.

---

## 9. Limitations and Trade-offs

1. **LLM Evaluator Nuance:** While structured output and temperature=0 minimize hallucinations in the evaluator, LLM-as-a-judge is not a formal mathematical theorem prover. Cross-validation against ground truth (`data/references.md`) is necessary for strict guarantees.
2. **Deterministic Ceiling:** Retries are strictly capped at 2 attempts (3 versions max) to prevent infinite loops and runaway API token costs.
3. **Controlled Self-Evolution:** The system stores failure patterns and guidance in `memory.json`, but the evaluation rubric remains immutable unless altered by human engineers, preventing the system from lowering its own standards.
